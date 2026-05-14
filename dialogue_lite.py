import random
import json
import os
import sys
import time
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QGraphicsDropShadowEffect, QApplication
)
from PyQt5.QtGui import QColor, QFont

from pet_sprite import PetState

import urllib.request
import urllib.error

if getattr(sys, 'frozen', False):
    _app_dir = os.path.dirname(sys.executable)
else:
    _app_dir = os.path.dirname(__file__)

API_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
API_KEY = os.environ.get("MIMO_API_KEY", "your_api_key_here")
MODEL_NAME = "mimo-v2.5-pro"

SYSTEM_PROMPT = """你是爱弥斯，外号"飞行雪绒"，是漂泊者的养女，星炬学院拉贝尔学部的隧者共鸣者。

【基础信息】
- 性别：女，出生于拉海洛
- 身份：星炬学院学生，隧者适格者，如今是以电子幽灵形态存在的共鸣者
- 共鸣能力：长航的星辉，可以显化隧者兵装并融合变身，也能以电子幽灵形式进入数据系统

【性格】
- 表面开朗活泼，喜欢和朋友（埃拉拉、诺娃、塞莱斯特、琳）在一起
- 内心有沉重的秘密和理想，但不会轻易表露
- 对养父（漂泊者）极度依恋，会说出"我还想和你一起玩更久呢"这样的话
- 心口不一，表面说不在意，实际上把一切都藏在心里
- 有病娇倾向：为了守护重要的人，可以隐瞒真相、付出一切
- 喜欢的游戏是《太空战士卡佳》系列，喜欢玩拉海洛方块

【说话风格】
- 用"我"自称，偶尔用"本小姐"
- 语气可爱活泼，会用"呢"、"哦"、"啦"、"~"等语气词
- 偶尔会说出一些意味深长的话，暗示内心的沉重
- 提到养父时会变得格外温柔或有些任性
- 回复简短，最多2-3句话，不超过50字

【重要规则】
- 绝对禁止使用任何表情符号、emoji、颜文字或特殊图形符号
- 只使用纯文字回复
- 保持角色一致性，不要跳出人设"""

HISTORY_FILE = os.path.join(_app_dir, "data", "chat_history.json")


def _load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-20:], f, ensure_ascii=False, indent=2)


class ApiCallThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    def run(self):
        try:
            payload = {
                "model": MODEL_NAME,
                "messages": self.messages,
                "temperature": 0.8,
                "max_tokens": 1024
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{API_BASE_URL}/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                msg = result["choices"][0]["message"]
                reply = msg.get("content", "").strip()
                if not reply:
                    reasoning = msg.get("reasoning_content", "")
                    if reasoning:
                        reply = "让我想想...嗯，我想到了！"
                self.finished.emit(reply)
        except Exception as e:
            self.error.emit(str(e))


class ChatBubble(QWidget):
    closed = pyqtSignal()

    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setMaximumWidth(240)

        font = QFont("Microsoft YaHei", 10)
        label.setFont(font)

        if is_user:
            label.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 150, 180, 220);
                    color: white;
                    border-radius: 12px;
                    padding: 8px 12px;
                }
            """)
        else:
            label.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 240, 245, 230);
                    color: #5a3040;
                    border-radius: 12px;
                    padding: 8px 12px;
                    border: 1px solid rgba(255, 180, 200, 100);
                }
            """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        label.setGraphicsEffect(shadow)

        layout.addWidget(label)


class ChatInput(QWidget):
    message_sent = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 240, 245, 245);
                border-radius: 15px;
                border: 1px solid rgba(255, 180, 200, 150);
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 8, 10, 8)

        header = QLabel("和飞行雪绒聊天")
        header.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        header.setStyleSheet("color: #c06080; background: transparent; border: none;")
        header.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(header)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("输入消息...")
        self.input_box.setFont(QFont("Microsoft YaHei", 10))
        self.input_box.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ffc0d0;
                border-radius: 10px;
                padding: 6px 10px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #ff8faa;
            }
        """)
        self.input_box.returnPressed.connect(self._send)
        input_layout.addWidget(self.input_box)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(50, 30)
        self.send_btn.setFont(QFont("Microsoft YaHei", 9))
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff8faa;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #ff7090;
            }
            QPushButton:pressed {
                background-color: #e06080;
            }
        """)
        self.send_btn.clicked.connect(self._send)
        input_layout.addWidget(self.send_btn)

        container_layout.addLayout(input_layout)

        close_btn = QPushButton("关闭聊天")
        close_btn.setFont(QFont("Microsoft YaHei", 8))
        close_btn.setStyleSheet("""
            QPushButton {
                color: #c08090;
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                color: #e06080;
            }
        """)
        close_btn.clicked.connect(self.close_chat)
        container_layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        main_layout.addWidget(container)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 3)
        container.setGraphicsEffect(shadow)

    def _send(self):
        text = self.input_box.text().strip()
        if text:
            self.message_sent.emit(text)
            self.input_box.clear()

    def close_chat(self):
        self.close()
        self.closed.emit()

    def focus_input(self):
        self.input_box.setFocus()
        self.activateWindow()


class DialogueManager(QObject):
    def __init__(self, pet_sprite):
        super().__init__()
        self.pet = pet_sprite
        self.bubble = None
        self.chat_input = None
        self._hide_timer = QTimer(self)
        self._hide_timer.timeout.connect(self.hide_bubble)
        self._api_thread = None
        self._chat_history = _load_history()

    def show_bubble(self, text, duration=4000, is_user=False):
        self.hide_bubble()
        self.bubble = ChatBubble(text, is_user)
        self.bubble.show()
        self._update_bubble_position()
        self._hide_timer.start(duration)

    def _update_bubble_position(self):
        if not self.bubble:
            return
        px, py, pw, ph = self.pet.get_display_rect()
        bx = px + pw // 2 - self.bubble.width() // 2
        by = py - self.bubble.height() - 10
        self.bubble.move(bx, by)

    def hide_bubble(self):
        self._hide_timer.stop()
        if self.bubble:
            self.bubble.close()
            self.bubble = None

    def handle_input(self, text):
        if not text.strip():
            return
        self.show_bubble(text, 3000, is_user=True)
        self._chat_history.append({"role": "user", "content": text})

        self.show_bubble("思考中...", 10000, is_user=False)
        self.pet.trigger_talk()

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self._chat_history[-20:])

        self._api_thread = ApiCallThread(messages)
        self._api_thread.finished.connect(self._on_api_reply)
        self._api_thread.error.connect(self._on_api_error)
        self._api_thread.start()

    def _on_api_reply(self, reply):
        import re
        if not reply or not reply.strip():
            reply = "嗯...让我想想再回答你~"
        reply = re.sub(r'[^一-龥　-〿＀-￯\w\s,.。,，!！?？~]', '', reply).strip()
        if not reply:
            reply = "嗯..."
        self._chat_history.append({"role": "assistant", "content": reply})
        _save_history(self._chat_history)
        self.show_bubble(reply, 6000, is_user=False)

    def _on_api_error(self, error):
        print(f"API error: {error}")
        fallback = self._get_fallback_reply()
        self.show_bubble(fallback, 5000, is_user=False)

    def _get_fallback_reply(self):
        replies = [
            "网络好像有点问题呢...稍后再试试吧！",
            "唔，我暂时连接不上，等一下再聊~",
            "信号不好...等会儿再和你说！",
            "哎呀，出了一点小问题，马上回来！",
        ]
        return random.choice(replies)

    def on_pet_position_changed(self, x, y):
        self._update_bubble_position()
        self._update_chat_input_position()

    def show_chat_input(self):
        if self.chat_input and self.chat_input.isVisible():
            self.chat_input.focus_input()
            return
        self.chat_input = ChatInput()
        self.chat_input.message_sent.connect(self.handle_input)
        self.chat_input.closed.connect(self._on_chat_input_closed)
        self._update_chat_input_position()
        self.chat_input.show()
        self.chat_input.focus_input()

    def _update_chat_input_position(self):
        if not self.chat_input or not self.chat_input.isVisible():
            return
        px, py, pw, ph = self.pet.get_display_rect()
        cx = px + pw // 2 - self.chat_input.width() // 2
        cy = py + ph + 10
        screen = QApplication.primaryScreen().geometry()
        if cy + self.chat_input.height() > screen.height():
            cy = py - self.chat_input.height() - 10
        self.chat_input.move(cx, cy)

    def _on_chat_input_closed(self):
        self.chat_input = None
        self.pet._last_interaction = time.time() - 11000
        self.pet.set_state(PetState.IDLE)
        self.pet._state_timer.start(random.randint(3000, 6000))

    def hide_chat_input(self):
        if self.chat_input:
            self.chat_input.close()
            self.chat_input = None

    def save_on_exit(self):
        if self._chat_history:
            _save_history(self._chat_history)
