import os

from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtWidgets import (
    QMainWindow, QMenu, QAction,
    QApplication
)
from PyQt5.QtGui import QPainter, QCursor

from pet_sprite import PetSprite, PetState
from dialogue import DialogueManager
from reminder import ReminderManager
from config import load_settings, save_settings


class PetWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        settings = load_settings()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        asset_path = os.path.join(os.path.dirname(__file__), "assets", "ams.gif")
        self.pet = PetSprite(
            asset_path,
            x=settings["pet_x"],
            y=settings["pet_y"],
            size=settings["pet_size"]
        )

        self.dialogue = DialogueManager(self.pet)
        self.reminder = ReminderManager(self.pet)

        self.pet.position_changed.connect(self._on_pet_moved)
        self.pet.position_changed.connect(self.dialogue.on_pet_position_changed)
        self.reminder.reminder_triggered.connect(self._on_reminder_triggered)

        self._dragging = False
        self._drag_offset = QPoint()

        self._idle_speech_enabled = True
        self._idle_speech_start_timer = QTimer(self)
        self._idle_speech_start_timer.setSingleShot(True)
        self._idle_speech_start_timer.timeout.connect(self._start_idle_speech_if_enabled)
        self._idle_speech_start_timer.start(10000)

        self._update_geometry()
        self.show()

    def _start_idle_speech_if_enabled(self):
        if self._idle_speech_enabled:
            self.dialogue.start_idle_speech()

    def _update_geometry(self):
        x, y, w, h = self.pet.get_display_rect()
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(x, y, w, h)
        self.update()

    def _on_pet_moved(self, x, y):
        self._update_geometry()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        pixmap = self.pet.get_current_pixmap()
        x, y, w, h = self.pet.get_display_rect()
        local_x = x - self.x()
        local_y = y - self.y()
        painter.drawPixmap(local_x, local_y, w, h, pixmap)
        painter.end()

    def _is_click_on_pet(self, pos):
        local_x = pos.x() - self.x()
        local_y = pos.y() - self.y()
        px, py, pw, ph = self.pet.get_display_rect()
        local_pet_x = px - self.x()
        local_pet_y = py - self.y()
        rel_x = local_x - local_pet_x
        rel_y = local_y - local_pet_y
        if rel_x < 0 or rel_x >= pw or rel_y < 0 or rel_y >= ph:
            return False
        pixmap = self.pet.get_current_pixmap()
        if rel_x < pixmap.width() and rel_y < pixmap.height():
            img = pixmap.toImage()
            color = img.pixelColor(rel_x, rel_y)
            return color.alpha() > 30
        return False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._is_click_on_pet(event.globalPos()):
                self._dragging = True
                self._drag_offset = event.globalPos() - self.pos()
                self.pet.trigger_happy()
                self.dialogue.stop_idle_speech()
                self._idle_speech_start_timer.start(15000)

                reply_texts = [
                    "嘿嘿，被发现了！",
                    "哎呀，别戳我啦~",
                    "你是在和我玩吗？",
                    "咕噜~（发出可爱的声音）",
                    "摸摸头~",
                ]
                import random
                self.dialogue.show_bubble(random.choice(reply_texts), 3000)

        elif event.button() == Qt.RightButton:
            if self._is_click_on_pet(event.globalPos()):
                self.dialogue.stop_idle_speech()
                self._idle_speech_start_timer.start(15000)
                self._show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.LeftButton:
            new_pos = event.globalPos() - self._drag_offset
            self.pet.move_to(new_pos.x(), new_pos.y())
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._save_position()

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 20px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #e0e0ff;
            }
        """)

        talk_action = QAction("对话", self)
        talk_action.triggered.connect(self._open_dialogue)
        menu.addAction(talk_action)

        reminder_action = QAction("设置提醒", self)
        reminder_action.triggered.connect(self._open_reminder)
        menu.addAction(reminder_action)

        speech_label = "关闭待机语音" if self._idle_speech_enabled else "开启待机语音"
        speech_action = QAction(speech_label, self)
        speech_action.triggered.connect(self._toggle_idle_speech)
        menu.addAction(speech_action)

        menu.addSeparator()

        size_menu = menu.addMenu("大小")
        for size_label, size_val in [("小", 100), ("中", 150), ("大", 200), ("特大", 250)]:
            action = QAction(size_label, self)
            action.triggered.connect(lambda checked, s=size_val: self._change_size(s))
            size_menu.addAction(action)

        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        menu.exec_(pos)

    def _open_dialogue(self):
        self.dialogue.show_chat_input()

    def _open_reminder(self):
        self.reminder.open_dialog(self)

    def _toggle_idle_speech(self):
        self._idle_speech_enabled = not self._idle_speech_enabled
        if self._idle_speech_enabled:
            self.dialogue.start_idle_speech()
        else:
            self.dialogue.stop_idle_speech()

    def _on_reminder_triggered(self, content):
        self.dialogue.show_bubble(f"提醒：{content}", 6000)
        self.pet.trigger_happy()

    def _change_size(self, new_size):
        self.pet.update_size(new_size)
        self._update_geometry()
        self._save_position()

    def _save_position(self):
        settings = load_settings()
        settings["pet_x"] = self.pet.x
        settings["pet_y"] = self.pet.y
        settings["pet_size"] = self.pet.size
        save_settings(settings)

    def _quit(self):
        self._save_position()
        self.dialogue.save_on_exit()
        self.dialogue.hide_bubble()
        self.dialogue.hide_chat_input()
        QApplication.quit()

    def closeEvent(self, event):
        self._save_position()
        self.dialogue.save_on_exit()
        self.dialogue.hide_bubble()
        self.dialogue.hide_chat_input()
        super().closeEvent(event)
