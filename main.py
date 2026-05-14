import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# 加载 .env 文件
_env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_file):
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ.setdefault(key, value)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from pet_window import PetWindow


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    pet = PetWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
