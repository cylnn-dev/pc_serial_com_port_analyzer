import sys

import numpy as np
import qdarktheme
import serial
import sounddevice as sd
from PyQt6.QtCore import QSize, QThreadPool, QProcess
from PyQt6.QtWidgets import QPushButton, QSizePolicy, QStatusBar, QStyleFactory, QFileDialog, QApplication
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
from numpy.fft import fftfreq, fft
from serial import SerialException

from settings_window import SettingsWindow
from threaded_classes import SerialDataFetcher, MicRecorder
from utility import decode_bytes


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.mic_recorder_thread = None
        self.packet = None
        self.setWindowTitle('Serial COM Analyzer')
        # self.setStyleSheet("background-color: white;")
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)

        self.fetcher_thread = None
        self.handle = None
        self.time_indices = None
        # (self.com_port,
        #  self.baud_rate,
        #  self.sample_rate,
        #  self.chunk,
        #  self.timeout,
        #  self.sample_size,
        #  self.record_n_sample,
        #  self.float_packet,
        #  self.time_indices,
        #  self.freqs,
        #  self.mic_recorder_thread,
        #  ) = [None] * 11

        self.param_dict = {}

        self.record_file: str = ""
        self.record_mic_flag = False

        self._default_time_ax_lims = [(0, 0.6), (-12, 12)]
        self._default_freq_ax_lims = [(-500, 500), (0, 1400)]

        self.threadpool = QThreadPool()

        print(f'Multithreading with maximum {self.threadpool.maxThreadCount()} threads')

        main_layout = QtWidgets.QVBoxLayout(self._main)
        self.statusbar: QStatusBar = self.statusBar()
        self.statusbar.showMessage("Ready")

        plot_layouts = QtWidgets.QHBoxLayout()
        time_layout = QtWidgets.QVBoxLayout()
        freq_layout = QtWidgets.QVBoxLayout()

        time_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        # Ideally one would use self.addToolBar here, but it is slightly
        # incompatible between PyQt6 and other bindings, so we just add the
        # toolbar as a plain widget instead.
        time_layout.addWidget(time_canvas)
        time_layout.addWidget(NavigationToolbar(time_canvas, self))

        freq_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        freq_layout.addWidget(freq_canvas)
        freq_layout.addWidget(NavigationToolbar(freq_canvas, self))

        # define time and freq axes
        self._time_ax = time_canvas.figure.subplots()
        self._time_ax.set_xlim(self._default_time_ax_lims[0])
        self._time_ax.set_ylim(self._default_time_ax_lims[1])
        self._time_ax.grid(True)
        self._line_t, = self._time_ax.plot([], [], label='time domain')
        time_canvas.figure.tight_layout()

        self._freq_ax = freq_canvas.figure.subplots()
        self._freq_ax.set_xlim(self._default_freq_ax_lims[0])
        self._freq_ax.set_ylim(self._default_freq_ax_lims[1])
        self._freq_ax.grid(True)
        self._line_freq, = self._freq_ax.plot([], [], label='frequency domain')
        freq_canvas.figure.tight_layout()
        ############

        # apply dark theme compatible matplotlib styles
        time_canvas.figure.patch.set_facecolor('#202124')
        self._time_ax.set_facecolor('#202124')
        self._time_ax.tick_params(axis='both', colors='white')

        freq_canvas.figure.patch.set_facecolor('#202124')
        self._freq_ax.set_facecolor('#202124')
        self._freq_ax.tick_params(axis='both', colors='white')
        ############

        plot_layouts.addLayout(time_layout)
        plot_layouts.addLayout(freq_layout)
        main_layout.addLayout(plot_layouts)

        # button layouts
        read_record_layout = QtWidgets.QHBoxLayout()
        read_record_layout.addStretch()

        self.play_button = QPushButton("Play")
        self.play_button.setEnabled(False)
        self.play_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        read_record_layout.addWidget(self.play_button)

        self.record_button = QPushButton("Record")
        self.record_button.setEnabled(False)
        self.record_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        read_record_layout.addWidget(self.record_button)

        self.read_button = QPushButton("Read")
        self.read_button.setEnabled(False)
        self.read_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        read_record_layout.addWidget(self.read_button)

        self.choose_file_button = QPushButton("Choose File")
        self.choose_file_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        read_record_layout.addWidget(self.choose_file_button)
        read_record_layout.addStretch()

        main_layout.addLayout(read_record_layout)

        setting_connect_layout = QtWidgets.QHBoxLayout()
        setting_connect_layout.addStretch()

        self.connect_button = QPushButton("Connect")
        self.connect_button.setEnabled(False)
        self.connect_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        setting_connect_layout.addWidget(self.connect_button)

        self.record_mic_button = QPushButton("Record Mic")
        self.record_mic_button.setEnabled(True)
        self.record_mic_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        setting_connect_layout.addWidget(self.record_mic_button)

        self.port_setting_button = QPushButton("Port Settings")
        self.port_setting_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        setting_connect_layout.addWidget(self.port_setting_button)
        setting_connect_layout.addStretch()

        button_layout = QtWidgets.QVBoxLayout()
        button_layout.addLayout(read_record_layout)
        button_layout.addLayout(setting_connect_layout)

        main_layout.addLayout(button_layout)
        ###############

        self.connect_buttons()

    def connect_buttons(self):
        self.port_setting_button.clicked.connect(self.open_settings_window)
        self.connect_button.clicked.connect(self.open_serial_port)
        self.read_button.clicked.connect(self.start_read)
        self.record_button.clicked.connect(self.start_record)
        self.play_button.clicked.connect(self.start_play)
        self.choose_file_button.clicked.connect(self.open_file_dialog)
        self.record_mic_button.clicked.connect(self.record_mic)

    def record_mic(self):
        self.record_mic_flag = not self.record_mic_flag
        if self.record_mic_flag:
            if not self.mic_recorder_thread:
                self.mic_recorder_thread = MicRecorder(in_device=self.param_dict['input_device'],
                                                       out_device=self.param_dict['output_device'],
                                                       samplerate=self.param_dict['sample_rate'],
                                                       channels=self.param_dict['channels'],
                                                       latency=self.param_dict['latency'],
                                                       blocksize=self.param_dict['block_size'],
                                                       )
                self.mic_recorder_thread.signals.result_signal.connect(self._update_canvas)

            self.mic_recorder_thread.is_stopped = False
            if not self.mic_recorder_thread.enable:
                self.threadpool.start(self.mic_recorder_thread)
                self.mic_recorder_thread.enable = True

            self.mic_recorder_thread.stream.start()
        else:
            if self.mic_recorder_thread:
                self.mic_recorder_thread.stream.abort()

    def open_file_dialog(self):
        self.read_button.setEnabled(False)
        self.play_button.setEnabled(False)
        file_dialog = QFileDialog(self)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        files, _ = file_dialog.getOpenFileNames(self, "Open File", "", "All Files (*)")

        if len(files) > 1:
            self.statusbar.showMessage('Accepts only one file. Try Again')
            self.open_file_dialog()
        elif len(files) == 0:
            self.statusbar.showMessage('Nothing chosen')
            self.record_file = ""
        else:
            self.record_file = files[0]
            print('selected file:', self.record_file)
            self.statusbar.showMessage("Select the samplerate using Port Settings, note: all sounds plays at 48kHz in "
                                       "Windows")

    def start_read(self):
        if self.threadpool.activeThreadCount() > 0:
            self.statusbar.showMessage('Please close any active ports before continuing')
            return

        if self.handle is not None:
            self.start_fetcher()
            self.statusbar.showMessage('Reading')
            print('active thread:', self.threadpool.activeThreadCount())

        elif self.record_file:
            self.statusbar.showMessage('Reading record file')
            with open(self.record_file, 'rb') as file:
                byte_packet = file.read()

            print('record file:', byte_packet)
            self.packet = decode_bytes(byte_packet)
            self._update_canvas(self.packet)

            # # also enable play button after reading the record successfully
            # self.start_play()
            self.play_button.setEnabled(True)
        else:
            self.statusbar.showMessage('Connect before reading or choose a .bin file')

    def start_play(self):
        # audio_thread = AudioPlayer(self.sample_rate, len(self.float_packet), self.float_packet)
        # self.threadpool.start(audio_thread)

        sd.wait()
        audio = self.packet
        # audio /= np.max(np.abs(audio), axis=0) // todo_fixed: check if it is necessary to adjust values
        print("audio:", audio)
        self.statusbar.showMessage('Packet is playing now')
        sd.default.channels = 1
        # sd.default.dtype = np.float32
        sd.play(audio, samplerate=self._play_samplerate, blocking=True)

    def start_record(self):
        if self.threadpool.activeThreadCount() > 0:
            self.statusbar.showMessage('"Please close any active ports before continuing')
            return

        if self.param_dict['record_n_samples'] > 0:
            fetcher_thread_record = SerialDataFetcher(self.handle, self.param_dict['chunk'],
                                                      record_n_sample=self.param_dict['record_n_samples'])
            self.threadpool.start(fetcher_thread_record)
        else:
            self.statusbar.showMessage(f'choose an appropriate record sample size! Current: {self.record_n_sample}')

    def open_serial_port(self):
        if self.handle is not None:
            # close the handle and emit finish signal from the thread
            print('closing fired!')
            self.handle.close()
            self.handle = None
            self.close_thread()
            self.connect_button.setText("Connect")
            print('active thread:', self.threadpool.activeThreadCount())

        else:
            try:
                if self.handle is not None:
                    if self.handle.is_open:
                        self.handle.close()
                        self.handle.flushInput()
                        self.handle.flushOutput()
                        print('Previous port closed')

                self.handle = serial.Serial(port=self.param_dict['com_port'], baudrate=self.param_dict['baud_rate'],
                                            timeout=self.param_dict['timeout'], )
                print("handle opened!", self.handle)
                self.statusbar.showMessage(f"Listening {self.param_dict['com_port']}")
                self.connect_button.setText("Disconnect")
            except SerialException as e:
                self.statusbar.showMessage(f"Connection error on {self.param_dict['com_port']}! {e}")
                self.handle = None

    def start_fetcher(self):
        self.fetcher_thread = SerialDataFetcher(self.handle, self.param_dict['chunk'])
        self.fetcher_thread.signals.result_signal.connect(self._update_canvas)
        self.fetcher_thread.signals.finish_signal.connect(self.close_thread)
        self.threadpool.start(self.fetcher_thread)

    def close_thread(self):
        if self.fetcher_thread:
            self.fetcher_thread.is_stopped = True
        self.threadpool.clear()

    def close_and_restart(self):
        # Close the application
        QApplication.instance().quit()

        # Restart the application
        self.restart_app()

    @staticmethod
    def restart_app():
        program = sys.executable  # Get the Python interpreter path
        arguments = sys.argv  # Get the command line arguments

        # Start a new instance of the application
        QProcess.startDetached(program, arguments)

    def open_settings_window(self):
        settings_window = SettingsWindow(self)
        settings_window.setStyleSheet(qdarktheme.load_stylesheet())
        settings_window.setGeometry(self.geometry().right(), self.geometry().top(), 200, 100)
        settings_window.setFixedSize(QSize(320, 450))
        if settings_window.exec():
            try:
                self.param_dict = settings_window.get_settings()
                param_display = ", ".join(
                    f"{param_name}: {param_value}" for param_name, param_value in self.param_dict.items())

                self.statusbar.showMessage(param_display)
                self.buttons_enable(True)
            except ValueError as e:
                self.statusbar.showMessage(f"Values are not of the correct type\n Try again: \n{e}")
                self.buttons_enable(False)
                self.open_settings_window()

    def buttons_enable(self, enable):
        self.connect_button.setEnabled(enable)
        self.record_button.setEnabled(enable)
        self.read_button.setEnabled(enable)

    def _update_canvas(self, packet, freqs=None):
        # print("update canvas fired")
        packet_len = len(packet)
        if (self.time_indices is None) or len(self.time_indices) != packet_len:
            # print("generating indices")
            self.time_indices = np.linspace(0, 1 / self.param_dict['sample_rate'] * packet_len, packet_len)
            self.freqs = fftfreq(packet_len, 1 / self.param_dict['sample_rate'])
            # print('time_indices:', self.time_indices)
            # print('freqs:', self.freqs)
            # print('packet:', packet)

        self._line_t.set_data(self.time_indices, packet)
        self._line_t.figure.canvas.draw()

        fft_packet = fft(packet, axis=0)
        self._line_freq.set_data(self.freqs if freqs is None else freqs, np.abs(fft_packet))
        self._line_freq.figure.canvas.draw()


def apply_dark_theme():
    app.setStyle(QStyleFactory.create("Fusion"))
    qdarktheme.setup_theme(corner_shape='rounded')


if __name__ == "__main__":
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QtWidgets.QApplication.instance()

    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow()
    apply_dark_theme()
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec()
