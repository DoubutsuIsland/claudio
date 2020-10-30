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


#def init_trials(var: dict) -> List[float]:
#    mean = var.get("mean-iti")
#    _range = var.get("range-iti")
#    trial = var.get("trial", 0)
#    if mean < _range or trial < 1:
#        raise ValueError
#    d = 2 * _range
#    e = _range / trial
#    _min = mean - _range
#    itis = [(_min + (step * d / trial)) + e for step in range(trial)]
#    shuffle(itis)
#    return itis

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
                #agent.send_to(RECORDER, packing(cs))
                #beep()
                #await agent.sleep(cs_duration)
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


#def set_yml_widow(yaml_path: str):
#    global x, y
#    ymlPath = glob.glob(yaml_path)
#    ymlFile = [os.path.basename(i) for i in ymlPath]
#
#    BtoP = Config("./config/gui/box2port.yml")
#    BPKey = [key for key in BtoP.get_metadata().keys()]
#    radioButton = []
#    for i in range(0, len(BPKey)):
#        radioButton.append(sg.Radio(f'{BPKey[i]}', 'Radio1', key = f'{BPKey[i]}'))
#
#    sg.SetOptions(text_justification='left', font = ('Hack', 13))
#    layout =[[sg.Text('Set Your Experiment', justification = 'center', font = ('Hack', 15), size = (50,1))],
#            [sg.Text('config file: ', size = (13, 1)), sg.Combo(values = ymlFile, readonly = True, auto_size_text = True, key = 'path')],
#            [sg.Text('chamber: ', size = (13,1)), sg.Frame(layout = [radioButton],
#                  title='',title_color='black', element_justification = 'center', border_width = 5)],
#            [sg.Text('')],
#            [sg.Cancel(), sg.Button('Submit', pad = (20,(5,0)))]]
#
#    win_set_yml = sg.Window('set yaml file', layout)
#
#    while True:
#        event, values = win_set_yml.read()
#        x, y = win_set_yml.CurrentLocation()
#        if event in (None, 'Cancel'):
#            sys.exit()
#            break
#        if event == 'Submit':
#            if values['path'] != "":
#                config = Config("./config/gui/" + f'{values["path"]}')
#                for i in range(0, len(BPKey)):
#                    if values[f'{BPKey[i]}'] == True:
#                        chamber = BPKey[i]
#                        port = BtoP.get_metadata()[f'{BPKey[i]}']
#                        config['Comport']['port'] = port
#                        config['chamber'] = chamber
#                try:
#                    port
#                    break
#                except NameError:
#                    sg.popup('No Chamber selected!', location = (x, y))
#            else:
#                sg.popup('No File selected!', location = (x, y))
#
#    win_set_yml.close()
#    return config
#
#
#def set_filename_window():
#    global x, y
#    cols = []
#    chamber = config['chamber']
#    for els in list(config['Experimental'].items()):
#        cols.append([sg.Text(f'{els[0]}:', justification = 'right', size = (15,1)),
#            sg.Text(f'{els[1]}', size =(20,1), background_color = 'blue')])
#
#    layout = [[sg.Text('Experimental Parameters', font = ('Hack', 15))],
#            [sg.Frame('parameters', [[sg.Column(cols, background_color = 'white')],[sg.Text('', size = (30,1)), sg.Button('revise')]])],
#            [sg.Text('')],
#            [sg.Text("Experimenter: "), sg.Input('', size = (30, 1), key = 'experimenter')],
#            [sg.Text("data file: "), sg.Input('', size = (25, 1), key = 'dataFile'), sg.Text('.csv', justification = 'left')],
#            [sg.Cancel(), sg.Button('submit')]]
#
#    window = sg.Window(f'{chamber}', layout, location = (x, y))
#    window2_active = False
#
#    while True:                  # the event loop
#        event, values = window.read()
#        x, y = window.CurrentLocation()
#        if event in (None, 'Cancel'):
#            sys.exit()
#            break
#        if event == "submit":
#            if values['dataFile'] != "" and values['experimenter'] != "":
#                break
#            else:
#                sg.popup('Specify Experimenter and FileName!', location = (x, y))
#                event, values = window.read()
#        if event == 'revise' and not window2_active:
#            window2_active = True
#            layout2 = []
#            for els in list(config['Experimental'].items()):
#                layout2.append([sg.Text(f'{els[0]} :', justification = 'right', size = (15,1)),
#                    sg.Input(f'{els[1]}', key = f'{els[0]}')])
#
#            layout2.append([sg.Cancel(), sg.Button('save')])
#            window2 = sg.Window('settings', layout2)
#            while True:
#                ev2, val2 = window2.read()
#                if ev2 in (None, 'Cancel'):
#                    window2.Close()
#                    window2_active = False
#                    break
#                if ev2 == 'save':
#                    sg.popup('Not implemented! :)')
#
#    filename = values["dataFile"] + "_" + \
#            config['Experimental']['schedule'] + "_" + \
#            f"{chamber}" + "_" + \
#            values["experimenter"] + "_" + \
#            datetime.now().strftime("%m-%d-%H-%M") + ".csv"
#    window.close()
#    return filename


if __name__ == '__main__':
    from pino.ino import Comport, OUTPUT, SSINPUT_PULLUP
    from pino.config import Config
    from pino.ui import clap
    from amas.env import Environment
    from amas.connection import Register
    from datetime import datetime
    from guifunc import wins
    #import PySimpleGUI as sg
    #import glob
    #import os

    config = wins.set_yml_widow('./config/gui/*.yml')

    #config = clap.PinoCli().get_config()
    #meta = config.get_metadata()

    #SAMPLERATE = expvars.get("samplerate")
    #cs_duration = expvars.get("cs-duration")
    #freq = expvars.get("Hz")
    #amp = expvars.get("amplifer", 10.0)
    #cs = make_pure_tone(amp, freq, SAMPLERATE, cs_duration)
    #sd.default.device = expvars.get("speaker")
    #sound = set_speaker(cs, samplerate=SAMPLERATE)

    #sub = meta.get("subject")
    #cond = meta.get("condition")

    filename = wins.set_filename_window(config)

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
    stimulator.assign_task(stimulate, ino=ino, beep=sound, var=expvars) \
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
