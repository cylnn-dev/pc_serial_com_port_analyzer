import sys

from PyQt6.QtWidgets import QPushButton, QSizePolicy, QDialog, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setGeometry(200, 200, 160, 160)  # useless?

        # uart settings
        self.com_port_label = QLabel('COM Port:\t')
        self.com_port_input = QLineEdit(self)

        self.baud_rate_label = QLabel('Baud Rate:\t')
        self.baud_rate_input = QLineEdit(self)

        self.chunk_label = QLabel('Chunk:\t\t')
        self.chunk_input = QLineEdit(self)

        self.timeout_label = QLabel('Timeout:\t\t')
        self.timeout_input = QLineEdit(self)

        self.record_label = QLabel('Record n_sample:\t')
        self.record_input = QLineEdit(self)

        # general settings
        self.sample_rate_label = QLabel('Sample Rate:\t')
        self.sample_rate_input = QLineEdit(self)

        self.in_device_label = QLabel('input device\t')
        self.in_device_input = QLineEdit(self)

        self.out_device_label = QLabel('output device\t')
        self.out_device_input = QLineEdit(self)

        # usb settings
        self.n_channels_label = QLabel('channels\t\t')
        self.n_channels_input = QLineEdit(self)

        self.block_size_label = QLabel('block size\t')
        self.block_size_input = QLineEdit(self)

        self.latency_label = QLabel('latency\t\t')
        self.latency_input = QLineEdit(self)

        # default values
        self.set_default_values()

        self.save_button = QPushButton('Save', self)
        self.save_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.save_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(QLabel('\t\t--- general settings ---'))

        sample_layout = QHBoxLayout()
        sample_layout.addStretch()
        sample_layout.addWidget(self.sample_rate_label)
        sample_layout.addWidget(self.sample_rate_input)
        sample_layout.addStretch()
        layout.addLayout(sample_layout)

        in_device_layout = QHBoxLayout()
        in_device_layout.addStretch()
        in_device_layout.addWidget(self.in_device_label)
        in_device_layout.addWidget(self.in_device_input)
        in_device_layout.addStretch()
        layout.addLayout(in_device_layout)

        out_device_layout = QHBoxLayout()
        out_device_layout.addStretch()
        out_device_layout.addWidget(self.out_device_label)
        out_device_layout.addWidget(self.out_device_input)
        out_device_layout.addStretch()
        layout.addLayout(out_device_layout)

        layout.addWidget(QLabel('\t\t--- USB settings ---'))
        n_channels_layout = QHBoxLayout()
        n_channels_layout.addStretch()
        n_channels_layout.addWidget(self.n_channels_label)
        n_channels_layout.addWidget(self.n_channels_input)
        n_channels_layout.addStretch()
        layout.addLayout(n_channels_layout)

        blocksize_layout = QHBoxLayout()
        blocksize_layout.addStretch()
        blocksize_layout.addWidget(self.block_size_label)
        blocksize_layout.addWidget(self.block_size_input)
        blocksize_layout.addStretch()
        layout.addLayout(blocksize_layout)

        latency_layout = QHBoxLayout()
        latency_layout.addStretch()
        latency_layout.addWidget(self.latency_label)
        latency_layout.addWidget(self.latency_input)
        latency_layout.addStretch()
        layout.addLayout(latency_layout)

        layout.addWidget(QLabel('\t\t--- UART settings ---'))
        com_layout = QHBoxLayout()
        com_layout.addStretch()
        com_layout.addWidget(self.com_port_label)
        com_layout.addWidget(self.com_port_input)
        com_layout.addStretch()
        layout.addLayout(com_layout)

        baud_layout = QHBoxLayout()
        baud_layout.addStretch()
        baud_layout.addWidget(self.baud_rate_label)
        baud_layout.addWidget(self.baud_rate_input)
        baud_layout.addStretch()
        layout.addLayout(baud_layout)

        chunk_layout = QHBoxLayout()
        chunk_layout.addStretch()
        chunk_layout.addWidget(self.chunk_label)
        chunk_layout.addWidget(self.chunk_input)
        chunk_layout.addStretch()
        layout.addLayout(chunk_layout)

        timeout_layout = QHBoxLayout()
        timeout_layout.addStretch()
        timeout_layout.addWidget(self.timeout_label)
        timeout_layout.addWidget(self.timeout_input)
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)

        record_layout = QHBoxLayout()
        record_layout.addStretch()
        record_layout.addWidget(self.record_label)
        record_layout.addWidget(self.record_input)
        record_layout.addStretch()
        layout.addLayout(record_layout)

        layout.addWidget(self.save_button)
        layout.addStretch()
        self.setLayout(layout)

        self.param_names = ['sample_rate', 'input_device', 'output_device', 'channels', 'block_size', 'latency',
                            'com_port', 'baud_rate', 'chunk', 'timeout', 'record_n_samples']
        self.param_dict = {}

    def set_default_values(self):
        self.sample_rate_input.setText('48_000')
        self.in_device_input.setText('-1')
        self.out_device_input.setText('35')
        self.latency_input.setText('high')
        self.n_channels_input.setText('1')
        self.block_size_input.setText('0')
        self.com_port_input.setText('COM8')
        self.baud_rate_input.setText('12_000_000')
        self.chunk_input.setText('256')
        self.timeout_input.setText('400')
        self.record_input.setText('50_000')

    def get_settings(self):
        try:
            param_values = [
                int(self.sample_rate_input.text()),
                int(self.in_device_input.text()),
                int(self.out_device_input.text()),
                int(self.n_channels_input.text()),
                int(self.block_size_input.text()),
                str(self.latency_input.text().strip().lower()),
                str(self.com_port_input.text()).strip().upper(),
                int(self.baud_rate_input.text()),
                int(self.chunk_input.text()),
                int(self.timeout_input.text()),
                int(self.record_input.text())
            ]

        except ValueError as e:
            print(f"Invalid input(s): {e}", file=sys.stderr)
            return {}

        self.param_dict = {param_name: param_value for (param_name, param_value) in zip(self.param_names, param_values)}

        return self.param_dict if self.param_dict else {}

