from random import shuffle
from time import perf_counter
from typing import Callable, List, Tuple

import numpy as np
import sounddevice as sd
from amas.agent import OBSERVER, Agent, NotWorkingError, Observer
from pino.ino import HIGH, LOW, Arduino
import random

STIMULATOR = "STIMULATOR"
READER = "READER"
RECORDER = "RECORDER"


def packing(event: int) -> Tuple[float, int]:
    return (perf_counter(), event)


def make_pure_tone(amp: float, freq: int, samplerate: int,
                   t: float) -> np.ndarray:
    return amp * np.sin(2.0 * np.pi * freq * np.arange(samplerate * t) /
                        samplerate).astype(np.float32)


def set_speaker(tone: np.ndarray, samplerate: int) -> Callable:
    def sound():
        sd.play(tone, samplerate=samplerate)
        return None

    return sound


def init_trials(var: dict) -> List[int]:
    schedule = var.get("schedule", "none")
    trial = var.get("trial", 0)
    if schedule == "PEAK":

        peakRatio = 0.15
        peakN = int(trial*peakRatio)
        freeN = trial - peakN * 3 + 2 - 5

        peaks = list()
        peaks.extend([0]*freeN)
        peaks.extend([1]*peakN)

        peaks.extend([0]*5)
        peaks.extend([1]*5)

        random.shuffle(peaks)

        trials = list([0, 0, 0])
        for i in range(len(peaks)):
            if peaks[i] == 1:
                trials.extend([1, 0, 0])
            else:
                trials.extend([0])

    elif schedule == "FT":
        trials = [0 for i in range(trial)]

    else:
        raise Exception(f"undefined schedule: {schedule}")

    return trials


async def stimulate(agent: Agent, ino: Arduino, beep: Callable,
                    var: dict) -> None:
    cs = 100
    us = var.get("us", 12)
    us_duration = var.get("us-duration")
    cs_duration = var.get("cs-duration")
    interval = var.get("interval", 10.)

    trials = init_trials(var)

    agent.send_to(RECORDER, (perf_counter(), 0))
    try:
        count = 0
        for trial in trials:
            count += 1

            if trial == 0:
                await agent.sleep(interval - us_duration)
            elif trial == 1:
                await agent.sleep(random.randint(
                        interval * 3, interval * 3 + 20 - us_duration
                    ))

            ino.digital_write(us, HIGH)
            await agent.sleep(us_duration)
            ino.digital_write(us, LOW)
            agent.send_to(RECORDER, packing(us))
            print(count)
        agent.send_to(RECORDER, packing(1))
    except NotWorkingError:
        agent.send_to(RECORDER, packing(-1))
    agent.send_to(OBSERVER, "done")
    return None


async def read(agent: Agent, ino: Arduino) -> None:
    try:
        while agent.working():
            v = await agent.call_async(ino.read_until_eol)
            if v is None:
                continue
            s = v.rstrip().decode("utf-8")
            agent.send_to(RECORDER, packing(s))
    except NotWorkingError:
        ino.cancel_read()
        pass
    return None


async def record(agent: Agent, filename: str) -> None:
    packs: List[Tuple[float, int]] = []
    try:
        while agent.working():
            _, mess = await agent.recv()
            print(mess)
            packs.append(mess)
    except NotWorkingError or KeyboardInterrupt:
        pass
    with open(filename, "w") as f:
        f.write("time, event\n")
        for pack in packs:
            t, e = pack
            f.write(f"{t}, {e}\n")
    return None


async def observe(agent: Observer) -> None:
    while agent.working():
        _, mess = await agent.recv(t=2.0)
        if mess == "done":
            agent.send_all(mess)
            agent.finish()
            break
    return None


async def watch(agent: Agent) -> None:
    while agent.working():
        _, mess = await agent.recv_from_observer()
        if mess == "done":
            agent.finish()
            break
    return None


if __name__ == '__main__':
    from pino.ino import Comport, OUTPUT, SSINPUT_PULLUP
    from pino.config import Config
    from pino.ui import clap
    from amas.env import Environment
    from amas.connection import Register
    from guifunc import wins

    config = wins.set_config('./config/gui/*.yml')
    filename = wins.set_filename(config)

    expvars = config.get_experimental()

    us = expvars.get("us")
    us_duration = expvars.get("us_duration")
    lick = expvars.get("lick")

    com = Comport() \
        .apply_settings(config.get_comport()) \
        .set_timeout(2.0) \
        .deploy() \
        .connect()

    ino = Arduino(com)
    ino.set_pinmode(us, OUTPUT)
    ino.set_pinmode(lick, SSINPUT_PULLUP)

    stimulator = Agent(STIMULATOR)
    stimulator.assign_task(stimulate, ino=ino, beep=None, var=expvars) \
        .assign_task(watch)

    reader = Agent(READER)
    reader.assign_task(read, ino=ino) \
        .assign_task(watch)

    recorder = Agent(RECORDER)
    recorder.assign_task(record, filename=filename) \
        .assign_task(watch)

    observer = Observer()
    observer.assign_task(observe)

    rgist = Register([stimulator, reader, recorder, observer])

    env = Environment([stimulator, reader, recorder, observer])
    env.run()
