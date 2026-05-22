"""Tests for data models — Project, DialConfig, NetComposeDial, ThemeAssemblyElement."""

import json
import pytest
from xtc_dial_factory.models.project import (
    Project, ProjectType, ClockType, DialConfig, NetComposeDial, ThemeAssemblyElement
)


class TestProject:
    def test_create_cl_project(self):
        p = Project("MyDial", ProjectType.CL_DIAL)
        assert p.name == "MyDial"
        assert p.project_type == ProjectType.CL_DIAL
        assert p.package_name == "com.xtc.mydial"
        assert p.source_name == "mydial"

    def test_create_pl_project(self):
        p = Project("MyPlugin", ProjectType.PL_PLUGIN, "com.custom.plugin")
        assert p.project_type == ProjectType.PL_PLUGIN
        assert p.package_name == "com.custom.plugin"

    def test_create_compose_project(self):
        p = Project("MyCompose", ProjectType.COMPOSE_DIAL)
        assert p.project_type == ProjectType.COMPOSE_DIAL

    def test_source_name_compose(self):
        p = Project("MyCompose", ProjectType.COMPOSE_DIAL)
        p.compose_dial = NetComposeDial(id=999)
        assert p.source_name == "999"

    def test_get_dial_dir(self):
        p = Project("MyDial", ProjectType.CL_DIAL)
        assert p.get_dial_dir() == f"/sdcard/xtc/dial/{p.source_name}/"

    def test_get_src_dir(self, sample_cl_project):
        src = sample_cl_project.get_src_dir()
        assert src.endswith("com/xtc/testdial")

    def test_get_manifest_path(self, sample_cl_project):
        assert sample_cl_project.get_manifest_path().endswith("AndroidManifest.xml")

    def test_serialize_roundtrip(self):
        p = Project("RoundTrip", ProjectType.CL_DIAL, "com.xtc.round", "author")
        d = p.to_dict()
        p2 = Project.from_dict(d)
        assert p2.name == "RoundTrip"
        assert p2.package_name == "com.xtc.round"
        assert p2.author == "author"
        assert p2.project_type == ProjectType.CL_DIAL

    def test_dirty_flag(self):
        p = Project("Test")
        assert not p.is_dirty
        p.mark_dirty()
        assert p.is_dirty
        p.mark_clean()
        assert not p.is_dirty


class TestDialConfig:
    def test_defaults(self):
        dc = DialConfig()
        assert dc.sourceName == ""
        assert dc.clockType == 1
        assert dc.useState == 1
        assert dc.keyVersion == 0

    def test_to_json_contains_keys(self):
        dc = DialConfig(sourceName="xtcwatch", clockType=1)
        j = dc.to_json()
        assert '"sourceName"' in j
        assert '"xtcwatch"' in j
        assert '"clockType"' in j

    def test_to_json_valid(self):
        dc = DialConfig(sourceName="test", clockType=1, useState=1, versionCode=5)
        parsed = json.loads(dc.to_json())
        assert parsed["sourceName"] == "test"
        assert parsed["versionCode"] == 5

    def test_from_json(self):
        raw = '{"sourceName":"xtcwatch","clockType":1,"useState":1,"dialDir":"/sdcard/xtc/dial/xtcwatch/"}'
        dc = DialConfig.from_json(raw)
        assert dc.sourceName == "xtcwatch"
        assert dc.clockType == 1

    def test_from_json_ignores_unknown(self):
        raw = '{"sourceName":"test","unknownField":"ignored"}'
        dc = DialConfig.from_json(raw)
        assert dc.sourceName == "test"

    def test_roundtrip(self, sample_dial_config):
        j = sample_dial_config.to_json()
        dc2 = DialConfig.from_json(j)
        assert dc2.sourceName == sample_dial_config.sourceName
        assert dc2.clockType == sample_dial_config.clockType
        assert dc2.versionCode == sample_dial_config.versionCode


class TestThemeAssemblyElement:
    def test_defaults(self):
        e = ThemeAssemblyElement()
        assert e.component == ""
        assert e.type == 1
        assert e.x == 0
        assert e.y == 0
        assert e.width == 100
        assert e.height == 100

    def test_to_dict_omits_none(self):
        e = ThemeAssemblyElement(component="test", componentId=None)
        d = e.to_dict()
        assert "componentId" not in d
        assert d["component"] == "test"

    def test_full(self):
        e = ThemeAssemblyElement(
            component="time_no_6", componentId=916, type=1,
            x=56, y=3, width=180, height=86,
            dpX=28.0, dpY=1.5, dpWidth=90.0, dpHeight=43.0,
            versionCode=10, extra='{"previewStyle":5}'
        )
        d = e.to_dict()
        assert d["component"] == "time_no_6"
        assert d["type"] == 1
        assert d["x"] == 56
        assert d["width"] == 180


class TestNetComposeDial:
    def test_defaults(self):
        n = NetComposeDial()
        assert n.name == "新组合表盘"
        assert n.elementList == []

    def test_with_elements(self, sample_compose_project):
        n = sample_compose_project.compose_dial
        assert n is not None
        assert len(n.elementList) == 2
        assert n.elementList[0].component == "time_no_6"

    def test_to_json_valid(self, sample_compose_project):
        n = sample_compose_project.compose_dial
        j = n.to_json()
        parsed = json.loads(j)
        assert parsed["name"] == "TestCompose"
        assert len(parsed["elementList"]) == 2
        assert parsed["elementList"][0]["component"] == "time_no_6"

    def test_from_json(self):
        raw = '''{
            "id": 1,
            "name": "Test",
            "elementList": [
                {"component": "time", "type": 1, "x": 10, "y": 20, "width": 100, "height": 50}
            ]
        }'''
        n = NetComposeDial.from_json(raw)
        assert n.name == "Test"
        assert len(n.elementList) == 1
        assert n.elementList[0].x == 10

    def test_roundtrip(self, sample_compose_project):
        n = sample_compose_project.compose_dial
        j = n.to_json()
        n2 = NetComposeDial.from_json(j)
        assert n2.name == n.name
        assert len(n2.elementList) == len(n.elementList)
        for e1, e2 in zip(n.elementList, n2.elementList):
            assert e1.component == e2.component
            assert e1.x == e2.x
            assert e1.y == e2.y


class TestClockType:
    def test_values(self):
        assert ClockType.DEFAULT_CODE.value == -2
        assert ClockType.TRADITIONAL_CL.value == 1
        assert ClockType.COMPOSE_DIY.value == 9

    def test_from_value(self):
        assert ClockType.from_value(1) == ClockType.TRADITIONAL_CL
        assert ClockType.from_value(9) == ClockType.COMPOSE_DIY
        assert ClockType.from_value(999) == ClockType.TRADITIONAL_CL  # default
