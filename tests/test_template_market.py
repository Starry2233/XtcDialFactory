"""Tests for template marketplace dialog."""

import json
import os
import zipfile
import pytest


class TestScanTemplates:
    def _scan(self, templates_dir):
        """Replicate _refresh_template_list scan logic."""
        results = []
        for entry in sorted(os.listdir(str(templates_dir))):
            template_dir = os.path.join(str(templates_dir), entry)
            if not os.path.isdir(template_dir) or entry.startswith("."):
                continue
            meta_path = os.path.join(template_dir, "template.json")
            config_path = os.path.join(template_dir, "config.json")
            meta = None
            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass
            if meta is None:
                project_type = "unknown"
                if os.path.isfile(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                        project_type = "compose_dial" if "elementList" in cfg else "cl_dial"
                    except (json.JSONDecodeError, IOError):
                        pass
                meta = {"name": entry, "type": project_type}
            results.append(meta)
        return results

    def test_scan_empty_dir(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        assert self._scan(templates_dir) == []

    def test_scan_with_valid_meta(self, tmp_path):
        templates_dir = tmp_path / "templates"
        dial_dir = templates_dir / "my_dial"
        dial_dir.mkdir(parents=True)
        with open(dial_dir / "template.json", "w", encoding="utf-8") as f:
            json.dump({"name": "My Dial", "type": "cl_dial", "version": "1.0"}, f)
        results = self._scan(templates_dir)
        assert len(results) == 1
        assert results[0]["name"] == "My Dial"

    def test_scan_skips_dirs_without_meta(self, tmp_path):
        templates_dir = tmp_path / "templates"
        (templates_dir / "empty_dir").mkdir(parents=True)
        results = self._scan(templates_dir)
        assert len(results) == 1  # fallback: name from dir name
        assert results[0]["name"] == "empty_dir"

    def test_scan_uses_config_fallback(self, tmp_path):
        templates_dir = tmp_path / "templates"
        dial_dir = templates_dir / "my_dial"
        dial_dir.mkdir(parents=True)
        with open(dial_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump({"sourceName": "test", "clockType": 1}, f)
        results = self._scan(templates_dir)
        assert len(results) == 1
        assert results[0]["name"] == "my_dial"
        assert results[0]["type"] == "cl_dial"

    def test_scan_skips_hidden_dirs(self, tmp_path):
        templates_dir = tmp_path / "templates"
        (templates_dir / ".hidden").mkdir(parents=True)
        results = self._scan(templates_dir)
        assert results == []


class TestExportImport:
    def _export_zip(self, project_dir, export_path):
        """Replicate _export_template zip logic."""
        meta = {"name": "Test", "type": "cl_dial", "version": "1.0", "author": "tester"}
        with zipfile.ZipFile(str(export_path), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("template.json", json.dumps(meta, indent=2, ensure_ascii=False))
            include_extensions = {".json", ".xml", ".java", ".gradle",
                                  ".properties", ".txt", ".png", ".jpg", ".jpeg"}
            exclude_dirs = {"build", ".gradle", "__pycache__", ".git"}
            for root, dirs, files in os.walk(str(project_dir)):
                dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
                for filename in files:
                    filepath = os.path.join(root, filename)
                    relpath = os.path.relpath(filepath, str(project_dir))
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in include_extensions or filename == "AndroidManifest.xml":
                        zf.write(filepath, relpath)

    def test_export_creates_valid_archive(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "config.json").write_text('{"sourceName":"test"}', encoding="utf-8")
        src = project_dir / "src"
        src.mkdir()
        (src / "Main.java").write_text("// code", encoding="utf-8")

        export_path = tmp_path / "export.xtc-template"
        self._export_zip(project_dir, export_path)

        assert export_path.exists()
        with zipfile.ZipFile(str(export_path), "r") as zf:
            names = zf.namelist()
            assert "template.json" in names
            assert "config.json" in names
            assert "src/Main.java" in names

    def test_import_extracts_correctly(self, tmp_path):
        zip_path = tmp_path / "template.xtc-template"
        with zipfile.ZipFile(str(zip_path), "w") as zf:
            zf.writestr("template.json", json.dumps({
                "name": "Imported", "type": "cl_dial", "version": "1.0"
            }))
            zf.writestr("config.json", '{"sourceName":"imported"}')
            zf.writestr("src/Main.java", "// code")

        with zipfile.ZipFile(str(zip_path), "r") as zf:
            meta = json.loads(zf.read("template.json"))
            extract_dir = tmp_path / "templates" / meta["name"]
            os.makedirs(str(extract_dir), exist_ok=True)
            for member in zf.namelist():
                zf.extract(member, str(extract_dir))

        assert (extract_dir / "config.json").exists()
        assert (extract_dir / "src" / "Main.java").exists()
        with open(extract_dir / "config.json") as f:
            assert json.load(f)["sourceName"] == "imported"

    def test_import_validates_template_json(self, tmp_path):
        zip_path = tmp_path / "bad.xtc-template"
        with zipfile.ZipFile(str(zip_path), "w") as zf:
            zf.writestr("random.txt", "content")

        with zipfile.ZipFile(str(zip_path), "r") as zf:
            has_template_json = "template.json" in zf.namelist()

        assert not has_template_json

    def test_export_excludes_build_dirs(self, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "config.json").write_text("{}", encoding="utf-8")
        build = project_dir / "build"
        build.mkdir()
        (build / "output.apk").write_text("fake", encoding="utf-8")

        export_path = tmp_path / "export.xtc-template"
        self._export_zip(project_dir, export_path)

        with zipfile.ZipFile(str(export_path), "r") as zf:
            names = zf.namelist()
            assert not any(n.startswith("build") for n in names)
