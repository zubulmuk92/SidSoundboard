from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QInputDialog,
    QLabel, QMessageBox, QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget
)

import profiles

import i18n
from i18n import tr
from ui.theme import TEXT_MAIN, TEXT_MUTED


class SettingsView(QWidget):
    def __init__(self, audio_manager, config, on_save, on_bind_panic, parent=None,
                 on_scenes_changed=None):
        super().__init__(parent)
        self.audio_manager = audio_manager
        self.config = config
        self.on_save = on_save
        self.on_bind_panic = on_bind_panic
        # Scene edits are structural, so they apply at once rather than
        # waiting for Save like the audio settings do.
        self.on_scenes_changed = on_scenes_changed or (lambda: None)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        title = QLabel(tr("settings.title"))
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_MAIN};")
        layout.addWidget(title)

        form = QFrame()
        form.setObjectName("SoundCard")
        form_layout = QGridLayout(form)
        form_layout.setSpacing(20)

        self.cb_language = QComboBox()
        self._language_codes = list(i18n.LANGUAGES)
        self.cb_language.addItems([i18n.LANGUAGES[c] for c in self._language_codes])
        current = self.config.get("language", i18n.DEFAULT_LANGUAGE)
        if current in self._language_codes:
            self.cb_language.setCurrentIndex(self._language_codes.index(current))

        devices = self.audio_manager.get_output_devices()
        dev_list = [d["name"] for d in devices]

        self.cb_main_device = QComboBox()
        self.cb_main_device.addItems(dev_list)
        if self.config.get("primary_output") in dev_list:
            self.cb_main_device.setCurrentText(self.config["primary_output"])

        self.chk_dual = QCheckBox(tr("settings.dual_output"))
        self.chk_dual.setChecked(self.config.get("dual_output_enabled", False))
        self.chk_dual.toggled.connect(self._on_dual_toggled)

        self.cb_second_device = QComboBox()
        self.cb_second_device.addItems(dev_list)
        if self.config.get("secondary_output") in dev_list:
            self.cb_second_device.setCurrentText(self.config["secondary_output"])
        self.cb_second_device.setEnabled(self.chk_dual.isChecked())

        row = 0
        form_layout.addWidget(QLabel(tr("settings.language")), row, 0)
        form_layout.addWidget(self.cb_language, row, 1)
        row += 1
        form_layout.addWidget(QLabel(tr("settings.primary_device")), row, 0)
        form_layout.addWidget(self.cb_main_device, row, 1)
        row += 1
        form_layout.addWidget(self.chk_dual, row, 0)
        row += 1
        form_layout.addWidget(QLabel(tr("settings.secondary_device")), row, 0)
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
        form_layout.addWidget(QLabel(tr("settings.secondary_volume")), row, 0)
        form_layout.addWidget(vol_row, row, 1)
        row += 1

        self.sl_master_volume = QSlider(Qt.Horizontal)
        self.sl_master_volume.setRange(0, 200)
        self.sl_master_volume.setValue(self.config.get("master_volume", 100))
        self.lbl_master_volume = QLabel(f"{self.sl_master_volume.value()}%")
        self.lbl_master_volume.setFixedWidth(45)
        self.sl_master_volume.valueChanged.connect(
            lambda v: self.lbl_master_volume.setText(f"{v}%")
        )
        master_row = QWidget()
        master_layout = QHBoxLayout(master_row)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.addWidget(self.sl_master_volume)
        master_layout.addWidget(self.lbl_master_volume)
        form_layout.addWidget(QLabel(tr("settings.master_volume")), row, 0)
        form_layout.addWidget(master_row, row, 1)
        row += 1

        self.chk_solo = QCheckBox(tr("settings.solo"))
        self.chk_solo.setChecked(self.config.get("mode_solo", False))
        form_layout.addWidget(self.chk_solo, row, 0)
        row += 1

        self.spin_fade_in = QSpinBox()
        self.spin_fade_in.setRange(0, 5000)
        self.spin_fade_in.setSingleStep(50)
        self.spin_fade_in.setValue(self.config.get("fade_in_ms", 150))
        form_layout.addWidget(QLabel(tr("settings.fade_in")), row, 0)
        form_layout.addWidget(self.spin_fade_in, row, 1)
        row += 1

        self.spin_fade_out = QSpinBox()
        self.spin_fade_out.setRange(0, 5000)
        self.spin_fade_out.setSingleStep(50)
        self.spin_fade_out.setValue(self.config.get("fade_out_ms", 150))
        form_layout.addWidget(QLabel(tr("settings.fade_out")), row, 0)
        form_layout.addWidget(self.spin_fade_out, row, 1)
        row += 1

        self.btn_panic = QPushButton(tr("settings.panic_current", key=self.config.get("panic_hotkey", "None")))
        self.btn_panic.clicked.connect(self.on_bind_panic)
        form_layout.addWidget(QLabel(tr("settings.panic_key")), row, 0)
        form_layout.addWidget(self.btn_panic, row, 1)
        row += 1

        self.btn_save = QPushButton(tr("settings.save"))
        self.btn_save.setProperty("class", "accent")
        self.btn_save.clicked.connect(self._save)
        form_layout.addWidget(self.btn_save, row, 1)

        layout.addWidget(form)
        layout.addWidget(self._build_scene_section())
        layout.addStretch()

    def _build_scene_section(self):
        section = QFrame()
        section.setObjectName("SoundCard")
        layout = QVBoxLayout(section)
        layout.setSpacing(10)

        title = QLabel(tr("scene.section"))
        title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT_MAIN};")
        layout.addWidget(title)

        hint = QLabel(tr("scene.hint"))
        hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        row = QHBoxLayout()
        self.cb_scene = QComboBox()
        self.refresh_scenes()
        row.addWidget(self.cb_scene)

        btn_rename = QPushButton(tr("scene.rename"))
        btn_rename.clicked.connect(self._rename_scene)
        row.addWidget(btn_rename)

        btn_delete = QPushButton(tr("scene.delete"))
        btn_delete.setProperty("class", "danger")
        btn_delete.clicked.connect(self._delete_scene)
        row.addWidget(btn_delete)

        layout.addLayout(row)
        return section

    def refresh_scenes(self):
        """Re-reads the scene list. Scenes can be created from the sidebar
        while this screen is built but not visible, so it cannot rely on
        the list it saw at construction time."""
        selected = self.cb_scene.currentData()
        self.cb_scene.blockSignals(True)
        self.cb_scene.clear()
        for profile in self.config.get("profiles", []):
            self.cb_scene.addItem(profile["name"], profile["id"])
        index = self.cb_scene.findData(selected)
        if index >= 0:
            self.cb_scene.setCurrentIndex(index)
        self.cb_scene.blockSignals(False)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_scenes()

    def _selected_scene(self):
        scene_id = self.cb_scene.currentData()
        for profile in self.config.get("profiles", []):
            if profile["id"] == scene_id:
                return profile
        return None

    def _rename_scene(self):
        scene = self._selected_scene()
        if not scene:
            return
        name, ok = QInputDialog.getText(
            self, tr("scene.rename"), tr("scene.rename_prompt"), text=scene["name"]
        )
        if not ok or not name.strip():
            return
        profiles.rename_profile(self.config, scene["id"], name.strip())
        self.refresh_scenes()
        self.on_scenes_changed()

    def _delete_scene(self):
        scene = self._selected_scene()
        if not scene:
            return

        if len(self.config.get("profiles", [])) <= 1:
            QMessageBox.information(
                self, tr("scene.section"), tr("scene.cannot_delete_last")
            )
            return

        reply = QMessageBox.question(
            self, tr("scene.delete"),
            tr("scene.delete_confirm", name=scene["name"], count=len(scene.get("sounds", []))),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        profiles.delete_profile(self.config, scene["id"])
        self.refresh_scenes()
        self.on_scenes_changed()

    def _on_dual_toggled(self, checked):
        self.cb_second_device.setEnabled(checked)
        self.sl_secondary_volume.setEnabled(checked)

    def set_panic_label(self, hotkey_text):
        self.btn_panic.setText(tr("settings.panic_current", key=hotkey_text))

    def _save(self):
        self.config["language"] = self._language_codes[self.cb_language.currentIndex()]
        self.config["primary_output"] = self.cb_main_device.currentText()
        self.config["dual_output_enabled"] = self.chk_dual.isChecked()
        self.config["secondary_output"] = self.cb_second_device.currentText()
        self.config["global_secondary_volume"] = self.sl_secondary_volume.value()
        self.config["master_volume"] = self.sl_master_volume.value()
        self.config["mode_solo"] = self.chk_solo.isChecked()
        self.config["fade_in_ms"] = self.spin_fade_in.value()
        self.config["fade_out_ms"] = self.spin_fade_out.value()
        self.on_save(self.config)
        # Inline confirmation rather than a modal to dismiss: saving settings
        # is not an event worth interrupting the user for.
        self.btn_save.setText(tr("settings.saved"))
        QTimer.singleShot(1600, self._restore_save_label)

    def _restore_save_label(self):
        # Saving may have changed the language, which rebuilds the whole UI
        # and destroys this view. Firing on a deleted widget is not an error
        # worth surfacing.
        try:
            self.btn_save.setText(tr("settings.save"))
        except RuntimeError:
            pass
