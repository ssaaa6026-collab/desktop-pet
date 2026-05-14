from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QListWidget,
    QListWidgetItem, QWidget
)
from PyQt5.QtGui import QFont

from config import (
    load_reminders, add_reminder, remove_reminder,
    get_pending_reminders, mark_reminder_fired
)


class ReminderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置提醒")
        self.setFixedSize(350, 400)
        self.setup_ui()
        self._load_list()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #fff0f5;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("日程提醒")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #c06080; background: transparent;")
        layout.addWidget(title)

        input_layout = QHBoxLayout()
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("时间 (如: 2025-01-15 14:30)")
        self.time_input.setFont(QFont("Microsoft YaHei", 10))
        self.time_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ffc0d0;
                border-radius: 8px;
                padding: 6px 10px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #ff8faa;
            }
        """)
        input_layout.addWidget(self.time_input)

        add_btn = QPushButton("添加")
        add_btn.setFixedWidth(60)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff8faa;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #ff7090;
            }
        """)
        add_btn.clicked.connect(self._add_reminder)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)

        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("提醒内容")
        self.content_input.setFont(QFont("Microsoft YaHei", 10))
        self.content_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ffc0d0;
                border-radius: 8px;
                padding: 6px 10px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #ff8faa;
            }
        """)
        layout.addWidget(self.content_input)

        self.reminder_list = QListWidget()
        self.reminder_list.setFont(QFont("Microsoft YaHei", 10))
        self.reminder_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ffc0d0;
                border-radius: 8px;
                background: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #ffe0e8;
            }
            QListWidget::item:selected {
                background-color: #ffd0e0;
                color: #5a3040;
            }
        """)
        layout.addWidget(self.reminder_list)

        btn_layout = QHBoxLayout()
        del_btn = QPushButton("删除选中")
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffa0b8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #ff8098;
            }
        """)
        del_btn.clicked.connect(self._delete_reminder)
        btn_layout.addWidget(del_btn)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0d0d8;
                color: #5a3040;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #d0c0c8;
            }
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _load_list(self):
        self.reminder_list.clear()
        reminders = load_reminders()
        for r in reminders:
            status = "✓" if r.get("fired") else "○"
            text = f"{status} {r['time']} - {r['content']}"
            self.reminder_list.addItem(QListWidgetItem(text))

    def _add_reminder(self):
        time_str = self.time_input.text().strip()
        content = self.content_input.text().strip()

        if not time_str or not content:
            QMessageBox.warning(self, "提示", "请填写时间和提醒内容")
            return

        from datetime import datetime
        try:
            datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            QMessageBox.warning(self, "提示", "时间格式错误，请使用: YYYY-MM-DD HH:MM")
            return

        add_reminder(time_str, content)
        self.time_input.clear()
        self.content_input.clear()
        self._load_list()

    def _delete_reminder(self):
        row = self.reminder_list.currentRow()
        if row < 0:
            return
        remove_reminder(row)
        self._load_list()


class ReminderManager(QObject):
    reminder_triggered = pyqtSignal(str)

    def __init__(self, pet_sprite):
        super().__init__()
        self.pet = pet_sprite
        self._check_timer = QTimer(self)
        self._check_timer.timeout.connect(self._check_reminders)
        self._check_timer.start(60000)

    def _check_reminders(self):
        pending = get_pending_reminders()
        for index, reminder in pending:
            mark_reminder_fired(index)
            self.reminder_triggered.emit(reminder["content"])

    def open_dialog(self, parent=None):
        dialog = ReminderDialog(parent)
        dialog.exec_()
