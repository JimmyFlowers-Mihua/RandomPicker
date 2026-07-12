# 🎲 智能随机点名器 (Random Picker)

[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-blue.svg)](#)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Funder](https://img.shields.io/badge/Powered%20by-JimmyFlowers-orange.svg)](#)

一款基于 Python (Eel) + HTML5 混合架构开发的轻量级桌面端随机点名软件。软件采用精美的响应式卡片化设计，支持 Excel 名单智能提取、临时排除屏蔽、多人数联合抽取以及极致的动画视效。

本项目已针对 macOS (M1/M2/M3 Apple Silicon) 与 Windows 10/11 进行了深度的跨平台打包优化，实现单文件分发下的“秒开”级极速冷启动。

---

## 🚀 极速下载与运行提示（小白/用户通道）

### 📥 软件直接下载
如果您不想配置 Python 环境进行编译，**推荐直接下载原作者已打包好的单文件免安装版本**：

[📊 点击前往 Release 页面下载最新版 (.exe / .app)](https://github.com/JimmyFlowers-Mihua/RandomPicker/releases)

> **⚠️ macOS (苹果 M1/M2/M3 & Intel) 运行必看：**
> 1. **启动较慢（正常现象）**：由于本软件为单文件免安装版本，**macOS 系统需要在后台进行解压和安全扫描，约有 10 秒左右的延迟，这是完全正常的**，请耐心等待 10 秒即可。
> 2. **如果提示“文件损坏”或“无法打开”**：这是因为软件未进行苹果官方付费证书签名，请按照下方 [🔧 macOS 权限解锁指南](#-macos-权限解锁与损坏解决指南) 快速修复。
> 3. **MacOS下第一次打开记得给予读写权限**，软件**有可能**出现第一次打开白屏，是因为没有读写权限导致的，赋予权限后关闭窗口（或者command+Q强行关闭一次）后再次打开即可解决

---

🔧 macOS 权限解锁与损坏解决指南
由于 macOS 的安全防护机制（Gatekeeper）非常严格，对于未付费签名的开发者作品，会默认拦截并提示“已损坏”。请按照以下步骤解除限制：

1. 开启“任何来源”选项（最推荐）
打开终端：在 Mac 上打开 启动台 > 其它 > 终端。
执行解锁命令：在终端中输入以下命令并回车：

```bash

sudo spctl --master-disable

 ```

输入密码：终端会提示输入您的 Mac 开机密码（输入时屏幕上不会有任何显示，盲打输入完直接敲回车即可）。
修改系统设置：
打开 Mac 系统的 系统设置 (系统偏好设置) > 安全性与隐私 > 通用。
此时可以看到“允许从以下位置下载的 App”选项中多出了一个 “任何来源”，勾选它即可。
2. 针对单文件的隔离清除（备用方案）
如果开启“任何来源”后双击仍报错，请在终端中运行以下命令，直接清除该 App 的安全隔离属性：

```bash

xattr -cr /Applications/随机点名器.app

 ```
---

## 💡 开发者真诚的请求 (Telemetry & Data Request)

本软件在 **原作者编译分发的官方 Release 版本** 中，内置了匿名设备信息和使用打点的遥测模块（包含设备配置、操作系统、大体地理位置、软件在线/下线事件，**承诺绝对不收集任何姓名、Excel 内容等隐私数据**）。

> **🎓 致技术社区的一封信：**
> 本项目作为作者本人的 **毕业设计与求职面试支撑成果**，非常需要收集一些真实用户的匿名使用数据和装机量进行成果展示。
> * **数据承诺**：我郑重承诺，在我的官方编译版本下收集到的所有数据**永远不会用于广告、画像等任何形式的商业用途或牟利,永远不会包含任何私人信息**。
> * **版本请求**：如果您觉得这个软件对您有帮助，**恳请您尽可能直接使用我官方 Release 页面分发的编译版本**。其他人自行下载源码重新打包分发的版本，由于没有我的安全密钥，无法参与数据贡献，且其安全性作者无法保证。
> 
> 感谢每一位为大学生毕业设计和求职助力点灯的老师与开发者！

---

## ✨ 核心亮点与技术特性

### 🎨 极简、唯美的 UI/UX 交互
* **响应式卡片设计**：采用现代毛玻璃质感与梦幻渐变背景，完美自适应各种分辨率屏幕。
* **名字气泡动态自适应**：支持单人霸屏显示，多人数抽取时自动转化为“胶囊气泡”横向网格排版，且字体根据抽取人数自动等比收缩，绝不遮挡或溢出屏幕。
* **物理级五彩纸屑特效**：抽取成功时触发丝滑的重力级 Canvas-Confetti 动画，拉满课堂/会议仪式感。

### ⚙️ 强劲、实用的后台控制
* **智能 Excel 解析**：支持标准 .xlsx 和 .xls 名单文件拖入，算法自动在表格前 20 行中检索“姓名”表头并提取名册，免去用户手动整理格式的烦恼。
* **沙盒沙盘机制**：自动在用户本机的“文档（Documents）”目录下创建专有安全数据库沙盒，不污染系统环境。
* **名单隔离与管理**：支持多个班级/会议名单自由切换，一键安全清空或删除。
* **临时排除功能**：在后台可以勾选特定人员，使其不参与本次抽取（如请假学生），勾选即时生效。

### 🚀 极致的性能优化
* **多线程异步预加载**：针对庞大的 Pandas 重型计算库引入了后台异步预加载机制。双击软件瞬间开屏，不卡顿前台网页渲染，等用户准备导入 Excel 时，后台早已加载完毕，兼顾“秒开”与“秒导入”。
* **网络与下线打点解耦**：隐藏式遥测模块全面采用 threading.Thread 异步后台托管，即使在无网、延迟极高的网络环境下，也绝不阻塞前台 UI 的关闭与退出。

---

## 🛠️ 项目文件结构

```text
RandomPicker/
├── web/                    # 前端资源文件夹
│   └── index.html          # 前端主页面 (HTML/CSS/JS)
├── main.py                 # Python 核心服务及启动入口
├── logo.icns               # macOS 应用程序图标
└── logo.ico                # Windows 应用程序图标

---

```
## 💻 开发者运行与本地编译指南

在开始前，请克隆本项目并进入根目录：

```bash

git clone https://github.com/JimmyFlowers-Mihua/RandomPicker.git
cd RandomPicker

```


### 1. 依赖环境安装
建议在虚拟环境或全局环境下执行以下安装（包含打包工具）：

```bash

pip install eel pandas jinja2 openpyxl xlrd requests appdirs pyinstaller

```

### 2. 开发者脱敏说明
在分发或编译前，如果你需要配置自己的遥测服务端，请修改 main.py 顶部的以下变量：

```python

# 将其修改为你自己的 Webhook 地址和校验密钥

NAS_WEBHOOK_URL = "https://your-api-domain.com/api/telemetry"
TELEMETRY_API_KEY = "your_sk_live_xxxxxxxxx"

```

---

## 📦 跨平台单文件打包 (Release Build)

本项目已经过精细的打包体积与兼容性调整，彻底解决了 setuptools 引起的 InvalidVersion 崩溃 Bug。

### 🍎 macOS 端打包
在 Mac 的终端中，单行运行以下命令。它会自动完成打包、提权并解除 macOS 对未签名独立 App 的沙盒安全隔离限制：

```bash

python3 -m PyInstaller --clean --windowed --onefile --add-data "web:web" --hidden-import=appdirs --hidden-import=xlrd --hidden-import=openpyxl --exclude-module pkg_resources --exclude-module unittest -n "随机点名器" -i "logo.icns" main.py && chmod -R 755 dist/随机点名器.app && xattr -cr dist/随机点名器.app

```

### 🔌 Windows 端打包
在 Windows 的 CMD 或 PowerShell 中运行以下命令进行打包（注意路径分隔符为分号 ;）：

```cmd

python -m PyInstaller --clean --windowed --onefile --add-data "web;web" --hidden-import=appdirs --hidden-import=xlrd --hidden-import=openpyxl --exclude-module pkg_resources -n "随机点名器" -i "logo.ico" main.py

 ```

打包完成后，在 dist 目录下会生成一个独立的 随机点名器.exe，直接双击运行即可。

---

⚖️ 开源许可协议 & 商业限制声明 (License)

本项目代码在 GPL v3.0 (GNU General Public License v3) 协议下开源，并附加以下双重许可与商业行为限制条款：

1. 强制开源传染 (GPL v3.0)
任何个人或团队在分发、修改或基于本项目进行二次开发时，衍生作品必须同样以 GPL v3.0 协议完全开源，严禁闭源。

2. 严禁未经授权的商业行为 (Commercial Use Restriction)
严禁闭源牟利：任何个人、团队或商业机构，不得在未经原作者（JimmyFlowers）书面授权的情况下，将本项目代码或编译后的程序进行直接售卖、倒卖或闭源打包商业化。

严禁未授权集成：本软件及其任何代码片段，不得作为收费系统的内置模块使用。

必须保留署名：任何分发 and 修改版本中，必须在显著位置保留原作者 JimmyFlowers 的署名及本项目 GitHub 源代码仓库链接。

💡 商业授权获取：
如果您需要在企业内部闭源部署使用、将本项目用于商业盈利性培训、或进行任何不适用 GPL v3.0 开源传染限制的商业集成，请主动联系原作者 JimmyFlowers 协商购买商业许可证书。

---

Created with ❤️ by JimmyFlowers  
如果您觉得这个项目帮到了您，欢迎在 GitHub 上点一个 ⭐ Star！如有任何问题或功能建议，欢迎提交 Issue。
