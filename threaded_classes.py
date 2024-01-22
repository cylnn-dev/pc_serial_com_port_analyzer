import platform
import time

import serial
import sounddevice as sd
from PyQt6.QtCore import pyqtSlot, QRunnable
from serial import PortNotOpenError

from utility import FetcherSignals, decode_bytes


class MicRecorder(QRunnable):
    """
    35 works for voiceaudio (out_device)
    """

    def __init__(self, in_device: str | int, out_device: str | int, samplerate: int, channels: int,
                 latency: str = 'high', blocksize: int = 0):

        super().__init__()

        if in_device == -1:
            if platform.system() == 'Windows':
                # MME is needed since there are more than one MicNode device APIs (at least in Windows)
                self.in_device = ' Microphone (MicNode), Windows WDM-KS'
            elif platform.system() == 'Darwin':
                self.in_device = 'MicNode'
            else:
                self.in_device = 'default'
        else:
            self.in_device = in_device

        self.out_device = out_device
        self.samplerate = samplerate
        self.channels = channels
        self.blocksize = blocksize
        self.dtype = 'int16'
        self.latency = latency
        self.signals = FetcherSignals()
        self.callback_status = sd.CallbackFlags()
        self.is_stopped = False
        self.enable = False
        self.stream = sd.Stream(device=(self.in_device, self.out_device),
                                samplerate=self.samplerate, blocksize=self.blocksize,
                                dtype=self.dtype, latency=self.latency,
                                channels=self.channels, callback=self.callback)

    def callback(self, indata, outdata, frames, time, status):
        self.callback_status |= status
        outdata[:] = indata
        self.signals.result_signal.emit(outdata)

        self.stream_status_check()

    def stream_status_check(self):
        if self.is_stopped:
            self.stream.stop()
        else:
            if not self.stream.active:
                self.stream.start()

            # try:
            #     if self.stream:
            #         self.stream.abort()
            # except Exception as e:
            #     print(f"Error while stopping/closing the stream: {e}")
            # finally:
            #     raise sd.CallbackAbort

    @pyqtSlot()
    def run(self) -> None:
        with self.stream:
            input()


class SerialDataFetcher(QRunnable):
    """
    data fetcher of UART protocol. It should only be used for serial communication with specific behaviour we described
    behavior: float packages of variable length with defined header structure: we use |0xff 0xff 0xff 0xff| for header
    and data is float (MSB) but packaged of 4 x 8 bits, because uart only support for 8-bit per element for sending
    and transmitting.

    todo: add parameter and variable descriptions
    """

    def __init__(self, handle: serial.Serial, chunk: int, record_n_sample: int = 0):
        super().__init__()
        self.handle: serial.Serial = handle
        if not self.handle.is_open:
            self.handle.open()

        self.chunk = chunk
        self.signals = FetcherSignals()
        self.record_n_sample: int = record_n_sample
        self.is_stopped = False

    @pyqtSlot()
    def run(self) -> None:
        if self.record_n_sample > 0:
            if self.handle is None:
                self.signals.finish_signal.emit()
                return

            print("recording started!")
            self.handle.timeout = 9e9

            tic = time.perf_counter()
            try:
                byte_packet = self.handle.read(self.record_n_sample)
            except PortNotOpenError():
                print("Connect to the port before recording!")
                self.signals.finish_signal.emit()
                return
            toc = time.perf_counter()

            elapsed_time = toc - tic  # in seconds
            print(f"elapsed_time: {elapsed_time:.2f} seconds")

            print("byte_packet:", byte_packet)

            with open('recorded_signal', 'wb') as f:
                f.write(byte_packet)

            self.handle.close()
            self.signals.finish_signal.emit()
        else:
            while not self.is_stopped:
                try:
                    tic = time.perf_counter()
                    byte_packet = self.handle.read(self.chunk)
                    toc = time.perf_counter()

                    float_packet = decode_bytes(byte_packet)
                    print(float_packet)

                    self.signals.result_signal.emit(float_packet)

                    # print(float_packet)
                    n_bytes = len(byte_packet)
                    elapsed_time = toc - tic  # in seconds
                    print(f'elapsed_time: {elapsed_time * 1000:.3f} ms, '
                          f'bits_per_second: {(n_bytes * 9 / elapsed_time):.3f} bps')

                except KeyboardInterrupt:
                    print('Com interrupted!')
                    self.handle.close()
                    self.signals.finish_signal.emit()
                    break

                except Exception as e:
                    print(f"An exception occured: {e}")
                    self.handle.close()
                    self.signals.finish_signal.emit()
                    break

            print('thread initiated stopping sequence')
            self.handle.close()
            self.signals.finish_signal.emit()


class AudioPlayer(QRunnable):
    """
    play recorded audio files,
    """

    def __init__(self, sample_rate, frames, packet):
        super().__init__()

        sd.default.samplerate = sample_rate
        sd.default.channels = 1
        self.frames = frames
        self.packet = packet

    @pyqtSlot()
    def run(self) -> None:
        # sd.OutputStream(device=sd.default.device[1], channels=1, callback=self.callback, samplerate=self.sample_rate)
        sd.wait()
        sd.play(self.packet)
