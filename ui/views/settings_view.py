from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QLabel, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget
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

        self.cb_ducking = QComboBox()
        self.cb_ducking.addItems(["Aucun", "Léger (50%)", "Fort (80%)", "Total (100%)"])
        self.cb_ducking.setCurrentText(self.config.get("audio_ducking_level", "Léger (50%)"))
        form_layout.addWidget(QLabel("Atténuation (Ducking) :"), row, 0)
        form_layout.addWidget(self.cb_ducking, row, 1)
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

        btn_save = QPushButton("SAUVEGARDER")
        btn_save.setProperty("class", "accent")
        btn_save.clicked.connect(self._save)
        form_layout.addWidget(btn_save, row, 1)

        layout.addWidget(form)
        layout.addStretch()

    def _on_dual_toggled(self, checked):
        self.cb_second_device.setEnabled(checked)

    def set_panic_label(self, hotkey_text):
        self.btn_panic.setText(f"Touche Arrêt: {hotkey_text}")

    def _save(self):
        self.config["primary_output"] = self.cb_main_device.currentText()
        self.config["dual_output_enabled"] = self.chk_dual.isChecked()
        self.config["secondary_output"] = self.cb_second_device.currentText()
        self.config["audio_ducking_level"] = self.cb_ducking.currentText()
        self.config["fade_in_ms"] = self.spin_fade_in.value()
        self.config["fade_out_ms"] = self.spin_fade_out.value()
        self.on_save(self.config)
        QMessageBox.information(self, "Succès", "Réglages appliqués.")
