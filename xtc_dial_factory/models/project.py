"""Project and configuration models for XTC Dial Factory."""

import json
import os
import uuid
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from enum import Enum, auto


class ProjectType(Enum):
    CL_DIAL = "cl_dial"            # Traditional .cl watch face
    PL_PLUGIN = "pl_plugin"        # .pl compose element plugin
    COMPOSE_DIAL = "compose_dial"  # Compose dial (multiple .pl elements)
    THEME_PACKAGE = "theme_package"  # Theme package (bundles dial + icon pack + extras)
    ICON_PACKAGE = "icon_package"    # Icon pack (custom app icons)


class ClockType(Enum):
    DEFAULT_CODE = -2
    TRADITIONAL_CL = 1
    CUSTOM_PHOTO = 6
    THEME_PACKAGE = 7
    COMPOSE_DIY = 9

    @classmethod
    def from_value(cls, v):
        for member in cls:
            if member.value == v:
                return member
        return cls.TRADITIONAL_CL


@dataclass
class DialConfig:
    """DialConfig - stored in SharedPreferences as current_dial_bean JSON."""
    sourceName: str = ""
    dialName: str = ""
    nameCompat: str = ""
    sourceId: int = 0
    clockType: int = 1
    useState: int = 1
    dialDir: str = ""
    versionCodeServer: int = 0
    versionCode: int = 1
    keyVersion: int = 0
    ipSpecial: int = 0

    def to_json(self) -> str:
        d = {k: v for k, v in asdict(self).items() if v is not None}
        return json.dumps(d, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "DialConfig":
        d = json.loads(s)
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class AssetFile:
    """An extra asset file to be deployed alongside the project (e.g. background images)."""
    local: str = ""      # Relative path in project directory (e.g. "ylp_360.png")
    remote: str = ""     # Absolute path on device (e.g. "/sdcard/xtc/dial/compose/bg.png")

    def to_dict(self) -> dict:
        return {"local": self.local, "remote": self.remote}

    @classmethod
    def from_dict(cls, d: dict) -> "AssetFile":
        return cls(local=d.get("local", ""), remote=d.get("remote", ""))


@dataclass
class PluginCommunication:
    """Inter-plugin communication configuration: one component sends a message to another."""
    source_component: str = ""
    target_component: str = ""
    action: str = ""
    data_template: str = "{}"
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "source_component": self.source_component,
            "target_component": self.target_component,
            "action": self.action,
            "data_template": self.data_template,
            "enabled": self.enabled
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PluginCommunication":
        return cls(
            source_component=d.get("source_component", ""),
            target_component=d.get("target_component", ""),
            action=d.get("action", ""),
            data_template=d.get("data_template", "{}"),
            enabled=d.get("enabled", True)
        )


@dataclass
class ThemeAssemblyElement:
    """Element in a compose dial elementList."""
    component: str = ""
    componentId: Optional[int] = None
    type: int = 1
    x: int = 0
    y: int = 0
    width: int = 100
    height: int = 100
    dpX: float = 0.0
    dpY: float = 0.0
    dpWidth: float = 50.0
    dpHeight: float = 50.0
    versionCode: int = 1
    resUrl: str = ""
    thumbnailUrl: str = ""
    extra: str = "{}"

    def to_dict(self) -> dict:
        d = {}
        for k, v in asdict(self).items():
            if v is not None:
                d[k] = v
        return d


@dataclass
class NetComposeDial:
    """Compose dial config.json structure."""
    id: int = 0
    name: str = "新组合表盘"
    diyType: int = 0
    diyVersion: int = 1
    preview: str = ""
    watchId: str = ""
    createTime: int = 0
    updateTime: Optional[int] = None
    onlyChange: bool = False
    elementList: List[ThemeAssemblyElement] = field(default_factory=list)

    def to_json(self) -> str:
        d = {"id": self.id, "name": self.name, "diyType": self.diyType,
             "diyVersion": self.diyVersion, "elementList": [e.to_dict() for e in self.elementList]}
        if self.preview:
            d["preview"] = self.preview
        if self.watchId:
            d["watchId"] = self.watchId
        if self.createTime:
            d["createTime"] = self.createTime
        return json.dumps(d, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "NetComposeDial":
        d = json.loads(s)
        elements = [ThemeAssemblyElement(**e) for e in d.get("elementList", [])]
        return cls(
            id=d.get("id", 0),
            name=d.get("name", ""),
            diyType=d.get("diyType", 0),
            diyVersion=d.get("diyVersion", 1),
            preview=d.get("preview", ""),
            watchId=d.get("watchId", ""),
            createTime=d.get("createTime", 0),
            elementList=elements
        )


@dataclass
class IconPackConfig:
    """IconConfig - stored as JSON within ThemePackConfig.mIconConfig or standalone.

    Controls how app icons are themed (size, color, conversion, resources path).
    """
    iconName: str = ""          # Display name of the icon pack
    sourceName: str = ""        # Unique identifier
    iconDp: float = 48.0        # Icon display size in dp
    nameColor: str = ""         # App name color (hex)
    convertType: int = 0        # Icon conversion type (0=none, 1=mask, etc.)
    spanConvertType: int = 0    # Span conversion type
    themePath: str = ""         # Path to icon resources on device
    originType: int = 0         # Origin icon type
    keyVersion: int = 1         # Key version

    def to_json(self) -> str:
        return json.dumps({k: v for k, v in asdict(self).items() if v is not None},
                          ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "IconPackConfig":
        d = json.loads(s) if isinstance(s, str) else s
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ThemePackConfig:
    """ThemePackConfig - config for a theme package.

    A theme package bundles a dial + icon pack + optional extras (background,
    launcher theme, charging animation, AOD, turn animation, bubbles).
    Stored as JSON in the themepackage ContentProvider 'packConfig' column.
    """
    sourceName: str = ""
    name: str = ""
    nameCompat: str = ""
    themePackDir: str = ""            # On-device dir: /sdcard/xtc/themepackage/<sourceName>/
    versionCode: int = 1
    keyVersion: int = 1
    osType: str = ""                  # OS type compatibility string

    # Bundled components (stored as JSON strings of their respective configs)
    dialConfig: str = ""              # JSON of DialConfig for the bundled dial
    mIconConfig: str = ""             # JSON of IconPackConfig for the bundled icon pack

    # Optional extras
    bgConfig: str = ""                # Background config JSON
    launcherThemeConfig: str = ""     # Launcher theme config JSON
    chargeConfig: str = ""            # Charging animation config JSON
    aodConfig: str = ""               # Always-on-display config JSON
    turnConfig: str = ""              # Turn/wake animation config JSON

    # Chat extras
    bubbleId: str = ""
    headId: str = ""
    nicknameId: str = ""

    def to_json(self) -> str:
        return json.dumps({k: v for k, v in asdict(self).items() if v is not None},
                          ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "ThemePackConfig":
        d = json.loads(s) if isinstance(s, str) else s
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class Project:
    """A project represents a dial, plugin, compose dial, theme package or icon package project."""

    def __init__(self, name: str = "", project_type: ProjectType = ProjectType.CL_DIAL,
                 package_name: str = "", author: str = ""):
        self.name = name
        self.project_type = project_type
        self.package_name = package_name or f"com.xtc.{name.lower()}" if name else ""
        self.author = author
        self.root_dir: str = ""
        self.version_code = 1
        self.version_name = "1.0.0"

        # Project specific
        self.dial_config: Optional[DialConfig] = None
        self.compose_dial: Optional[NetComposeDial] = None
        self.theme_pack_config: Optional[ThemePackConfig] = None
        self.icon_pack_config: Optional[IconPackConfig] = None
        self.plugins: List[str] = field(default_factory=list)  # List of .pl source names
        self.custom_plugins: List[str] = []  # Imported .pl source names
        self.plugin_type: int = 1  # Plugin category type (1=normal, 7=background, 11=text) for PL_PLUGIN
        self.communications: List[PluginCommunication] = []
        self.assets: List[AssetFile] = []    # Extra files to deploy (images, etc.)
        self.preview_image: str = ""          # Preview thumbnail (relative path in project dir)

        self.changelog: List[str] = []

        # Build system: "traditional" (javac → d8 → aapt → apksigner)
        # or "gradle" (runs Gradle wrapper, copies output from app/build/outputs/)
        self.build_system: str = "traditional"

        self._dirty = False
        self._project_file = ""

    @property
    def source_name(self) -> str:
        if self.project_type == ProjectType.COMPOSE_DIAL:
            return str(self.compose_dial.id) if self.compose_dial else self.name
        return self.name.lower()

    def get_dial_dir(self) -> str:
        """Get the on-device dial directory."""
        if self.project_type == ProjectType.THEME_PACKAGE:
            return f"/sdcard/xtc/themepackage/{self.source_name}/"
        return f"/sdcard/xtc/dial/{self.source_name}/"

    def get_theme_pack_dir(self) -> str:
        """Get the on-device theme package directory."""
        return f"/sdcard/xtc/themepackage/{self.source_name}/"

    def get_icon_pack_dir(self) -> str:
        """Get the on-device icon pack directory (within theme package)."""
        return f"/sdcard/xtc/themepackage/{self.source_name}/icon/"

    def get_manifest_path(self) -> str:
        return os.path.join(self.root_dir, "AndroidManifest.xml")

    def get_build_gradle_path(self) -> str:
        return os.path.join(self.root_dir, "build.gradle")

    def get_config_path(self) -> str:
        if self.project_type == ProjectType.THEME_PACKAGE:
            return os.path.join(self.root_dir, "themepack.json")
        elif self.project_type == ProjectType.ICON_PACKAGE:
            return os.path.join(self.root_dir, "icon_config.json")
        return os.path.join(self.root_dir, "config.json")

    def get_src_dir(self) -> str:
        pkg_path = self.package_name.replace(".", "/")
        return os.path.join(self.root_dir, "src", "main", "java", pkg_path)

    def get_cl_output(self) -> str:
        return os.path.join(self.root_dir, "build", "outputs", f"{self.source_name}.cl")

    def get_pl_output(self) -> str:
        return os.path.join(self.root_dir, "build", "outputs", f"{self.source_name}.pl")

    def mark_clean(self):
        self._dirty = False

    def mark_dirty(self):
        self._dirty = True

    def register_imported_plugin(self, source_name: str):
        """Register an imported .pl plugin source name."""
        if source_name not in self.custom_plugins:
            self.custom_plugins.append(source_name)
            self.mark_dirty()

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def bump_version(self, part: str):
        """Bump version_name and increment version_code.

        Args:
            part: One of "major", "minor", "patch".
        """
        try:
            parts = self.version_name.split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            major, minor, patch = 1, 0, 0

        if part == "major":
            major += 1
            minor = 0
            patch = 0
        elif part == "minor":
            minor += 1
            patch = 0
        elif part == "patch":
            patch += 1
        else:
            return

        self.version_name = f"{major}.{minor}.{patch}"
        self.version_code += 1

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "project_type": self.project_type.value,
            "package_name": self.package_name,
            "author": self.author,
            "version_code": self.version_code,
            "version_name": self.version_name,
            "root_dir": self.root_dir,
            "source_name": self.source_name,
            "changelog": list(self.changelog),
            "custom_plugins": list(self.custom_plugins),
            "plugin_type": self.plugin_type,
            "communications": [c.to_dict() for c in self.communications],
            "assets": [a.to_dict() for a in self.assets],
            "preview_image": self.preview_image,
            "build_system": self.build_system,
        }
        if self.theme_pack_config:
            d["theme_pack_config"] = json.loads(self.theme_pack_config.to_json())
        if self.icon_pack_config:
            d["icon_pack_config"] = json.loads(self.icon_pack_config.to_json())
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Project":
        p = cls(
            name=d.get("name", ""),
            project_type=ProjectType(d.get("project_type", "cl_dial")),
            package_name=d.get("package_name", ""),
            author=d.get("author", "")
        )
        p.version_code = d.get("version_code", 1)
        p.version_name = d.get("version_name", "1.0.0")
        p.root_dir = d.get("root_dir", "")
        p.changelog = list(d.get("changelog", []))
        p.custom_plugins = list(d.get("custom_plugins", []))
        p.plugin_type = d.get("plugin_type", 1)
        p.build_system = d.get("build_system", "traditional")
        p.communications = [PluginCommunication.from_dict(c) for c in d.get("communications", [])]
        p.assets = [AssetFile.from_dict(a) for a in d.get("assets", [])]
        p.preview_image = d.get("preview_image", "")
        if "theme_pack_config" in d:
            p.theme_pack_config = ThemePackConfig.from_json(d["theme_pack_config"])
        if "icon_pack_config" in d:
            p.icon_pack_config = IconPackConfig.from_json(d["icon_pack_config"])
        return p
