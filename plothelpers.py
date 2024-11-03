"""
plothelpers.py
=====
helper functions for plot formatting
"""
import numpy as np
from numpy.typing import ArrayLike


def value_to_db(value, v0=1.0):
    """
    Convert given value to dB, with 0dB being v0.
    :param value: value to convert
    :param v0: base value for 0db
    """
    ratio = value / v0
    if ratio <= 0:
        return -np.inf
    return 10 * np.log10(ratio)


def db_to_value(db, v0=1.0):
    """
    Convert dB to float value.
    :param db: value to convert
    :param v0: base value for 0db
    :return:
    """
    return 10 ** (db / 10) * v0


def decibel_formatter(v0=1.0, unit='dB'):
    """
    create formatter for display axis values as decibels
    :param v0: base value for 0db
    :param unit: unit display string
    :return: function
    """
    def format_value(value, pos=None):
        db = value_to_db(value, v0=v0)
        return f'{db:.0f} {unit}'
    return format_value


def samples_time_conversion(samplerate=44100, timebase="ms"):
    """
    create conversion functions between number of samples and time in milliseconds
    :param timebase: unit for time display, either "ms" or "s"
    :param samplerate: sample rate for converion
    :return: tuple of functions
    """
    if timebase == "ms":
        factor = 1000
    elif timebase == "s":
        factor = 1
    else:
        raise ValueError("timebase must be either 'ms' or 's'")

    def _sample2ms(samples: ArrayLike):
        return (samples * factor) / samplerate

    def _ms2samples(times: ArrayLike):
        return times * samplerate / factor
    return _sample2ms, _ms2samples
