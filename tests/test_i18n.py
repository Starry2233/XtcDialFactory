"""Tests for i18n localization system."""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch

from xtc_dial_factory.i18n import I18n


# Real locales dir for tests that need actual translations
REAL_LOCALES = Path(__file__).parent.parent / "locales"


class TestI18n:
    def setup_method(self):
        I18n._instance = None
        I18n._translations = {}
        I18n._current_lang = "zh_CN"

    def test_singleton(self):
        a = I18n.instance()
        b = I18n.instance()
        assert a is b

    def test_tr_zh_cn(self):
        with patch("xtc_dial_factory.i18n._LOCALES_DIR", REAL_LOCALES):
            I18n._instance = None
            i18n = I18n.instance()
            i18n.set_language("zh_CN")
            result = i18n.tr("app.name")
            assert result == "XTC Dial Factory"

    def test_tr_en_us(self):
        with patch("xtc_dial_factory.i18n._LOCALES_DIR", REAL_LOCALES):
            I18n._instance = None
            i18n = I18n.instance()
            i18n.set_language("en_US")
            result = i18n.tr("app.description")
            assert "Smart Watch" in result

    def test_tr_fallback_to_key(self):
        with patch("xtc_dial_factory.i18n._LOCALES_DIR", REAL_LOCALES):
            I18n._instance = None
            i18n = I18n.instance()
            result = i18n.tr("nonexistent_key_xyz")
            assert result == "nonexistent_key_xyz"

    def test_tr_fallback_to_default(self):
        with patch("xtc_dial_factory.i18n._LOCALES_DIR", REAL_LOCALES):
            I18n._instance = None
            i18n = I18n.instance()
            result = i18n.tr("nonexistent_key", "Custom Default")
            assert result == "Custom Default"

    def test_set_language_unsupported(self):
        I18n._instance = None
        i18n = I18n.instance()
        i18n.set_language("fr_FR")
        assert i18n.current_language() == "zh_CN"

    def test_current_language(self):
        I18n._instance = None
        i18n = I18n.instance()
        i18n.set_language("en_US")
        assert i18n.current_language() == "en_US"

    def test_supported_languages(self):
        langs = I18n.supported_languages()
        assert "zh_CN" in langs
        assert "en_US" in langs
        assert langs["zh_CN"] == "中文 (简体)"

    def test_reload_on_language_change(self):
        with patch("xtc_dial_factory.i18n._LOCALES_DIR", REAL_LOCALES):
            I18n._instance = None
            i18n = I18n.instance()
            i18n.set_language("zh_CN")
            zh_result = i18n.tr("app.description")
            i18n.set_language("en_US")
            en_result = i18n.tr("app.description")
            assert zh_result != en_result
            assert zh_result == "小天才电话手表表盘开发IDE"

    @pytest.fixture
    def temp_locale_dir(self, tmp_path):
        locale_dir = tmp_path / "locales"
        locale_dir.mkdir()
        with open(locale_dir / "zh_CN.json", "w", encoding="utf-8") as f:
            json.dump({"greeting": "你好", "farewell": "再见"}, f, ensure_ascii=False)
        with open(locale_dir / "en_US.json", "w", encoding="utf-8") as f:
            json.dump({"greeting": "Hello", "farewell": "Goodbye"}, f)
        return locale_dir

    def test_custom_locale_dir(self, temp_locale_dir):
        with patch("xtc_dial_factory.i18n._LOCALES_DIR", temp_locale_dir):
            I18n._instance = None
            i18n = I18n.instance()
            i18n.set_language("zh_CN")
            assert i18n.tr("greeting") == "你好"
            i18n.set_language("en_US")
            assert i18n.tr("greeting") == "Hello"

    def test_missing_file_fallback(self, tmp_path):
        with patch("xtc_dial_factory.i18n._LOCALES_DIR", tmp_path):
            I18n._instance = None
            i18n = I18n.instance()
            result = i18n.tr("app.name")
            assert result == "app.name"

    def test_detect_system_locale(self):
        """Test that system locale auto-detection works."""
        with patch("locale.getlocale", return_value=("zh_CN", "UTF-8")):
            I18n._instance = None
            i18n = I18n.instance()
            assert i18n.current_language() == "zh_CN"
