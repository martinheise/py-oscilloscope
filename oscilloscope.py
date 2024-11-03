import queue
import time

import numpy as np
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import MaxNLocator, AutoMinorLocator

from plothelpers import decibel_formatter, samples_time_conversion


class Oscilloscope:
    """
    class Oscilloscope, handling display of realtime audio data in an animated plot
    """

    max_window = 65536
    min_window = 16
    max_yzoom = 8.0
    min_yzoom = 1.0

    def __init__(self, stream, window=1024, downsample=1, interval=1000, channels=(1,)):
        self.q = queue.Queue()
        self.stream = stream
        self.paused = False
        self.avg = 1
        self.downsample = downsample
        self.interval = interval
        self.channel_mapping = [c - 1 for c in channels]

        # prepare empty plotdata with max length
        self.plotdata = np.zeros((self.max_window, self.stream.channels))

        self.fig, self.lines, self.status_text, self.ax = self.setup_plot()
        self.window = window
        self.set_window()
        self.yzoom = 1.0
        self.set_yzoom()
        # we need blit=False (and animate=False on artists) to keep axis modifiable
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=self.interval, blit=False, save_count=10)

        self.cid_key = self.fig.canvas.mpl_connect('key_press_event', self.onkeypress)
        self.starttime = time.time()

    def set_window(self, window=None):
        """
        set time window to display
        :param window: time window in number of samples
        """
        if window is not None:
            self.window = max(min(window, self.max_window), self.min_window)
        self.ax.set_xlim([-self.window, 0])

    def set_yzoom(self, yzoom=None):
        """
        set vertical zoom factor
        :param yzoom: new zoom factor (float value)
        """
        if yzoom is not None:
            self.yzoom = max(min(yzoom, self.max_yzoom), self.min_yzoom)
        lim = 1 / self.yzoom
        self.ax.set_ylim([-lim, lim])

    def put_data(self, data):
        """put data into oscilloscope, as callback for sounddevice InputStream"""
        # modify data and create a copy:
        self.q.put(data[::self.downsample, self.channel_mapping])

    def setup_plot(self):
        """
        prepare plot, setup layout and axes
        """
        fig, ax = plt.subplots(figsize=(12, 6), facecolor=(0.9, 0.9, 0.9, 1))
        # layout="constrained" does not work with subplots_adjust
        fig.subplots_adjust(left=0.08, right=0.99, top=0.85, bottom=0.2)

        # ToDo: simplify lines for performance?
        # mpl.rcParams['path.simplify'] = True
        # mpl.rcParams['path.simplify_threshold'] = 1.0

        lines_cycler = (cycler(color=['blue', 'green']))
        ax.set_prop_cycle(lines_cycler)

        # using negative x values (most recent sample = 0)
        xvals = np.arange(-len(self.plotdata) + 1, 1, 1)
        # this is one Line2D per channel:
        lines = ax.plot(xvals, self.plotdata, picker=True, linewidth=1)
        if self.stream.channels > 1:
            ax.legend([f'channel {c}' for c in range(1, self.stream.channels)],
                      loc='lower left', ncol=self.stream.channels)

        # x-axis with secondary
        ax.xaxis.set_major_locator(MaxNLocator(nbins=10, steps=[1, 2, 5], min_n_ticks=4, integer=True))
        ax.xaxis.set_minor_locator(MaxNLocator(nbins=40, steps=[1, 2.5, 5], integer=True))
        ax.xaxis.grid(True)
        ax.xaxis.grid(True, which='minor', linestyle=':')
        ax.secondary_xaxis('top', functions=samples_time_conversion(self.stream.samplerate, 'ms'))
        ax.set_xlabel('samples')
        # add text as label does not seem to work:
        ax.text(0.5, 1.1, 'milliseconds', transform=ax.transAxes, ha='center')

        # y-axis
        ax.set_ylim([-1, 1])
        ax.yaxis.set_major_formatter(decibel_formatter())
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2.5, 5], min_n_ticks=5))
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.grid(True)
        ax.set_ylabel('amp')

        # texts
        fig.text(0.99, 0.05,
                 'p: pause – a: moving average – +/-: zoom ↔  – alt+/-: zoom ↕',
                 horizontalalignment="right")
        status_text = fig.text(0.08, 0.05, '(status)')

        return fig, lines, status_text, ax

    def update_plot(self, frame):
        """
        update plot with recent audio data, as callback for FuncAnimation
        """
        while True:
            try:
                data = self.q.get_nowait()
            except queue.Empty:
                break
            shift = len(data)  # shift = usually blocksize
            self.plotdata = np.roll(self.plotdata, -shift, axis=0)
            # error "could not broadcast input ..." if shift (= blocksize?) > plotdata
            self.plotdata[-shift:, :] = data

        if not self.paused:
            for channel, line in enumerate(self.lines):
                if self.avg > 1:
                    # moving average, np.roll to hide boundary effects
                    line.set_ydata(
                        np.roll(
                            np.convolve(self.plotdata[:, channel], np.ones(self.avg), "same") / self.avg,
                            self.avg
                        )
                    )
                else:
                    line.set_ydata(self.plotdata[:, channel])
            # ToDo: update status partly if paused
            self.status_text.set_text(f'frame %d, time %.3f, window %d, average %d' %
                                      (frame, (time.time() - self.starttime), self.window, self.avg))

        # return not necessary with blit=False, but let’s keep it
        return self.lines + [self.status_text] + [self.ax.xaxis]

    def show(self):
        """
        show animated oscilloscope for stream
        """
        self.starttime = time.time()
        with self.stream:
            plt.show()

    def onkeypress(self, event):
        """
        handle key events
        :param Event event:
        :return: void
        """
        print('%s key: x=%d, y=%d, xdata=%f, ydata=%f' % (
            event.key,
            event.x if event.x else 0,
            event.y if event.y else 0,
            event.xdata if event.xdata else 0,
            event.ydata if event.ydata else 0))
        if event.key == 'p':
            self.paused = not self.paused
        if event.key == 'alt+-':
            self.set_yzoom(self.yzoom / 2)
        if event.key == 'alt++':
            self.set_yzoom(self.yzoom * 2)
        if event.key == '-':
            self.set_window(self.window * 2)
        if event.key == '+':
            self.set_window(self.window / 2)
        if event.key == 'a':
            if self.avg == 1:
                self.avg = 3
            elif self.avg == 3:
                self.avg = 5
            else:
                self.avg = 1
