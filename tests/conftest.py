"""Shared fixtures and configuration for tests."""

import sys
import os
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from xtc_dial_factory.models.project import (
    Project, ProjectType, DialConfig, NetComposeDial, ThemeAssemblyElement
)


@pytest.fixture
def sample_cl_project():
    """Create a minimal .cl dial project."""
    p = Project("TestDial", ProjectType.CL_DIAL, "com.xtc.testdial", "tester")
    p.version_code = 1
    return p


@pytest.fixture
def sample_pl_project():
    """Create a minimal .pl plugin project."""
    p = Project("TestPlugin", ProjectType.PL_PLUGIN, "com.xtc.testplugin", "tester")
    p.version_code = 1
    return p


@pytest.fixture
def sample_compose_project():
    """Create a compose dial project with two elements."""
    p = Project("TestCompose", ProjectType.COMPOSE_DIAL, "com.xtc.testcompose", "tester")
    p.compose_dial = NetComposeDial(
        id=123456,
        name="TestCompose",
        elementList=[
            ThemeAssemblyElement(
                component="time_no_6", componentId=916, type=1,
                x=56, y=3, width=180, height=86, versionCode=10
            ),
            ThemeAssemblyElement(
                component="date_3", componentId=20, type=1,
                x=38, y=82, width=112, height=29, versionCode=15
            ),
        ]
    )
    return p


@pytest.fixture
def sample_dial_config():
    """Create a sample DialConfig matching device format."""
    return DialConfig(
        sourceName="testdial",
        clockType=1,
        useState=1,
        dialDir="/sdcard/xtc/dial/testdial/",
        versionCode=1,
        keyVersion=1,
    )


@pytest.fixture
def temp_project_dir(sample_cl_project):
    """Create a temporary directory with a real project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_cl_project.root_dir = tmpdir
        # Create minimal source tree
        pkg_dir = os.path.join(tmpdir, "src", "main", "java",
                               *sample_cl_project.package_name.split("."))
        os.makedirs(pkg_dir, exist_ok=True)
        # Create stub Java file
        java_file = os.path.join(pkg_dir, "DialViewImpl.java")
        with open(java_file, "w") as f:
            f.write("package com.xtc.testdial;\npublic class DialViewImpl {}\n")
        # Create AndroidManifest.xml
        with open(os.path.join(tmpdir, "AndroidManifest.xml"), "w") as f:
            f.write('<manifest package="com.xtc.testdial"/>')
        # Create config.json
        with open(os.path.join(tmpdir, "config.json"), "w") as f:
            json.dump({"sourceName": "testdial", "clockType": 1}, f)
        yield sample_cl_project
