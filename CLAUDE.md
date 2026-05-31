# XTC Dial Factory — 表盘工厂

> **IDE 级别工程** — 为小天才电话手表构建自定义表盘和桌面组件的可视化开发环境。
>
> 本文件作为项目总纲，包含：TODO 列表、XTC 内部实现原理、反编译源码位置指引。
> **任何 AI 接手前请先阅读此文件。**

---

## 一、快速开始

```bash
pip install -r requirements.txt
python main.py
```

---

## 二、核心原则

1. **项目可维护性最重要** — 任何代码修改应以可维护性为第一优先级，优先选择简单清晰的设计而非取巧的方案
2. **不要加冗余注释** — 代码应自文档化。不添加说明显而易见功能的注释，不保留注释掉的代码。注释仅用于解释**为什么**这么做，而非**做了什么**

---

## 三、项目 TODO（按优先级）

### P0 — 核心功能（必须稳定）

- [x] **新建表盘项目向导** — 选择项目类型（.cl 传统表盘 / .pl 组件插件 / 组合表盘），填写包名、名称、作者
- [x] **Gradle 编译集成** — 调用 Gradle wrapper 编译 Java 源码 → d8 转 DEX → aapt 打包 APK → apksigner 签名
- [x] **设备部署** — adb push 到设备对应目录，Frida 写入 SharedPreferences 激活，System.exit 重启 Launcher
- [x] **配置编辑器** — 可视化编辑 config.json（sourceName、clockType、useState、dialDir 等字段）
- [x] **项目管理** — 打开/保存/最近项目列表

### P1 — 可视化编辑器

- [x] **画布渲染** — QGraphicsView + QGraphicsScene，模拟 360×360 圆形表盘
- [x] **组件拖放** — 从组件面板拖入画布，支持位置/大小调整（含 palette drag → canvas drop）
- [x] **对齐辅助** — 网格吸附（5px）、居中、边缘对齐
- [x] **组件属性面板** — 选中组件后编辑 x, y, width, height, type, extra 等属性
- [x] **实时预览** — QTimer 驱动时钟走动、日期更新

### P2 — 组合表盘

- [x] **组合表盘编辑** — 添加/删除/排序多个组件元素
- [x] **层级管理** — Z-order 调整（置顶/置底/上移/下移，Ctrl+Shift+↑↓ 快捷键）
- [x] **预置组件库** — 时间、日期、电池、步数、天气、电量环形、消息通知等标准组件
- [x] **自定义组件导入** — 导入 .pl 文件，解析 AndroidManifest.xml 提取元数据，添加到画布
- [x] **组件间通信** — sendMessage/registerCallback 可视化配置（源/目标/action/数据模板）

### P3 — 高级功能

- [x] **Frida 一键部署** — 内置 Frida 脚本注入激活（集成在 deploy.py 中）
- [x] **日志查看器** — QProcess adb logcat + QSyntaxHighlighter 过滤高亮（10,000 行缓冲区）
- [x] **设备屏幕截图** — QProcess adb exec-out screencap -p，3s 自动刷新，保存到本地
- [x] **模板市场** — 导入/导出 .xtc-template zip，本地模板浏览，应用到项目
- [x] **国际化** — JSON 翻译文件（zh_CN/en_US），I18n 单例，语言切换设置

### P4 — 工程化

- [x] **错误报告** — sys.excepthook 拦截，crash_logs/ 文件存储，QMessageBox 显示详情
- [x] **版本管理** — 版本号递增（major/minor/patch），更新日志，versionCode 自动+1
- [x] **插件 SDK 文档生成** — Java 桩代码解析器，HTML/Markdown 双格式导出，QTextBrowser 预览
- [x] **自动测试** — 106 单元测试覆盖 models/builder/deploy/app/i18n/error_reporter/sdk_docs/template_market

---

## 三、小天才表盘系统内部实现

### 3.1 表盘类型（clockType）

| 类型值 | 名称 | 说明 |
|--------|------|------|
| `-2` | 默认代码表盘 | 硬编码在 Launcher 中的默认表盘（如 I20_default_0） |
| `1` | 传统 CL 表盘 | `.cl` 文件（APK 变体），通过 DexClassLoader 加载 `DialViewImpl` |
| `6` | 自定义照片表盘 | 用户照片制作的表盘 |
| `7` | 主题包表盘 | 从主题包（theme package）中加载的 .cl 文件 |
| `9` | 组合/DIY 表盘 | 组合多个 .pl 插件的表盘，从 config.json 定义 |
| `10` | 新类型 | 未知（如 yjck 表盘） |

### 3.2 文件系统路径

```
# 传统 CL 表盘
/sdcard/xtc/dial/<sourceName>/
├── <sourceName>.cl          # 签名 APK (重命名为 .cl)
├── config.json               # 表盘配置
├── preview_launcher.png      # Launcher 预览图
├── preview_main.png          # 主预览图
└── oat/                      # 预编译 oat 文件

# 组合表盘
/sdcard/xtc/dial/compose/
├── custom_dial/<id>/
│   ├── config.json           # NetComposeDial JSON
│   └── compose_dial_*.jpg    # 预览图
└── element/<component>/<version>/
    └── <component>.pl        # 签名 APK (重命名为 .pl)

# 主题包（CL 表盘也可以来自主题包）
/sdcard/xtc/themepackage/<theme>/dial/
├── <name>.cl
├── config.json
├── preview_launcher.png
└── preview_main.png
```

### 3.3 关键代码路径

#### 反编译源码位置
所有框架源码在：`E:\xtcservices\decompiled\sources\`
Launcher 源码在：`E:\xtcservices\decompiled\i3launcher\sources\`

#### 框架侧（system_server 中的服务）

| 类 | 路径 | 功能 |
|----|------|------|
| `com.xtc.utils.storage.SharedManager` | sources/ | SharedPreferences 封装 |
| `com.xtc.utils.encode.JSONUtil` | sources/ | JSON 序列化/反序列化 |

#### Launcher 侧（com.xtc.i3launcher）

| 类 | 路径 | 功能 |
|----|------|------|
| `bkp.java` (DialStoreResolver) | i3launcher/sources/kotlinx/coroutines/sync/bkp.java | 查询 dialstore ContentProvider，构建表盘列表 |
| `bko.java` (ClockResourceManager) | i3launcher/sources/kotlinx/coroutines/sync/bko.java | getCurrentDial, getDefaultDial, startThemeUpdate |
| `bkx.java` (PreviewPresenter) | i3launcher/sources/kotlinx/coroutines/sync/bkx.java | 预览列表 Presenter |
| `blj.java` (PreviewDataUseCase) | i3launcher/sources/kotlinx/coroutines/sync/blj.java | 组合处理传统表盘、组合表盘、主题包 |
| `bkj.java` (ComposeUtils) | i3launcher/sources/kotlinx/coroutines/sync/bkj.java | 读写组合表盘 config.json |
| `bkh.java` (ComposeDialLoader) | i3launcher/sources/kotlinx/coroutines/sync/bkh.java | 加载组合表盘 |
| `bki.java` (ComposePluginLoader) | i3launcher/sources/kotlinx/coroutines/sync/bki.java | 加载 .pl 插件 |
| `bkg.java` (ComposeClassLoader) | i3launcher/sources/kotlinx/coroutines/sync/bkg.java | 插件 ClassLoader |
| `enw.java` | i3launcher/sources/kotlinx/coroutines/sync/enw.java | 读写 current_dial_bean SP |
| `emb.java` (AIDialHelper) | i3launcher/sources/kotlinx/coroutines/sync/emb.java | AI 表盘功能 |
| `fac.java` | i3launcher/sources/kotlinx/coroutines/sync/fac.java | 读取 .cl 文件配置 |
| `fah.java` | i3launcher/sources/kotlinx/coroutines/sync/fah.java | 创建 DexClassLoader |
| `NetComposeDial.java` | i3launcher/sources/com/xtc/clockwidget/compose/bean/NetComposeDial.java | 组合表盘 JSON 模型 |
| `DialConfig.java` | 引用 com.xtc.themelib.common.dial.DialConfig | 表盘配置模型 |
| `DialPreviewData.java` | i3launcher/sources/com/xtc/clockwidget/module/data/DialPreviewData.java | 预览列表项 |
| `PreviewAdapter.java` | i3launcher/sources/com/xtc/clockwidget/adapter/PreviewAdapter.java | 预览列表适配器 |

### 3.4 ContentProvider: dialstore

**URI:** `content://com.xtc.theme.dialstore.provider`
**数据库:** `/data/data/com.xtc.theme/databases/dial_store.db`
**表:** `dial`

**查询条件:** `useTime <> 0 AND isDelete <> 1` ORDER BY `useTime DESC`

关键列：
```
sourceName        VARCHAR  — 标识符（传统表盘用名称，组合表盘用数字 ID）
name              VARCHAR  — 显示名称
type              INTEGER  — clockType (1=传统, 7=主题, 9=组合)
useState          INTEGER  — 1=使用中, 2=可用, 4=未使用
useTime           BIGINT   — 最后使用时间戳（用于排序）
dialId            INTEGER  — 表盘 ID
sortId            INTEGER  — 排序 ID
isDelete          INTEGER  — 0=未删除
category          INTEGER  — 0=普通, 2=照片
versionCode       INTEGER  — 版本号
preset            INTEGER  — 是否预置
```

**UNIQUE 约束:** `(dialId, sortId, sourceName)`

**特殊 URI 路径:**
- `/update_using` — 更新使用状态（upsert）
- `/resource_status` — 查询资源就绪状态（返回 `"1"` 表示就绪）
- `com.xtc.theme.action.dial_exceed` — Call 方法检查表盘数量上限

### 3.5 SharedPreferences / MMKV

**SP Key: `current_dial_bean`**
值: DialConfig 的 JSON 序列化
```json
{"sourceName":"xtcwatch","clockType":1,"useState":1,"dialDir":"/sdcard/xtc/dial/xtcwatch/","versionCode":1,"keyVersion":1}
```

**SP Key: `current_use_dial`**（旧版兼容）
值: sourceName 字符串（如 `"xtcwatch"`）

**MMKV Key: `key_current_changing_dial_data`**
值: 切换中的 DialConfig 数据

**读取流程** (enw.m22810a / bko.m10123c):
1. 读 `current_dial_bean` → 解析 JSON → 返回 DialConfig
2. 如果为空 → 读 `current_use_dial` → 查数据库找到完整配置
3. 如果都为空 → 返回默认表盘（I20_default_X）

**写入流程** (enw.m22812a / bko.m10118a):
1. 序列化 DialConfig 为 JSON
2. 写入 `current_dial_bean`
3. 调用 `sm.sync()` 同步
4. 同时更新 dialstore 的 useState 和 useTime

### 3.6 编译链（关键，必须稳定）

```
Java 源码 → javac (source/target 8) → .class
.class → d8 (d8.bat) → classes.dex
classes.dex + AndroidManifest.xml → aapt → unsigned.apk
unsigned.apk → apksigner → signed.apk
signed.apk → rename to .cl or .pl
```

**注意事项（Windows）：**
- `d8.bat --classpath` 不支持通配符 `*`，必须使用 `Get-ChildItem -Recurse` 枚举 `.class` 文件
- `aapt package -F` 指定输出路径时，Manifest 必须在当前目录或使用绝对路径（推荐复制到输出目录）
- `apksigner` 要用 `.bat` 包装器，不能用 `java -jar apksigner.jar`
- 所有路径中不能有空格
- Git Bash 会将 `/sdcard` 转换为本地 Windows 路径，必须用 PowerShell

**签名配置：**
在应用设置中配置 keystore 路径、密码和别名。

### 3.7 .cl 传统表盘接口

```java
package com.xtc.<name>;

public class DialViewImpl {
    // Launcher 调用此方法获取表盘 View
    public static BaseDial getDialView(Context context, String sourceName) {
        return new MyDialView(context);
    }
}
```

`BaseDial` 继承 `RelativeLayout`，关键方法：
- 渲染时钟、背景等
- 不需要特定生命周期回调

可选类 `PowerSaveDialViewImpl`（省电模式，缺失不影响正常显示）：
```java
package com.xtc.<name>;
// 省电模式的低功耗渲染实现
```

### 3.8 .pl 组件插件接口

```java
package com.xtc.<component>;

public class Plugin implements IPlugin {
    @Override
    public String getSourceName() { return "<component>"; }
    
    @Override
    public View getView(Context context, int width, int height, String extra) {
        // 返回组件 View
    }
    
    @Override
    public void initPlugin(Context context, IMessageCallback callback) {}
    
    @Override
    public void registerCallback(IMessageCallback callback) {}
    
    @Override
    public void sendMessage(String action, Object data) {}
}
```

**插件类型（type 字段）：**
| type | 说明 |
|------|------|
| 1 | 普通组件（如时间、日期、电池、自定义） |
| 7 | 背景组件（全屏背景，GIF 或图片） |
| 11 | 文本组件（self_text，可自定义文字） |

**组件路径：** `/sdcard/xtc/dial/compose/element/<component>/<versionCode>/<component>.pl`

### 3.9 组合表盘 config.json 结构（NetComposeDial）

```json
{
  "id": 1,
  "name": "示例组合表盘",
  "diyType": 0,
  "diyVersion": 1,
  "preview": "compose_dial_xxx.jpg",
  "watchId": "d515b5e73cac449684199baab895f34b32381163",
  "createTime": 1763164068000,
  "elementList": [
    {
      "component": "time_no_6",
      "componentId": 916,
      "type": 1,
      "x": 56,
      "y": 3,
      "width": 180,
      "height": 86,
      "dpX": 28.0,
      "dpY": 1.5,
      "dpWidth": 90.0,
      "dpHeight": 43.0,
      "versionCode": 10,
      "resUrl": "http://...time_no_6.pl",
      "thumbnailUrl": "http://...preview.png",
      "extra": "{\"previewStyle\":5,\"runMode\":2}"
    }
  ]
}
```

### 3.10 Launcher 关键流程

**表盘列表构建** (blj.m10284a → PreviewDataUseCase):
1. `bkp.m10133a()` 查询 dialstore ContentProvider → 获取最近使用的表盘列表
2. `m10282b()` 处理自定义照片表盘（clockType=6）
3. `m10280a()` 处理组合表盘（clockType=9）：
   - 如果 composeDialSwitch 关闭 → 只保留 useState=1 的组合表盘
   - 如果 composeDialSwitch 打开 → 调用 `bkj.m10031a()` 读取 config.json 验证每个组合表盘
   - 验证失败（config 不存在或 JSON 解析失败）→ 从列表中移除
4. 合并列表，按 useTime 排序，最多 8 项

**表盘切换流程** (bkx.mo10144a):
1. 用户长按打开预览列表
2. 点击选择表盘
3. `bjw.m9965a()` 检查表盘是否存在（checkSourceExist）
4. `enx.m22815a().m22818a()` 发送切换 Intent
5. `ClockStatusPresenter` 接收 Intent → 调用 loadDial
6. 如果是组合表盘 → ComposeDialLoader 加载 config.json → ComposePluginLoader 加载每个 .pl 插件
7. 如果是传统表盘 → PluginLoader 加载 .cl 文件 → DexClassLoader → DialViewImpl.getDialView()
8. 完成 → 广播 `onChangeDialComplete`

---

## 四、项目架构说明

### 4.1 目录结构

```
E:\XtcDialFactory/
├── CLAUDE.md                   # 本文件
├── main.py                     # 入口
├── requirements.txt            # 依赖
├── xtc_dial_factory/           # 核心包
│   ├── app.py                  # 应用初始化
│   ├── models/                 # 数据模型
│   ├── views/                  # UI 视图
│   ├── build/                  # 编译部署
│   └── widgets/                # 自定义组件
├── templates/                  # 项目模板
│   ├── cl_dial/                # 传统表盘模板
│   ├── pl_plugin/              # 插件模板
│   └── compose_dial/           # 组合表盘模板
├── resources/                  # 资源文件
│   ├── icons/
│   └── stubs/                  # 编译用桩代码
└── docs/
```

### 4.2 技术栈

- **前端:** PySide6 (Qt6 for Python)
- **可视化:** QGraphicsView + QGraphicsScene
- **构建:** Gradle wrapper / d8 + aapt + apksigner
- **部署:** adb + Frida
- **配置:** JSON (内置编辑器)

### 4.3 反编译源码引用指南

当需要参考 XTC 实现时：
1. **框架服务:** `E:\xtcservices\decompiled\sources\com\android\server\xtc*`
2. **Launcher:** `E:\xtcservices\decompiled\i3launcher\sources\kotlinx\coroutines\sync\`
3. **表盘模型:** `E:\xtcservices\decompiled\i3launcher\sources\com\xtc\clockwidget\`
4. **日志标签:** 所有 DialTag 开头的 TAG 对应 obfuscated 类名

---

## 五、部署验证流程

```bash
# 1. 编译
cd <project_dir>
./gradlew assembleRelease

# 2. Push 到设备（传统 .cl 表盘）
adb push build/outputs/xtcwatch.cl /sdcard/xtc/dial/xtcwatch/
adb push config.json /sdcard/xtc/dial/xtcwatch/

# 3. Push 到设备（组合表盘 .pl 插件）
adb push build/outputs/myplugin.pl /sdcard/xtc/dial/compose/element/myplugin/1/

# 4. 组合表盘 config
adb push compose_config.json /sdcard/xtc/dial/compose/custom_dial/1/config.json

# 5. Frida 激活
frida -U -n com.xtc.i3launcher -e '
Java.perform(function(){
    var sm = Java.use("com.xtc.utils.storage.SharedManager").getInstance(
        Java.use("android.app.ActivityThread").currentApplication().getApplicationContext());
    sm.saveString("current_dial_bean", JSON.stringify(dialConfig));
    sm.sync();
    Java.use("java.lang.System").exit(0);
});'

# 6. 查看日志
adb logcat -d | grep -E "DialTag|PluginLoader|ComposeDial"
```

---

## 六、已知问题

1. **Gradle 在 Windows 上的兼容性** — 使用 Gradle wrapper 时注意路径分隔符
2. **d8 --classpath 通配符** — Windows 上必须枚举文件，不能使用 `*`
3. **Git Bash 路径转换** — `/sdcard` 会被转换为 Windows 路径，用 PowerShell 或 `//sdcard`
4. **Java 版本** — 必须使用 Java 8 源码兼容（source/target 8），JDK 8 或 JDK 11+
5. **Frida 编码** — 中文字符在终端中可能被转义，使用 Unicode 转义序列
6. **ContentProvider insert 权限** — dialstore 的 insert 需要从主题 app 进程执行，launcher 只能 update

---

## 七、参考资源

- 反编译框架源码: `E:\xtcservices\decompiled\sources\`
- Launcher 源码: `E:\xtcservices\decompiled\i3launcher\sources\`
- 示例项目: `C:\Users\Administrator\.doge\xtc-dial-factory\samples\`
- 构建脚本: `build.ps1`, `build.sh`
- 设备: Z8A (Android O API 27)
- ADB: 已配置
- Frida: 已安装 17.9.1

---

## 八、测试

```bash
.venv/Scripts/python -m pytest tests/ -v
```

测试覆盖：
| 模块 | 文件 | 测试数 |
|------|------|--------|
| models | `test_models.py` | 20 |
| builder | `test_builder.py` | 10 |
| deploy | `test_deploy.py` | 12 |
| app | `test_app.py` | 9 |
| **总计** | | **60** |

测试原则：
- models 测试纯数据逻辑（序列化/反序列化/业务规则）
- builder/deploy 测试路径生成、错误处理、边界条件
- 外部命令（javac/adb/frida）使用 mock，不依赖真实环境
- conftest.py 提供共享 fixtures（sample_cl_project, sample_compose_project 等）
