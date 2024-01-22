import numpy as np
from PyQt6.QtCore import pyqtSignal, QObject


class FetcherSignals(QObject):
    """
    These signals are used with threads of this program to communicate through the lifecycle
    contains 'result' and 'finish' signals of the DataFetcher
    result_signal: send data to matplotlib to plot the data
    finish_signal: pause or terminate the thread
    """
    result_signal = pyqtSignal(object)
    finish_signal = pyqtSignal()

    def __init__(self):
        super().__init__()


class EmptyError(Exception):
    pass


def decode_bytes(byte_packet):
    """
    UART byte decoder for 32-bit float values

    these monstrously written lines finds headers we defined as 4 0xFF and converts to float.
    Packages contains 4 bytes = 32 bits.
    """
    # extract float's by looking for headers and then flatten
    packets = byte_packet.split(b'\xff\xff\xff\xff')
    # trim the first and the last packages
    packets[0] = packets[0][len(packets[0]) % 4:]
    packets[-1] = packets[-1][:-len(packets[-1]) % 4] if len(packets[-1]) % 4 else packets[-1]
    packets = [packet[:-len(packet) % 4] if (len(packet) % 4) else packet for packet in packets]
    packets = [packet for packet in packets if len(packet) > 3]
    print([len(packet) for packet in packets])
    float_packets = [np.frombuffer(packet, dtype=np.float32) for packet in packets]
    float_packet = [item for sublist in float_packets for item in sublist]
    return float_packet
