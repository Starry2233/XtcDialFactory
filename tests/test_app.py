"""Tests for application settings and app factory."""

import json
import pytest
from unittest.mock import patch, MagicMock

from xtc_dial_factory.app import AppSettings, create_app


class TestAppSettings:
    @pytest.fixture
    def mock_qsettings(self):
        """Create a mock QSettings that actually stores/retrieves values."""
        storage = {}

        def mock_value(key, default=None):
            return storage.get(key, default)

        def mock_setValue(key, value):
            storage[key] = value

        with patch("xtc_dial_factory.app.QSettings") as mock_qs:
            instance = MagicMock()
            instance.value.side_effect = mock_value
            instance.setValue.side_effect = mock_setValue
            mock_qs.return_value = instance
            yield instance

    def test_default_values(self):
        with patch("xtc_dial_factory.app.QSettings") as mock_qs:
            mock_instance = MagicMock()
            mock_instance.value.side_effect = lambda key, default=None: default
            mock_qs.return_value = mock_instance

            s = AppSettings()
            path = s.sdk_path
            assert path is not None
            assert isinstance(path, str)

    def test_recent_projects_roundtrip(self, mock_qsettings):
        s = AppSettings()
        projects = ["/path/one", "/path/two"]
        s.recent_projects = projects
        result = s.recent_projects
        assert result == projects

    def test_add_recent_project_deduplicates(self, mock_qsettings):
        s = AppSettings()
        s.recent_projects = ["/first", "/second"]
        s.add_recent_project("/first")
        result = s.recent_projects
        assert result[0] == "/first"
        assert result.count("/first") == 1

    def test_add_recent_project_max_10(self, mock_qsettings):
        s = AppSettings()
        s.recent_projects = [f"/path/{i}" for i in range(10)]
        s.add_recent_project("/new")
        result = s.recent_projects
        assert len(result) <= 10
        assert result[0] == "/new"

    def test_keystore_defaults(self):
        with patch("xtc_dial_factory.app.QSettings") as mock_qs:
            mock_instance = MagicMock()
            mock_instance.value.side_effect = lambda k, d=None: d
            mock_qs.return_value = mock_instance

            s = AppSettings()
            assert s.keystore_path == "E:/android.keystore"
            assert s.keystore_password == ""
            assert s.keystore_alias == ""

    def test_sdk_path_setter(self, mock_qsettings):
        s = AppSettings()
        s.sdk_path = "/custom/sdk"
        assert s.sdk_path == "/custom/sdk"

    def test_build_tools_default(self):
        with patch("xtc_dial_factory.app.QSettings") as mock_qs:
            mock_instance = MagicMock()
            mock_instance.value.side_effect = lambda key, default=None: default
            mock_qs.return_value = mock_instance
            s = AppSettings()
            assert s.build_tools_version == "37.0.0"


class TestCreateApp:
    def test_create_app(self):
        with patch("xtc_dial_factory.app.QApplication") as mock_app:
            mock_instance = MagicMock()
            mock_app.return_value = mock_instance

            app = create_app([])
            assert app is not None
            mock_app.assert_called_once()

    def test_create_app_sets_metadata(self):
        with patch("xtc_dial_factory.app.QApplication") as mock_app:
            mock_instance = MagicMock()
            mock_app.return_value = mock_instance

            app = create_app([])
            mock_instance.setApplicationName.assert_called_once()
            mock_instance.setApplicationVersion.assert_called_once()
            mock_instance.setOrganizationName.assert_called_once()
