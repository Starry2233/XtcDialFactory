"""Internationalization system for XTC Dial Factory.

Provides a singleton I18n class that loads translations from JSON files
in the locales/ directory. Supports zh_CN and en_US with system locale
auto-detection on first load.
"""

import json
import locale
from pathlib import Path


_LOCALES_DIR = Path(__file__).parent.parent / "locales"

_SUPPORTED_LANGUAGES = {
    "zh_CN": "中文 (简体)",
    "en_US": "English",
}


class I18n:
    """JSON-based translation system singleton.

    Usage:
        I18n.instance().tr("menu.file")
        I18n.instance().set_language("en_US")
    """

    _instance = None
    _translations = {}
    _current_lang = "zh_CN"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._detect_system_locale()
        self._load_translations()

    def _detect_system_locale(self):
        try:
            lang_code, _ = locale.getlocale(locale.LC_CTYPE)
            if lang_code:
                lang_code = lang_code.replace("-", "_")
                if lang_code in _SUPPORTED_LANGUAGES:
                    self._current_lang = lang_code
                    return
                base = lang_code.split("_")[0]
                for supported in _SUPPORTED_LANGUAGES:
                    if supported.startswith(base):
                        self._current_lang = supported
                        return
        except (locale.Error, ValueError, TypeError):
            pass

    def _load_translations(self):
        lang_file = _LOCALES_DIR / f"{self._current_lang}.json"
        if lang_file.exists():
            with open(lang_file, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
        else:
            self._translations = {}

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def tr(self, key: str, default: str = None) -> str:
        """Translate a key to the current language.

        Args:
            key: Translation key to look up.
            default: Fallback value if key is not found.
                     If None, the key itself is used as fallback.

        Returns:
            Translated string, or default/key if not found.
        """
        if default is not None:
            return self._translations.get(key, default)
        return self._translations.get(key, key)

    def set_language(self, lang_code: str):
        """Switch the current language and reload translations."""
        if lang_code not in _SUPPORTED_LANGUAGES:
            lang_code = "zh_CN"
        self._current_lang = lang_code
        self._load_translations()

    def current_language(self) -> str:
        """Return the current language code (e.g. 'zh_CN', 'en_US')."""
        return self._current_lang

    @staticmethod
    def supported_languages():
        """Return dict of language_code -> display_name."""
        return dict(_SUPPORTED_LANGUAGES)
