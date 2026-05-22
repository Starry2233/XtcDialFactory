XTC Dial Factory - 模板目录
================================

该目录存放表盘和组件插件的项目模板。

目录结构
--------
每个模板是一个独立的子目录，包含以下文件：

  template.json        - 模板元数据（名称、类型、描述、版本、作者）
  config.json          - （可选）表盘配置文件
  AndroidManifest.xml  - （可选）Android 清单文件
  src/                 - （可选）Java 源码目录
  build.gradle         - （可选）Gradle 构建脚本

template.json 格式：
{
    "name": "模板名称",
    "type": "cl_dial | pl_plugin | compose_dial",
    "description": "模板描述",
    "version": "1.0",
    "author": "作者"
}

导出模板
--------
在模板市场对话框中选择"导出"按钮，可将当前项目打包为 .xtc-template
文件（ZIP 格式），包含 template.json、config.json、AndroidManifest.xml、
src/ 目录等关键文件。

导入模板
--------
在模板市场对话框中选择"导入"按钮，选择 .xtc-template 文件即可将其
解压到本目录。

发布模板
--------
将 .xtc-template 文件分享给其他开发者，对方可通过"导入"功能使用。
