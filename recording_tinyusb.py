import scipy
import sounddevice
import sounddevice as sd
import matplotlib.pyplot as plt
import numpy as np
import platform
import csv

if __name__ == '__main__':

    # If you got "ValueError: No input device matching", that is because your PC name example device
    # differently from tested list below. Uncomment the next line to see full list and try to pick correct one
    print(sd.query_devices())

    samplerate = 48000  # Sample rate
    duration = 10e-3  # Duration of recording

    if platform.system() == 'Windows':
        # MME is needed since there are more than one MicNode device APIs (at least in Windows)
        device = ' Microphone (MicNode), Windows WDM-KS'
    elif platform.system() == 'Darwin':
        device = 'MicNode'
    else:
        device = 'default'

    myrecording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16', device=device)
    print('Recording...')
    sd.wait()  # Wait until recording is finished
    print('Done!')

    time = np.arange(0, duration, 1 / samplerate)  # time vector
    plt.plot(time, myrecording)
    plt.grid(True)
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')
    plt.title('Recorded Data')
    plt.show()

    sd.play(myrecording, samplerate=samplerate)
    scipy.io.wavfile.write("recorded_signal.wav", samplerate, myrecording)

    #
    # samples = np.array(myrecording)
    # np.savetxt('Output.csv', samples, delimiter=",", fmt='%s')
