# P2P 语音聊天软件

一个使用 Python 构建的点对点（P2P）语音聊天应用。

## ✨ 功能特性

-   **现代化的图形用户界面**: 使用 `PySide6` 和 `PySide6-Fluent-Widgets` 构建，界面美观流畅。
-   **自由选择音频设备**: 用户可以根据需要自由选择麦克风和扬声器。
-   **支持 IPv6 / IPv4**: 底层采用 UDP 协议，同时支持 IPv6 和 IPv4 地址，并具备 IPv4 回退机制。
-   **高效的音频压缩**: 集成 `Opus` 音频编解码器，在保证音质的同时，有效降低网络带宽占用。
-   **多线程架构**: 核心的音频和网络模块运行在独立的线程中，确保 GUI 主线程不被阻塞，操作流畅无卡顿。
-   **清晰的状态显示**: 实时显示通话状态，如“空闲”、“连接中”、“通话中”等。

## 🚀 安装与设置

1.  **克隆本仓库**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **安装系统依赖**
    本项目依赖 `pyaudio`，需要先安装其对应的系统库 `portaudio`。在基于 Debian/Ubuntu 的系统上，可以使用以下命令安装：
    ```bash
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev
    ```
    为了确保 Qt 图形界面能正常运行，可能还需要安装 `xcb` 相关的库：
    ```bash
    sudo apt-get install -y libxcb-cursor0
    ```

    ### Windows 用户

    在 Windows 上，您需要手动下载并提供 `opus` 的动态链接库 (`.dll`)。

    1.  **下载 Opus 工具包**:
        -   访问 [Opus 官方下载页面](https://opus-codec.org/downloads/)。
        -   在 "Development binary builds" 或 "opus-tools" 部分，找到适用于 Windows 的二进制文件压缩包。推荐下载 64 位版本：`opus-tools-0.2-win64.zip`。
        -   [直接下载链接](https://archive.mozilla.org/pub/opus/win64/opus-tools-0.2-win64.zip)

    2.  **提取并放置 `opus.dll`**:
        -   解压下载的 `.zip` 文件。
        -   在解压后的文件夹中，找到 `opus.dll` 文件。它通常位于 `x64/` 或 `bin/` 目录下。
        -   将 `opus.dll` 文件复制到本项目的根目录下（与 `main.py` 文件放在同一个文件夹）。

3.  **创建虚拟环境并安装依赖**
    推荐使用 `uv` 来管理虚拟环境。
    ```bash
    # 创建虚拟环境
    uv venv

    # 激活虚拟环境
    source .venv/bin/activate

    # 根据 pyproject.toml 安装依赖
    uv pip install .
    ```

## 📝 使用方法

1.  **运行应用**
    ```bash
    python main.py
    ```

2.  **开始通话**
    -   在两台设备上分别运行此应用。
    -   在设备 A 的 "Peer IP/Port" 输入框中，填入设备 B 的 IP 地址和端口号（默认为 `12345`）。
    -   点击 "Call" 按钮。
    -   设备 B 将自动接听来电，双方即可开始通话。
    -   要结束通话，任意一方点击 "Hang Up" 按钮即可。

---
**开发者**: Jules
