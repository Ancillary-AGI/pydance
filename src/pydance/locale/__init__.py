import json
from typing import Dict, Optional, Union


class TranslationManager:
    """Manages translations and localization."""

    def __init__(self):
        self.translations: Dict[str, Dict[str, str]] = {}
        self.current_language = 'en'
        self._local = local()

    def load_translations(self, language: str, translations: Dict[str, str]):
        """Load translations for a language."""
        self.translations[language] = translations

    def load_from_file(self, file_path: Union[str, Path], language: str):
        """Load translations from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            translations = json.load(f)

        self.load_translations(language, translations)

    def load_from_directory(self, directory: Union[str, Path]):
        """Load all translation files from a directory."""
        dir_path = Path(directory)

        for file_path in dir_path.glob('*.json'):
            language = file_path.stem  # filename without extension
            self.load_from_file(file_path, language)

    def get_translation(self, key: str, language: Optional[str] = None) -> str:
        """Get translation for a key."""
        lang = language or self.current_language

        if lang in self.translations and key in self.translations[lang]:
            return self.translations[lang][key]

        return key  # Return key as fallback

    def set_language(self, language: str):
        """Set current language."""
        self.current_language = language

    @property
    def language(self) -> str:
        """Get current language."""
        return self.current_language


class Translator:
    """Translation utility class."""

    def __init__(self, manager: TranslationManager):
        self.manager = manager

    def __call__(self, key: str) -> str:
        """Translate a key."""
        return self.manager.get_translation(key)

    def gettext(self, key: str) -> str:
        """Get translated text (alias for __call__)."""
        return self(key)


# Global translation manager
_translation_manager = TranslationManager()
translator = Translator(_translation_manager)


def gettext(key: str) -> str:
    """Get translated text."""
    return _translation_manager.get_translation(key)


def ngettext(singular: str, plural: str, count: int) -> str:
    """Get pluralized translated text."""
    # Simple pluralization - in real implementation would be more sophisticated
    if count == 1:
        return _translation_manager.get_translation(singular)
    else:
        return _translation_manager.get_translation(plural)


def activate(language: str):
    """Activate a language."""
    _translation_manager.set_language(language)


def get_current_language() -> str:
    """Get current language."""
    return _translation_manager.language


def load_translations_from_directory(directory: Union[str, Path]):
    """Load translations from directory."""
    _translation_manager.load_from_directory(directory)


__all__ = [
    'TranslationManager',
    'Translator',
    'translator',
    'gettext',
    'ngettext',
    'activate',
    'get_current_language',
    'load_translations_from_directory'
]
