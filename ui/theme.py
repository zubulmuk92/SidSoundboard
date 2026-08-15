import os
import sys

from PySide6.QtGui import QIcon


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def get_icon(name):
    return QIcon(os.path.join(resource_path("icons"), name))


BG_APP = "#121316"
BG_PANEL = "#1B1D21"
BG_HOVER = "#26292F"
TEXT_MAIN = "#F2F1ED"
TEXT_MUTED = "#8B8D93"
ACCENT = "#FF8A3D"
ACCENT_HOVER = "#E67227"
DANGER = "#EF4444"

CATEGORY_COLORS = {
    "Sons Troll": "#FF3366",
    "Musiques": "#33CCFF",
    "SFX": "#33FF99",
    "Voix": "#FFCC00",
    "Ambiance": "#B829FF",
    "Gris": "#8B8D93",
}

QSS = f"""
QMainWindow, QDialog {{ background-color: {BG_APP}; }}
QWidget {{ color: {TEXT_MAIN}; font-family: 'Inter', 'Segoe UI'; font-size: 13px; }}

QScrollArea {{ border: none; background-color: transparent; }}
QScrollArea > QWidget > QWidget {{ background-color: transparent; }}

QScrollBar:vertical {{ border: none; background: {BG_APP}; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BG_HOVER}; min-height: 20px; border-radius: 5px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}

QPushButton {{
    background-color: {BG_PANEL}; color: {TEXT_MAIN}; border: 1px solid {BG_APP};
    border-radius: 6px; padding: 6px 12px; font-weight: 600;
}}
QPushButton:hover {{ background-color: {BG_HOVER}; border: 1px solid {ACCENT}; }}
QPushButton.accent {{ background-color: {ACCENT}; color: #121316; border: none; }}
QPushButton.accent:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton.danger {{ background-color: transparent; border: 1px solid {DANGER}; color: {DANGER}; }}
QPushButton.danger:hover {{ background-color: {DANGER}; color: white; }}

QLineEdit, QComboBox {{
    background-color: {BG_PANEL}; color: {TEXT_MAIN}; border: 1px solid {BG_HOVER};
    border-radius: 6px; padding: 6px 10px;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{ background-color: {BG_PANEL}; color: {TEXT_MAIN}; selection-background-color: {ACCENT}; }}

QSlider::groove:horizontal {{ border: 1px solid {BG_PANEL}; background: {BG_APP}; height: 6px; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {ACCENT}; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }}

#Sidebar {{ background-color: {BG_PANEL}; border-right: 1px solid {BG_APP}; }}
#Sidebar QPushButton {{ background-color: transparent; border: none; text-align: left; padding-left: 20px; font-size: 14px; }}
#Sidebar QPushButton:hover {{ background-color: {BG_HOVER}; }}
#Sidebar QPushButton:checked {{ background-color: {BG_APP}; color: {ACCENT}; border-left: 3px solid {ACCENT}; border-radius: 0px; }}

#SoundCard {{ background-color: {BG_PANEL}; border: 1px solid {BG_APP}; border-radius: 8px; }}
#SoundCard:hover {{ background-color: {BG_HOVER}; border: 1px solid {ACCENT}; }}

QProgressBar {{ border: 1px solid {BG_APP}; border-radius: 4px; text-align: center; color: white; background: {BG_PANEL}; }}
QProgressBar::chunk {{ background-color: {ACCENT}; width: 1px; }}
"""
