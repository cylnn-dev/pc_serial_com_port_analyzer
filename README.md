# Serial COM Port Analyzer

I highly recommend using a cost-effective logic analyzer instead of creating your desktop application. However, during my digital signal processing project, I developed a small application capable of receiving data packets from both UART and USB, equipped with various settings. This project is based on multithreaded PyQt6

In short, the app consists of:

- GUI thread controls button actions and updates plots and opening/closing communication protocols.
- SerialDataFetcher thread, that is catching and processing UART packages
- MicRecorder thread, dedicated to receiving USB packets (the development board was connected as a MIC to Windows, hence the name).
- AudioPlayer thread, continuously streaming the fetched packages directly to the speaker or the designated Virtual Cable.

WIP, detailed explanation on: https://cylnn-dev.github.io
