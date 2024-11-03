# py-oscilloscope

A small and simple tool to monitor audio signals in realtime, using matplotlib.

It is based on a an example for [python-sounddevice](https://github.com/spatialaudio/python-sounddevice/blob/0.4.7/examples/plot_input.py), enhancing the display and adding interactive modification of options.  


## Installing and running

Clone repository and install with pipenv:
```
pipenv sync
```

Or install necessary modules manually.

Run with:
```
pipenv run start <options>
```

or:
```
python main.py <options>
```

Run with option `-h` or `--help` to get an overview of all available options (all of them are optional)

### Options

- `-h`, `--help` show this help message and exit
- `-l`, `--list-devices` show list of audio devices and exit
- `-c [CHANNEL ...]`, `--channels [CHANNEL ...]` input channels to plot (default: the first)
- `-d DEVICE`, `--device DEVICE` input device (numeric ID or substring)
- `-w DURATION`, `--window DURATION` initial visible time slot (default: 1024 samples)
- `-i INTERVAL`, `--interval INTERVAL` minimum time between plot updates (default: 30 ms)
- `-b BLOCKSIZE`, `--blocksize BLOCKSIZE` block size (in samples)
- `-r SAMPLERATE`, `--samplerate SAMPLERATE` sampling rate of audio device
- `-n N`, `--downsample N`  display only every Nth sample (default: 1)


## Backend

The animated output needs an [interactive backend](https://matplotlib.org/stable/users/explain/figure/backends.html). I tested on macOS where the default `macosx` backend works fine out of the box, depending on your system environment you might need to configure something appropriate. 
