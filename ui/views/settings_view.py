from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget
)

from ui.theme import TEXT_MAIN


class SettingsView(QWidget):
    def __init__(self, audio_manager, config, on_save, on_bind_panic, parent=None):
        super().__init__(parent)
        self.audio_manager = audio_manager
        self.config = config
        self.on_save = on_save
        self.on_bind_panic = on_bind_panic
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        title = QLabel("Réglages Audio")
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_MAIN};")
        layout.addWidget(title)

        form = QFrame()
        form.setObjectName("SoundCard")
        form_layout = QGridLayout(form)
        form_layout.setSpacing(20)

        devices = self.audio_manager.get_output_devices()
        dev_list = [d["name"] for d in devices]

        self.cb_main_device = QComboBox()
        self.cb_main_device.addItems(dev_list)
        if self.config.get("primary_output") in dev_list:
            self.cb_main_device.setCurrentText(self.config["primary_output"])

        self.chk_dual = QCheckBox("Activer la double sortie")
        self.chk_dual.setChecked(self.config.get("dual_output_enabled", False))
        self.chk_dual.toggled.connect(self._on_dual_toggled)

        self.cb_second_device = QComboBox()
        self.cb_second_device.addItems(dev_list)
        if self.config.get("secondary_output") in dev_list:
            self.cb_second_device.setCurrentText(self.config["secondary_output"])
        self.cb_second_device.setEnabled(self.chk_dual.isChecked())

        row = 0
        form_layout.addWidget(QLabel("Périphérique Principal :"), row, 0)
        form_layout.addWidget(self.cb_main_device, row, 1)
        row += 1
        form_layout.addWidget(self.chk_dual, row, 0)
        row += 1
        form_layout.addWidget(QLabel("Périphérique Secondaire (Câble Virtuel) :"), row, 0)
        form_layout.addWidget(self.cb_second_device, row, 1)
        row += 1

        self.sl_secondary_volume = QSlider(Qt.Horizontal)
        self.sl_secondary_volume.setRange(0, 100)
        self.sl_secondary_volume.setValue(self.config.get("global_secondary_volume", 100))
        self.sl_secondary_volume.setEnabled(self.chk_dual.isChecked())
        self.lbl_secondary_volume = QLabel(f"{self.sl_secondary_volume.value()}%")
        self.lbl_secondary_volume.setFixedWidth(45)
        self.sl_secondary_volume.valueChanged.connect(
            lambda v: self.lbl_secondary_volume.setText(f"{v}%")
        )
        vol_row = QWidget()
        vol_layout = QHBoxLayout(vol_row)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        vol_layout.addWidget(self.sl_secondary_volume)
        vol_layout.addWidget(self.lbl_secondary_volume)
        form_layout.addWidget(QLabel("Volume envoyé sur le câble virtuel :"), row, 0)
        form_layout.addWidget(vol_row, row, 1)
        row += 1

        self.chk_solo = QCheckBox("Mode solo — un seul son à la fois")
        self.chk_solo.setChecked(self.config.get("mode_solo", False))
        form_layout.addWidget(self.chk_solo, row, 0)
        row += 1

        self.spin_fade_in = QSpinBox()
        self.spin_fade_in.setRange(0, 5000)
        self.spin_fade_in.setSingleStep(50)
        self.spin_fade_in.setValue(self.config.get("fade_in_ms", 150))
        form_layout.addWidget(QLabel("Fondu d'entrée (ms) :"), row, 0)
        form_layout.addWidget(self.spin_fade_in, row, 1)
        row += 1

        self.spin_fade_out = QSpinBox()
        self.spin_fade_out.setRange(0, 5000)
        self.spin_fade_out.setSingleStep(50)
        self.spin_fade_out.setValue(self.config.get("fade_out_ms", 150))
        form_layout.addWidget(QLabel("Fondu de sortie (ms) :"), row, 0)
        form_layout.addWidget(self.spin_fade_out, row, 1)
        row += 1

        self.btn_panic = QPushButton(f"Touche Arrêt: {self.config.get('panic_hotkey', 'None')}")
        self.btn_panic.clicked.connect(self.on_bind_panic)
        form_layout.addWidget(QLabel("Arrêt d'urgence global :"), row, 0)
        form_layout.addWidget(self.btn_panic, row, 1)
        row += 1

        self.btn_save = QPushButton("SAUVEGARDER")
        self.btn_save.setProperty("class", "accent")
        self.btn_save.clicked.connect(self._save)
        form_layout.addWidget(self.btn_save, row, 1)

        layout.addWidget(form)
        layout.addStretch()

    def _on_dual_toggled(self, checked):
        self.cb_second_device.setEnabled(checked)
        self.sl_secondary_volume.setEnabled(checked)

    def set_panic_label(self, hotkey_text):
        self.btn_panic.setText(f"Touche Arrêt: {hotkey_text}")

    def _save(self):
        self.config["primary_output"] = self.cb_main_device.currentText()
        self.config["dual_output_enabled"] = self.chk_dual.isChecked()
        self.config["secondary_output"] = self.cb_second_device.currentText()
        self.config["global_secondary_volume"] = self.sl_secondary_volume.value()
        self.config["mode_solo"] = self.chk_solo.isChecked()
        self.config["fade_in_ms"] = self.spin_fade_in.value()
        self.config["fade_out_ms"] = self.spin_fade_out.value()
        self.on_save(self.config)
        # Inline confirmation rather than a modal to dismiss: saving settings
        # is not an event worth interrupting the user for.
        self.btn_save.setText("ENREGISTRÉ ✓")
        QTimer.singleShot(1600, lambda: self.btn_save.setText("SAUVEGARDER"))
