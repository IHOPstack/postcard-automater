from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, QCheckBox, QPushButton
from config import get_setting, update_setting

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.layout = QVBoxLayout(self)

        self.dpi_spinbox = self.create_spinbox("Default DPI:", "default_dpi", 72, 1200)
        self.persist_files_checkbox = self.create_checkbox("Persist files between app instances", "persist_files")

        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        self.layout.addLayout(buttons_layout)

    def create_spinbox(self, label, setting_key, min_value, max_value):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        spinbox = QSpinBox()
        spinbox.setRange(min_value, max_value)
        spinbox.setValue(get_setting(f"user_modifiable.{setting_key}"))
        layout.addWidget(spinbox)
        self.layout.addLayout(layout)
        return spinbox

    def create_combobox(self, label, setting_key, options):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        combobox = QComboBox()
        combobox.addItems(options)
        combobox.setCurrentText(get_setting(f"user_modifiable.{setting_key}"))
        layout.addWidget(combobox)
        self.layout.addLayout(layout)
        return combobox

    def create_checkbox(self, label, setting_key):
        checkbox = QCheckBox(label)
        checkbox.setChecked(get_setting(f"user_modifiable.{setting_key}"))
        self.layout.addWidget(checkbox)
        return checkbox

    def save_settings(self):
        update_setting("default_dpi", self.dpi_spinbox.value())
        update_setting("persist_files", self.persist_files_checkbox.isChecked())
        self.accept()
