import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

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
