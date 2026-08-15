"""
Minimal translation catalog.

Deliberately not Qt Linguist: .ts/.qm files would add a build step and a
toolchain dependency for two languages and a few dozen strings, against
this project's whole premise of staying light. A dict lookup costs
nothing and ships inside the .exe for free.

Category names are NOT translated as data — `config["sounds"][i]["color"]`
keeps its canonical French key so an existing library survives a language
change. Only the label shown in the combo box is localized.
"""

DEFAULT_LANGUAGE = "fr"

# Language code -> name, always shown in its own language.
LANGUAGES = {"fr": "Français", "en": "English"}

_current_language = DEFAULT_LANGUAGE

TRANSLATIONS = {
    "fr": {
        # Navigation and window chrome
        "nav.library": " Bibliothèque",
        "nav.settings": " Réglages",
        "panic.button": "PANIQUE",
        "panic.tooltip": "Coupe immédiatement tous les sons en cours",
        "panic.hint": "ou la touche {key}",

        # Shared
        "common.error": "Erreur",
        "common.please_wait": "Veuillez patienter",
        "common.cancel": "Annuler",
        "common.confirm": "Confirmation",
        "common.none": "Aucune",

        # Library
        "library.search": "Rechercher un son (titre, touche, catégorie)…",
        "library.import": " IMPORTER",
        "library.youtube": " YOUTUBE",
        "library.pick_file": "Sélectionner un fichier audio",
        "library.audio_filter": "Fichiers audio (*.mp3 *.wav *.ogg *.flac *.m4a)",
        "library.importing": "Importation et normalisation en cours…",
        "library.import_failed": "Échec de l'import du fichier audio.",
        "library.delete_body": "Êtes-vous sûr de vouloir supprimer ce son ?",
        "library.empty_search": "Aucun son ne correspond à cette recherche.",
        "library.empty": (
            "Votre bibliothèque est vide.\n\n"
            "Importez un fichier audio, ou collez une URL YouTube pour "
            "télécharger un son directement."
        ),

        # YouTube dialog
        "yt.title": "Télécharger depuis YouTube",
        "yt.url": "URL YouTube (https://…)",
        "yt.name": "Nom du son (optionnel)",
        "yt.download": "TÉLÉCHARGER",
        "yt.failed": "Échec : {error}",

        # Sound card
        "card.play": " PLAY",
        "card.pause": " PAUSE",
        "card.edit_tooltip": "Éditer le son (effets, découpe, fondus)",
        "card.delete_tooltip": "Supprimer ce son",

        # Player bar
        "player.idle": "Aucun son en cours",
        "player.playing": "En cours : {name}",
        "player.paused": "En pause : {name}",

        # Settings
        "settings.title": "Réglages Audio",
        "settings.language": "Langue :",
        "settings.primary_device": "Périphérique principal :",
        "settings.dual_output": "Activer la double sortie",
        "settings.secondary_device": "Périphérique secondaire (câble virtuel) :",
        "settings.secondary_volume": "Volume envoyé sur le câble virtuel :",
        "settings.solo": "Mode solo — un seul son à la fois",
        "settings.fade_in": "Fondu d'entrée (ms) :",
        "settings.fade_out": "Fondu de sortie (ms) :",
        "settings.panic_key": "Touche panique globale :",
        "settings.panic_current": "Touche : {key}",
        "settings.press_key": "Appuyez sur une touche…",
        "settings.save": "SAUVEGARDER",
        "settings.saved": "ENREGISTRÉ ✓",

        # Sound editor
        "editor.title": "Éditer — {name}",
        "editor.name": "Nom :",
        "editor.category": "Catégorie :",
        "editor.trim_hint": "Découpe — glissez les poignées pour choisir la partie à garder",
        "editor.trim_range": "Garde de {start:.2f}s à {end:.2f}s ({length:.2f}s)",
        "editor.volume": "Volume :",
        "editor.speed": "Vitesse :",
        "editor.speed_hint": "change aussi la hauteur de la voix",
        "editor.bass": "Bass Booster :",
        "editor.reverb": "Reverb :",
        "editor.fade_in": "Fondu d'entrée :",
        "editor.fade_out": "Fondu de sortie :",
        "editor.preview": "APERÇU",
        "editor.rendering": "RENDU…",
        "editor.save": "ENREGISTRER",
        "editor.render_failed": "Échec du rendu audio :\n{error}",

        # Tray
        "tray.open": "Ouvrir l'interface",
        "tray.quit": "Quitter",

        # Categories (display only — the stored key stays French)
        "category.Sons Troll": "Sons Troll",
        "category.Musiques": "Musiques",
        "category.SFX": "SFX",
        "category.Voix": "Voix",
        "category.Ambiance": "Ambiance",
        "category.Gris": "Sans catégorie",
    },
    "en": {
        "nav.library": " Library",
        "nav.settings": " Settings",
        "panic.button": "PANIC",
        "panic.tooltip": "Cuts every playing sound immediately",
        "panic.hint": "or the {key} key",

        "common.error": "Error",
        "common.please_wait": "Please wait",
        "common.cancel": "Cancel",
        "common.confirm": "Confirm",
        "common.none": "None",

        "library.search": "Search a sound (name, key, category)…",
        "library.import": " IMPORT",
        "library.youtube": " YOUTUBE",
        "library.pick_file": "Choose an audio file",
        "library.audio_filter": "Audio files (*.mp3 *.wav *.ogg *.flac *.m4a)",
        "library.importing": "Importing and normalizing…",
        "library.import_failed": "Could not import the audio file.",
        "library.delete_body": "Delete this sound?",
        "library.empty_search": "No sound matches this search.",
        "library.empty": (
            "Your library is empty.\n\n"
            "Import an audio file, or paste a YouTube URL to download a "
            "sound directly."
        ),

        "yt.title": "Download from YouTube",
        "yt.url": "YouTube URL (https://…)",
        "yt.name": "Sound name (optional)",
        "yt.download": "DOWNLOAD",
        "yt.failed": "Failed: {error}",

        "card.play": " PLAY",
        "card.pause": " PAUSE",
        "card.edit_tooltip": "Edit this sound (effects, trim, fades)",
        "card.delete_tooltip": "Delete this sound",

        "player.idle": "Nothing playing",
        "player.playing": "Playing: {name}",
        "player.paused": "Paused: {name}",

        "settings.title": "Audio Settings",
        "settings.language": "Language:",
        "settings.primary_device": "Main device:",
        "settings.dual_output": "Enable dual output",
        "settings.secondary_device": "Secondary device (virtual cable):",
        "settings.secondary_volume": "Volume sent to the virtual cable:",
        "settings.solo": "Solo mode — one sound at a time",
        "settings.fade_in": "Fade in (ms):",
        "settings.fade_out": "Fade out (ms):",
        "settings.panic_key": "Global panic key:",
        "settings.panic_current": "Key: {key}",
        "settings.press_key": "Press a key…",
        "settings.save": "SAVE",
        "settings.saved": "SAVED ✓",

        "editor.title": "Edit — {name}",
        "editor.name": "Name:",
        "editor.category": "Category:",
        "editor.trim_hint": "Trim — drag the handles to pick the part you keep",
        "editor.trim_range": "Keeping {start:.2f}s to {end:.2f}s ({length:.2f}s)",
        "editor.volume": "Volume:",
        "editor.speed": "Speed:",
        "editor.speed_hint": "also shifts the pitch",
        "editor.bass": "Bass booster:",
        "editor.reverb": "Reverb:",
        "editor.fade_in": "Fade in:",
        "editor.fade_out": "Fade out:",
        "editor.preview": "PREVIEW",
        "editor.rendering": "RENDERING…",
        "editor.save": "SAVE",
        "editor.render_failed": "Audio rendering failed:\n{error}",

        "tray.open": "Open the interface",
        "tray.quit": "Quit",

        "category.Sons Troll": "Troll Sounds",
        "category.Musiques": "Music",
        "category.SFX": "SFX",
        "category.Voix": "Voice",
        "category.Ambiance": "Ambience",
        "category.Gris": "Uncategorized",
    },
}


def set_language(code):
    """Selects the active language, ignoring codes we have no catalog for."""
    global _current_language
    if code in TRANSLATIONS:
        _current_language = code
    return _current_language


def get_language():
    return _current_language


def tr(key, /, **kwargs):
    """
    Looks the key up in the active catalog, falling back to French and then
    to the key itself, so a missing translation degrades to something
    readable instead of blowing up mid-render.

    `key` is positional-only on purpose: several strings interpolate a
    placeholder literally named {key}, which would otherwise collide with
    this parameter.
    """
    catalog = TRANSLATIONS.get(_current_language, {})
    text = catalog.get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def category_label(key):
    """Display name for a category whose stored value is always French."""
    return tr(f"category.{key}")


def category_key(label):
    """Inverse of category_label — turns what the combo shows back into the
    value written to the config."""
    for key in ("Sons Troll", "Musiques", "SFX", "Voix", "Ambiance", "Gris"):
        if category_label(key) == label:
            return key
    return label
