# AI Desktop Pet - 飞行雪绒

一个基于 AI 的智能桌面宠物应用，具备角色人格、语音交互、日程管理等功能。

## 功能特点

- **AI 对话**：接入 mimo-v2.5 推理模型，支持多轮有记忆的对话
- **角色人设**：精心设计的角色背景（爱弥斯/飞行雪绒），保持角色一致性
- **语音交互**：集成 GPT-SoVITS 声线克隆，输出角色专属语音
- **自主行为**：待机时随机飞行、播放训练语句，展现角色个性
- **日程提醒**：支持设置提醒，到期时语音播报

## 项目结构

```
desktop_pet/
├── main.py              # 程序入口
├── pet_window.py        # 桌宠主窗口
├── pet_sprite.py        # 角色精灵与状态机
├── dialogue.py          # 对话系统与语音合成
├── reminder.py          # 日程提醒功能
├── config.py            # 配置管理
├── assets/
│   └── ams.gif          # 角色动画
└── requirements.txt     # 依赖
```

## 环境要求

- Python 3.9+
- Windows 10/11

## 安装

```bash
pip install -r requirements.txt
```

## 配置

### 环境变量

```bash
# mimo-v2.5 API Key（必需）
set MIMO_API_KEY=your_api_key_here

# GPT-SoVITS 配置（可选，用于语音功能）
set GPT_SOVITS_API=http://127.0.0.1:9880/tts
set GPT_SOVITS_LOGS_DIR=path/to/your/GPT-SoVITS/logs
set GPT_SOVITS_REF_TEXT=参考音频的文本内容
```

### 启动 GPT-SoVITS（可选）

如果需要语音功能，需要先启动 GPT-SoVITS API：

```bash
cd /d E:\path\to\GPT-SoVITS
py -3.9 api_v2.py
```

## 运行

```bash
python main.py
```

或双击 `桌宠.vbs`（无命令行窗口）。

## 使用说明

- **左键拖拽**：移动桌宠位置
- **左键点击**：触发互动反应
- **右键点击**：打开菜单
  - 对话：打开聊天输入框
  - 设置提醒：添加日程提醒
  - 待机语音开关：开启/关闭待机时的语音播放
  - 大小：调整桌宠尺寸
  - 退出：关闭程序

## 致谢

本项目使用了以下开源项目：

- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS/tree/main/GPT_SoVITS) - 基于 GPT 的少样本语音克隆框架，用于实现角色专属语音合成。感谢 [RVC-Boss](https://github.com/RVC-Boss) 提供的优秀开源项目。

## 技术栈

- PyQt5：桌面 GUI 框架
- Pillow：图像处理
- pygame：音频播放
- mimo-v2.5：AI 对话模型
- GPT-SoVITS-v2Pro：语音克隆模型

## License

MIT License
