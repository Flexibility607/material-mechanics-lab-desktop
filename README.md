# 材料力学实验报告助手（Windows 桌面版）

这是网站版的 Electron + Python 桌面封装。应用可录入 7 次材料力学实验的原始数据、自动计算并生成报告，并可导出 Markdown、HTML 或调用系统打印。OpenAI 报告轻微润色功能由本机 Python 服务端读取密钥。

原始数列和矩阵可在表格中逐项增删，也可下载当前实验的 CSV 模板、批量编辑后重新导入。报告信息为空时自动采用界面中灰色显示的默认值。

生成完成后，完整实验报告会在独立窗口中打开；原始记录扫描页在报告末尾统一写为“略”。

## 下载

预编译 Windows x64 安装程序放在本仓库的 GitHub Releases 中，不提交到 Git 历史。

## 源码构建

建议环境：Windows 10/11 x64、Python 3.10+、PyInstaller、Node.js、pnpm。安装 NSIS 后可使用仓库内的原生安装脚本；未安装时构建脚本会尝试使用 electron-builder 的 NSIS 流程。

```powershell
cd .\MaterialMechanicsLab
.\build_installer.ps1
```

输出文件：`MaterialMechanicsLab/dist/MaterialMechanicsLab-Setup.exe`。

## 目录

| 路径 | 内容 |
|---|---|
| `MaterialMechanicsLab/` | Electron 主进程、预加载脚本和安装包构建脚本 |
| `material_mechanics_assistant/` | 内置网站前端与 Python 服务端 |
| `04-自动报告计算/` | 统一报告计算器和脱敏算例 |
| `03-实验报告/markdown/` | 脱敏报告参考正文 |
| `实验汇总/` | 各实验独立计算脚本、样例数据与校核结果 |

## OpenAI 配置

在应用“API 设置”中保存密钥，或在本地调试时设置 `OPENAI_API_KEY`。不要将真实密钥写入源文件或提交到 Git。

## 隐私说明

公开仓库不包含手写报告 PDF、逐页扫描图片或真实身份字段。数值算例用于验证程序计算和报告替换功能。
