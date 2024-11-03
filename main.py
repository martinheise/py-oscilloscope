import argparse
import sys

from oscilloscope import Oscilloscope
import sounddevice as sd


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


def read_args():
    """read command line arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-l', '--list-devices', action='store_true',
        help='show list of audio devices and exit')
    _args, remaining = parser.parse_known_args()
    if _args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser])
    parser.add_argument(
        '-c', '--channels', type=int, default=[1], nargs='*', metavar='CHANNEL',
        help='input channels to plot (default: the first)')
    parser.add_argument(
        '-d', '--device', type=int_or_str,
        help='input device (numeric ID or substring)')
    parser.add_argument(
        '-w', '--window', type=float, default=1024, metavar='DURATION',
        help='initial visible time slot (default: %(default)s samples)')
    parser.add_argument(
        '-i', '--interval', type=float, default=30,
        help='minimum time between plot updates (default: %(default)s ms)')
    parser.add_argument(
        '-b', '--blocksize', type=int, help='block size (in samples)', default=1000)
    parser.add_argument(
        '-r', '--samplerate', type=float, help='sampling rate of audio device')
    parser.add_argument(
        '-n', '--downsample', type=int, default=1, metavar='N',
        help='display only every Nth sample (default: %(default)s)')
    _args = parser.parse_args(remaining)
    if any(c < 1 for c in _args.channels):
        parser.error('argument CHANNEL: must be >= 1')
    return _args


def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    osc.put_data(indata)


if __name__ == "__main__":
    args = read_args()
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        args.samplerate = device_info['default_samplerate']
    stream = sd.InputStream(
        device=args.device, channels=max(args.channels),
        samplerate=args.samplerate, callback=audio_callback, blocksize=args.blocksize)
    osc = Oscilloscope(stream, channels=args.channels, window=args.window,
                       downsample=args.downsample, interval=args.interval)
    osc.show()
