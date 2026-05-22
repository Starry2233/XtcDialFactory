"""Tests for SDK documentation generator."""

import os
import tempfile
import pytest

from xtc_dial_factory.docs.sdk_doc_generator import SdkDocGenerator


class TestSdkDocGenerator:
    @pytest.fixture
    def generator(self):
        return SdkDocGenerator()

    def test_scan_stubs_finds_classes(self, generator):
        classes = generator.scan_stubs()
        assert len(classes) >= 3

    def test_base_dial_parsed(self, generator):
        classes = generator.scan_stubs()
        base_dial = next(c for c in classes if c["name"] == "BaseDial")
        assert base_dial["type"] == "class"
        assert base_dial["package"] == "com.xtc.common"
        assert "View" in base_dial.get("extends", "")

    def test_iplugin_parsed(self, generator):
        classes = generator.scan_stubs()
        plugin = next(c for c in classes if c["name"] == "IPlugin")
        assert plugin["type"] == "interface"
        assert plugin["package"] == "com.xtc.diydial.iplugin"

    def test_methods_count(self, generator):
        classes = generator.scan_stubs()
        base_dial = next(c for c in classes if c["name"] == "BaseDial")
        assert len(base_dial["methods"]) == 5
        method_names = [m["name"] for m in base_dial["methods"]]
        assert "updateTime" in method_names
        assert "updateBattery" in method_names
        assert "updateStep" in method_names

    def test_iplugin_methods(self, generator):
        classes = generator.scan_stubs()
        plugin = next(c for c in classes if c["name"] == "IPlugin")
        method_names = [m["name"] for m in plugin["methods"]]
        assert "getSourceName" in method_names
        assert "getView" in method_names
        assert "initPlugin" in method_names
        assert "registerCallback" in method_names
        assert "sendMessage" in method_names

    def test_getview_signature(self, generator):
        classes = generator.scan_stubs()
        plugin = next(c for c in classes if c["name"] == "IPlugin")
        getview = next(m for m in plugin["methods"] if m["name"] == "getView")
        assert getview["return_type"] == "View"
        assert len(getview["params"]) == 4
        assert getview["params"][0]["type"] == "Context"
        assert getview["params"][1]["type"] == "int" or "int" in getview["params"][1]["type"]

    def test_imessagecallback_parsed(self, generator):
        classes = generator.scan_stubs()
        cb = next(c for c in classes if c["name"] == "IMessageCallback")
        assert cb["type"] == "interface"
        assert len(cb["methods"]) == 1
        assert cb["methods"][0]["name"] == "callback"

    def test_generate_html(self, generator):
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = generator.generate_html(tmpdir)
            assert os.path.exists(index_path)
            assert index_path.endswith("index.html")
            files = os.listdir(tmpdir)
            assert "BaseDial.html" in files
            assert "IPlugin.html" in files
            assert "index.html" in files

    def test_generate_html_content(self, generator):
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = generator.generate_html(tmpdir)
            with open(index_path, encoding="utf-8") as f:
                content = f.read()
            assert "XTC Dial Factory SDK" in content
            assert "BaseDial" in content
            assert "IPlugin" in content

    def test_generate_markdown(self, generator):
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = generator.generate_markdown(tmpdir)
            assert os.path.exists(index_path)
            assert index_path.endswith("index.md")
            files = os.listdir(tmpdir)
            assert "BaseDial.md" in files
            assert "IPlugin.md" in files

    def test_generate_markdown_content(self, generator):
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = generator.generate_markdown(tmpdir)
            with open(index_path, encoding="utf-8") as f:
                content = f.read()
            assert "BaseDial" in content
            assert "IPlugin" in content

    def test_parse_java_with_javadoc(self, generator):
        """Test that javadoc comments are captured."""
        classes = generator.scan_stubs()
        for cls in classes:
            if cls.get("javadoc", {}).get("description"):
                assert len(cls["javadoc"]["description"]) > 0
                break
        else:
            # All stubs have javadoc on classes
            assert False, "No javadoc found on any class"

    def test_class_modifiers(self, generator):
        classes = generator.scan_stubs()
        base_dial = next(c for c in classes if c["name"] == "BaseDial")
        assert "public" in base_dial["modifiers"]

    def test_empty_stubs_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SdkDocGenerator(stubs_dir=tmpdir)
            classes = gen.scan_stubs()
            assert len(classes) == 0

    def test_generate_html_no_classes(self, tmp_path):
        gen = SdkDocGenerator(stubs_dir=str(tmp_path))
        with pytest.raises(RuntimeError, match="No classes found"):
            gen.generate_html(str(tmp_path / "out"))
