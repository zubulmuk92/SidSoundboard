import os
import glob
import config_manager

def cleanup_caches(config=None):
    """
    Supprime tous les fichiers _v*_s* qui ne sont pas dans le config actuel.
    """
    if config is None:
        config = config_manager.load_config()
        
    active_files = set()
    for sound in config.get("sounds", []):
        if "cached_file_primary" in sound and sound["cached_file_primary"]:
            active_files.add(os.path.abspath(sound["cached_file_primary"]))
        if "cached_file_secondary" in sound and sound["cached_file_secondary"]:
            active_files.add(os.path.abspath(sound["cached_file_secondary"]))
        # Keep original files obviously, but they shouldn't match the regex unless named that way
        if "file" in sound and sound["file"]:
            active_files.add(os.path.abspath(sound["file"]))
            
    # On cherche tous les fichiers _v*_s* dans les répertoires des sons originaux
    # et dans le dossier courant
    search_dirs = set([os.path.abspath(".")])
    for f in active_files:
        search_dirs.add(os.path.dirname(f))
        
    for d in search_dirs:
        # Pattern: *_v*_s*.*
        pattern = os.path.join(d, "*_v*_s*.*")
        for f in glob.glob(pattern):
            abs_f = os.path.abspath(f)
            if abs_f not in active_files:
                try:
                    os.remove(abs_f)
                    print(f"Nettoyé: {abs_f}")
                except Exception as e:
                    pass
