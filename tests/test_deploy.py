"""Tests for device deployment — Deployer."""

import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock, call
from pathlib import Path

from xtc_dial_factory.build.deploy import Deployer, DeployError, _quote, _sanitize_adb_arg, _check_frida


class TestDevicePaths:
    def test_cl_dial_paths(self, sample_cl_project):
        d = Deployer(MagicMock())
        paths = d._device_paths(sample_cl_project)
        assert paths["target_dir"] == "/sdcard/xtc/dial/testdial/"
        assert paths["config_path"] == "/sdcard/xtc/dial/testdial/config.json"
        assert paths["output_file"] is not None
        assert paths["output_file"].endswith("testdial.cl")

    def test_pl_plugin_paths(self, sample_pl_project):
        sample_pl_project.version_code = 3
        d = Deployer(MagicMock())
        paths = d._device_paths(sample_pl_project)
        assert paths["target_dir"] == "/sdcard/xtc/dial/compose/element/testplugin/3/"
        assert paths["output_file"].endswith("testplugin.pl")

    def test_compose_dial_paths(self, sample_compose_project):
        d = Deployer(MagicMock())
        paths = d._device_paths(sample_compose_project)
        assert paths["target_dir"] == "/sdcard/xtc/dial/compose/custom_dial/123456/"
        assert paths["output_file"] is None


class TestCheckAdb:
    def test_no_devices_raises(self):
        d = Deployer(MagicMock())
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "List of devices attached\n\n"
        mock_result.stderr = ""

        with patch.object(d, '_adb', return_value=mock_result):
            with pytest.raises(DeployError) as exc:
                d._check_adb()
            assert "未检测到" in str(exc.value)

    def test_device_found_ok(self):
        d = Deployer(MagicMock())
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "List of devices attached\nemulator-5554\tdevice\n"
        mock_result.stderr = ""

        with patch.object(d, '_adb', return_value=mock_result):
            d._check_adb()  # should not raise


class TestDeployFlow:
    def test_no_output_file_raises(self, sample_cl_project):
        d = Deployer(MagicMock())
        with patch.object(d, '_check_adb'):
            with patch.object(d, '_device_paths',
                              return_value={"target_dir": "/sdcard/",
                                            "output_file": "/nonexistent/test.cl",
                                            "config_path": "/sdcard/config.json"}):
                success, msg = d.deploy(sample_cl_project, activate=False)
                assert success is False
                assert "编译产物未找到" in msg

    def test_compose_deploy_skips_output_file(self, sample_compose_project):
        d = Deployer(MagicMock())
        with patch.object(d, '_check_adb'):
            with patch.object(d, '_device_paths',
                              return_value={"target_dir": "/sdcard/compose/",
                                            "output_file": None,
                                            "config_path": "/sdcard/compose/config.json",
                                            "preview_l": None, "preview_m": None}):
                with patch.object(d, '_push_compose_config'):
                    with patch.object(d, '_activate'):
                        success, msg = d.deploy(sample_compose_project, activate=True)
                        assert success is True

    def test_deploy_creates_directory(self, sample_cl_project):
        d = Deployer(MagicMock())
        with patch.object(d, '_adb') as mock_adb:
            mock_adb.return_value = MagicMock(returncode=0, stdout="device\tdevice\n")
            # Set up _device_paths with a valid output file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".cl") as tmp:
                paths = {
                    "target_dir": "/sdcard/test/",
                    "output_file": tmp.name,
                    "config_path": "/sdcard/test/config.json",
                    "preview_l": None,
                    "preview_m": None,
                }
                with patch.object(d, '_device_paths', return_value=paths):
                    with patch.object(d, '_adb_shell') as mock_shell:
                        with patch.object(d, '_check_adb'):
                            with patch.object(d, '_activate'):
                                d.deploy(sample_cl_project, activate=True)
                                mock_shell.assert_any_call("mkdir -p '/sdcard/test/'")


class TestQuote:
    def test_quote_simple(self):
        assert _quote("hello") == "'hello'"

    def test_quote_with_single_quote(self):
        result = _quote("it's")
        assert "'" in result

    def test_quote_with_spaces(self):
        assert _quote("/sdcard/xtc/dial/test/") == "'/sdcard/xtc/dial/test/'"


class TestSanitizeAdbArg:
    def test_sanitize_windows_path(self):
        import platform
        if platform.system() == "Windows":
            result = _sanitize_adb_arg("/sdcard/test")
            assert result.startswith("//sdcard") or result == "/sdcard/test"
        else:
            result = _sanitize_adb_arg("/sdcard/test")
            assert result == "/sdcard/test"


class TestCheckFrida:
    def test_frida_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _check_frida()
            assert result is None

    def test_frida_found(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "16.5.1\n"
        with patch("subprocess.run", return_value=mock_result):
            result = _check_frida()
            assert result == "16.5.1"


class TestDeployError:
    def test_is_exception(self):
        err = DeployError("deploy failed")
        assert isinstance(err, Exception)
        assert str(err) == "deploy failed"
