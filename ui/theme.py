import os
import sys

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def _detect_windows_dark_mode():
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except Exception:
        return True


IS_DARK_MODE = _detect_windows_dark_mode()

# Visual direction: ice seen from underneath. Deep meltwater blues with a
# green cast, and an accent taken from the turquoise of a glacier crevasse
# rather than the expected electric cyan — real glacial ice reads green.
# Warmth is rationed to exactly one place: DANGER, so the panic control
# reads as fire against ice.

DARK_PALETTE = {
    "BG_APP": "#0A141B",
    "BG_PANEL": "#122430",
    "BG_HOVER": "#1C3646",
    "TEXT_MAIN": "#EAF6FA",
    "TEXT_MUTED": "#7392A6",
    "ACCENT": "#59E1D8",
    "ACCENT_HOVER": "#33C9C0",
    "ACCENT_TEXT": "#04161A",
    "DANGER": "#FF6B5B",
    "EDGE": "#2A4E63",
}

LIGHT_PALETTE = {
    "BG_APP": "#EAF2F5",
    "BG_PANEL": "#FFFFFF",
    "BG_HOVER": "#D5E5EC",
    "TEXT_MAIN": "#0C2029",
    "TEXT_MUTED": "#54707E",
    "ACCENT": "#0E8C87",
    "ACCENT_HOVER": "#0A6E6A",
    "ACCENT_TEXT": "#FFFFFF",
    "DANGER": "#D4453A",
    "EDGE": "#BBD3DE",
}

_PALETTE = DARK_PALETTE if IS_DARK_MODE else LIGHT_PALETTE

BG_APP = _PALETTE["BG_APP"]
BG_PANEL = _PALETTE["BG_PANEL"]
BG_HOVER = _PALETTE["BG_HOVER"]
TEXT_MAIN = _PALETTE["TEXT_MAIN"]
TEXT_MUTED = _PALETTE["TEXT_MUTED"]
ACCENT = _PALETTE["ACCENT"]
ACCENT_HOVER = _PALETTE["ACCENT_HOVER"]
ACCENT_TEXT = _PALETTE["ACCENT_TEXT"]
DANGER = _PALETTE["DANGER"]
# The lit top edge of a slab of ice — used as a 1px highlight on cards.
EDGE = _PALETTE["EDGE"]

# Cold spectrum, with two warm anchors so the grid still sorts at a glance
# mid-game: troll sounds burn, voices glow, everything else is ice.
CATEGORY_COLORS = {
    "Sons Troll": "#FF7A59",
    "Musiques": "#5AA9F0",
    "SFX": "#59E1D8",
    "Voix": "#F2C55C",
    "Ambiance": "#A98CF0",
    "Gris": TEXT_MUTED,
}

_ICON_CACHE = {}


def get_icon(name, color=None):
    """Loads an icons/*.svg file and bakes `color` in place of its
    currentColor placeholder — Qt's SVG renderer does not resolve
    currentColor itself and would otherwise paint it solid black."""
    color = color or TEXT_MAIN
    cache_key = (name, color)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    path = os.path.join(resource_path("icons"), name)
    with open(path, "r", encoding="utf-8") as f:
        svg_data = f.read().replace("currentColor", color)

    renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
    pixmap = QPixmap(QSize(48, 48))
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    icon = QIcon(pixmap)
    _ICON_CACHE[cache_key] = icon
    return icon


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
QPushButton.accent {{ background-color: {ACCENT}; color: {ACCENT_TEXT}; border: none; }}
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

#Sidebar {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BG_HOVER}, stop:0.45 {BG_PANEL}, stop:1 {BG_APP});
    border-right: 1px solid {EDGE};
}}
#Sidebar #SidebarCaption {{
    color: {TEXT_MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 1px;
}}
#Sidebar #NewSceneButton {{
    background-color: {BG_APP}; color: {ACCENT}; border: 1px solid {EDGE};
    border-radius: 6px; padding: 5px 8px; text-align: center; font-size: 12px;
}}
#Sidebar #NewSceneButton:hover {{ border: 1px solid {ACCENT}; background-color: {BG_HOVER}; }}

#Sidebar QPushButton {{ background-color: transparent; border: none; text-align: left; padding-left: 20px; font-size: 14px; }}
#Sidebar QPushButton:hover {{ background-color: {BG_HOVER}; }}
#Sidebar QPushButton:checked {{ background-color: {BG_APP}; color: {ACCENT}; border-left: 3px solid {ACCENT}; border-radius: 0px; }}

#SoundCard {{ background-color: {BG_PANEL}; border: 1px solid {EDGE}; border-radius: 8px; }}
#SoundCard:hover {{ background-color: {BG_HOVER}; border: 1px solid {ACCENT}; }}

#PlayerBar {{ background-color: {BG_PANEL}; border: 1px solid {EDGE}; border-radius: 8px; }}

#ErrorBanner {{
    background-color: {BG_PANEL};
    color: {DANGER};
    border: 1px solid {DANGER};
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 600;
}}

#EmptyState {{ color: {TEXT_MUTED}; font-size: 14px; }}

/* The one warm thing in the app, shaped like the industrial mushroom
   button it stands for: domed at rest, flattened and sunk when pressed. */
#Sidebar #PanicButton {{
    background-color: qradialgradient(cx:0.5, cy:0.32, radius:0.95, fx:0.5, fy:0.28,
        stop:0 #FF9C8E, stop:0.5 {DANGER}, stop:1 #B62D22);
    color: #FFFFFF;
    border: 2px solid #7C1E15;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-align: center;
    margin: 0px 14px;
}}
#Sidebar #PanicButton:hover {{
    background-color: qradialgradient(cx:0.5, cy:0.32, radius:0.95, fx:0.5, fy:0.28,
        stop:0 #FFB3A7, stop:0.5 #FF7C6B, stop:1 #C93427);
    border: 2px solid #FFB3A7;
}}
#Sidebar #PanicButton:pressed {{
    background-color: qradialgradient(cx:0.5, cy:0.6, radius:0.95, fx:0.5, fy:0.7,
        stop:0 #C93427, stop:1 #8E241B);
    border: 2px solid #5E150F;
    padding-top: 12px;
    padding-bottom: 8px;
}}

#Sidebar #PanicHint {{ color: {TEXT_MUTED}; font-size: 10px; letter-spacing: 0.5px; }}

QProgressBar {{ border: 1px solid {BG_APP}; border-radius: 4px; text-align: center; color: white; background: {BG_PANEL}; }}
QProgressBar::chunk {{ background-color: {ACCENT}; width: 1px; }}
"""
