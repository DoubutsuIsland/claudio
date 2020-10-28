from typing import Callable

import numpy as np


def make_pure_tone(amp: float, freq: int, samplerate: int,
                   t: float) -> np.ndarray:
    return amp * np.sin(
        2.0 * np.pi * freq * np.arange(samplerate * t) / samplerate)


def set_speaker(speaker, tone: np.ndarray, rate=int) -> Callable:
    def sound():
        speaker.play(tone, samplerate=rate)
        return None

    return sound


if __name__ == '__main__':
    import soundcard as sc
    from pino.config import Config

    config = Config("./config/sound_check.yml")
    expvars = config.get_experimental()
    SAMPLERATE = expvars.get("samplerate", 48000)
    SPEAKER_1 = expvars.get("speaker-1", 0)
    SPEAKER_2 = expvars.get("speaker-2", 1)
    HZ_1 = expvars.get("Hz-1", 440)
    HZ_2 = expvars.get("Hz-2", 880)
    SOUND_DUARION = 1  # sec
    speakers = list(filter(lambda d: "USB" in str(d), sc.all_speakers()))
    sound_1 = set_speaker(
        speakers[SPEAKER_1],
        make_pure_tone(20.0, HZ_1, SAMPLERATE, SOUND_DUARION), SAMPLERATE)
    sound_2 = set_speaker(
        speakers[SPEAKER_2],
        make_pure_tone(20.0, HZ_2, SAMPLERATE, SOUND_DUARION), SAMPLERATE)

    for _ in range(5):
        sound_1()
        sound_2()
