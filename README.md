# XTC Dial Factory

A visual development environment for creating custom watch faces and widget plugins for **XTC smartwatches** (小天才电话手表).

## Features

- **Project Wizard** — Create new dial projects (.cl traditional dials / .pl component plugins / compose dials)
- **Visual Editor** — Drag-and-drop canvas with QGraphicsView, component palettes, alignment guides, and real-time clock preview
- **Compose Dial Designer** — Layer multiple plugin components, adjust Z-order, configure inter-component communication
- **Gradle Build Integration** — Compile Java → DEX → APK → sign → deploy, all from the UI
- **One-click Device Deploy** — ADB push + Frida injection to activate dials on device
- **Plugin SDK Docs** — Auto-generated HTML/Markdown documentation from Java stub files
- **Template Marketplace** — Import/export .xtc-template packages, browse local templates
- **Device Tools** — Logcat viewer with syntax highlighting, screen capture utility
- **i18n Support** — Chinese/English UI with JSON translation files

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Requirements

- Python 3.11+
- PySide6
- Android SDK (build-tools, platform SDK 34) — for compilation
- JDK 8+ — for Java compilation
- ADB & Frida — for device deployment

## Project Structure

```
XtcDialFactory/
├── main.py                  # Entry point
├── xtc_dial_factory/        # Core package
│   ├── app.py               # Application & settings
│   ├── models/              # Data models
│   ├── views/               # UI (main window, editor, dialogs)
│   ├── build/               # Build & deploy pipeline
│   └── widgets/             # Custom Qt widgets
├── resources/               # Icons & Java stubs
├── templates/               # Project templates
├── locales/                 # i18n translation files
└── tests/                   # Test suite
```

## Build Pipeline

```
Java source → javac (1.8) → .class → d8 → classes.dex
                                    → aapt package → unsigned.apk
                                    → apksigner → signed .cl / .pl
```

## License

MIT
