"""Tests for build pipeline — ProjectBuilder."""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path

from xtc_dial_factory.build.builder import ProjectBuilder, BuildError


class TestBuilderInit:
    def test_creates_with_settings(self, sample_cl_project):
        mock_settings = MagicMock()
        mock_settings.sdk_path = "/fake/sdk"
        mock_settings.build_tools_version = "37.0.0"
        mock_settings.java_home = ""
        builder = ProjectBuilder(mock_settings)
        assert builder is not None
        assert builder._is_windows == sys.platform.startswith("win")


class TestFindSdkTool:
    def test_tool_not_found_raises(self):
        mock_settings = MagicMock()
        mock_settings.sdk_path = "/nonexistent"
        mock_settings.build_tools_version = "99.0.0"
        builder = ProjectBuilder(mock_settings)

        with pytest.raises(BuildError) as exc:
            builder._find_sdk_tool("nonexistent_tool")
        assert "not found" in str(exc.value).lower()


class TestAndroidJar:
    def test_no_platforms_dir_raises(self):
        mock_settings = MagicMock()
        mock_settings.sdk_path = "/nonexistent"
        builder = ProjectBuilder(mock_settings)

        with pytest.raises(BuildError) as exc:
            builder._android_jar()
        assert "not found" in str(exc.value)


class TestStubsDir:
    def test_stubs_dir_exists(self, sample_cl_project):
        mock_settings = MagicMock()
        builder = ProjectBuilder(mock_settings)
        stubs = builder._stubs_dir()
        assert "resources" in stubs and "stubs" in stubs
        assert os.path.isdir(stubs)


class TestGetJavac:
    def test_default_javac(self):
        mock_settings = MagicMock()
        mock_settings.java_home = ""
        builder = ProjectBuilder(mock_settings)
        javac = builder._get_javac()
        assert javac == "javac"  # falls back to PATH

    def test_java_home_used_when_set(self):
        mock_settings = MagicMock()
        mock_settings.java_home = "/usr/lib/jvm/java-11"
        builder = ProjectBuilder(mock_settings)
        with patch("os.path.exists", return_value=True):
            javac = builder._get_javac()
            assert "javac" in javac
            assert "/usr/lib/jvm/java-11" in javac


class TestBuildFlow:
    def test_compose_dial_skips_build(self, sample_compose_project):
        mock_settings = MagicMock()
        builder = ProjectBuilder(mock_settings)
        success, msg = builder.build(sample_compose_project)
        assert success is True

    def test_no_source_dir_raises(self, sample_cl_project):
        mock_settings = MagicMock()
        mock_settings.sdk_path = "/fake/sdk"
        mock_settings.build_tools_version = "37.0.0"
        builder = ProjectBuilder(mock_settings)

        with patch.object(builder, '_compile_java',
                          side_effect=BuildError("Source directory not found")):
            success, msg = builder.build(sample_cl_project)
            assert success is False
            assert "Source directory not found" in msg

    def test_compile_java_no_files(self, temp_project_dir):
        mock_settings = MagicMock()
        mock_settings.sdk_path = "/fake/sdk"
        mock_settings.java_home = ""
        builder = ProjectBuilder(mock_settings)

        # Remove java files to trigger error
        src_dir = temp_project_dir.get_src_dir()
        for f in Path(src_dir).rglob("*.java"):
            os.remove(f)

        with pytest.raises(BuildError) as exc:
            builder._compile_java(temp_project_dir)
        assert "No Java source" in str(exc.value)


class TestBuildError:
    def test_is_exception(self):
        err = BuildError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"

    def test_builder_returns_false_on_error(self, sample_cl_project):
        mock_settings = MagicMock()
        mock_settings.sdk_path = "/fake"
        mock_settings.build_tools_version = "37.0.0"
        mock_settings.java_home = ""
        builder = ProjectBuilder(mock_settings)

        # Mock build to raise
        with patch.object(builder, '_compile_java',
                          side_effect=BuildError("mock failure")):
            success, msg = builder.build(sample_cl_project)
            assert success is False
