import os
import sys
import random
import time
from enum import Enum, auto


def _get_asset_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "assets", "ams.gif")
    return os.path.join(os.path.dirname(__file__), "assets", "ams.gif")

from PIL import Image, ImageFilter
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap, QTransform
from PyQt5.QtWidgets import QApplication


class PetState(Enum):
    IDLE = auto()
    WALK_LEFT = auto()
    WALK_RIGHT = auto()
    FLY = auto()
    HAPPY = auto()
    TALK = auto()


class PetSprite(QObject):
    state_changed = pyqtSignal(PetState)
    position_changed = pyqtSignal(int, int)

    def __init__(self, asset_path, x=800, y=400, size=150):
        super().__init__()
        self.x = x
        self.y = y
        self.size = size
        self.state = PetState.IDLE
        self.facing_right = True
        self.idle_offset = 0
        self.idle_direction = 1
        self.walk_speed = 3
        self.bounce_scale = 1.0
        self.bounce_target = 1.0

        self._fly_dx = 0
        self._fly_dy = 0
        self._last_interaction = 0
        self._happy_count = 0

        self._frames_right = []
        self._frames_left = []
        self._frames_happy_right = []
        self._frames_happy_left = []
        self._current_frame = 0
        self._frame_delay = 100
        self._is_gif = False

        self._gif_timer = QTimer(self)
        self._gif_timer.timeout.connect(self._next_frame)

        self._load_images(asset_path)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(50)

        self._state_timer = QTimer(self)
        self._state_timer.timeout.connect(self._random_state_change)
        self._state_timer.start(random.randint(3000, 8000))

        self._bounce_timer = QTimer(self)
        self._bounce_timer.timeout.connect(self._update_bounce)

    def _load_images(self, asset_path):
        img = Image.open(asset_path)
        self._is_gif = getattr(img, 'is_animated', False)

        if self._is_gif:
            self._load_gif(img)
        else:
            self._load_static(img)

    def _load_gif(self, img):
        self._frames_right = []
        self._frames_left = []
        self._frames_happy_right = []
        self._frames_happy_left = []

        try:
            frame_count = img.n_frames
        except AttributeError:
            frame_count = 1

        for i in range(frame_count):
            img.seek(i)
            frame = img.convert("RGBA").resize((self.size, self.size), Image.LANCZOS)

            self._frames_right.append(self._pil_to_qpixmap(frame))
            self._frames_left.append(self._pil_to_qpixmap(frame.transpose(Image.FLIP_LEFT_RIGHT)))

            happy_size = int(self.size * 1.15)
            happy_frame = frame.resize((happy_size, happy_size), Image.LANCZOS)
            self._frames_happy_right.append(self._pil_to_qpixmap(happy_frame))
            self._frames_happy_left.append(self._pil_to_qpixmap(happy_frame.transpose(Image.FLIP_LEFT_RIGHT)))

            try:
                duration = img.info.get('duration', 100)
                if duration > 0:
                    self._frame_delay = duration
            except Exception:
                pass

        self._current_frame = 0
        self._start_gif_timer()

    def _load_static(self, img):
        img = img.convert("RGBA").resize((self.size, self.size), Image.LANCZOS)

        pixmap = self._pil_to_qpixmap(img)
        self._frames_right = [pixmap]
        self._frames_left = [self._pil_to_qpixmap(img.transpose(Image.FLIP_LEFT_RIGHT))]

        happy_size = int(self.size * 1.15)
        happy_img = img.resize((happy_size, happy_size), Image.LANCZOS)
        self._frames_happy_right = [self._pil_to_qpixmap(happy_img)]
        self._frames_happy_left = [self._pil_to_qpixmap(happy_img.transpose(Image.FLIP_LEFT_RIGHT))]

    def _start_gif_timer(self):
        if self._is_gif and len(self._frames_right) > 1:
            self._gif_timer.start(self._frame_delay)

    def _pil_to_qpixmap(self, pil_img):
        data = pil_img.tobytes("raw", "RGBA")
        qimg = QImage(
            data, pil_img.width, pil_img.height, QImage.Format_RGBA8888
        )
        return QPixmap.fromImage(qimg)

    def get_current_pixmap(self):
        if self.state == PetState.HAPPY:
            frames = self._frames_happy_right if self.facing_right else self._frames_happy_left
        else:
            frames = self._frames_right if self.facing_right else self._frames_left

        if frames:
            return frames[self._current_frame % len(frames)]
        return QPixmap()

    def _next_frame(self):
        if self.state == PetState.HAPPY:
            frames = self._frames_happy_right if self.facing_right else self._frames_happy_left
        else:
            frames = self._frames_right if self.facing_right else self._frames_left

        if len(frames) > 1:
            self._current_frame = (self._current_frame + 1) % len(frames)

    def get_display_rect(self):
        pixmap = self.get_current_pixmap()
        w = pixmap.width()
        h = pixmap.height()
        offset_y = int(self.idle_offset)
        bounce_w = int(w * self.bounce_scale)
        bounce_h = int(h * self.bounce_scale)
        dx = (bounce_w - w) // 2
        dy = (bounce_h - h) // 2
        return self.x - dx, self.y - dy - offset_y, bounce_w, bounce_h

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.state_changed.emit(new_state)

    def _get_screen_size(self):
        screen = QApplication.primaryScreen().geometry()
        return screen.width(), screen.height()

    def _animate(self):
        if self.state in (PetState.WALK_LEFT, PetState.WALK_RIGHT):
            self._animate_walk()
        elif self.state == PetState.FLY:
            self._animate_fly()
        elif self.state == PetState.IDLE:
            self._animate_idle()
        elif self.state == PetState.HAPPY:
            self._animate_happy()

    def _animate_walk(self):
        screen_width, _ = self._get_screen_size()
        if self.state == PetState.WALK_RIGHT:
            self.x += self.walk_speed
            self.facing_right = True
            if self.x >= screen_width - self.size:
                self.set_state(PetState.WALK_LEFT)
        else:
            self.x -= self.walk_speed
            self.facing_right = False
            if self.x <= 0:
                self.set_state(PetState.WALK_RIGHT)
        self.position_changed.emit(self.x, self.y)

    def _animate_fly(self):
        screen_width, screen_height = self._get_screen_size()
        self.x += self._fly_dx
        self.y += self._fly_dy

        if self._fly_dx != 0:
            self.facing_right = self._fly_dx > 0

        if self.x <= 0:
            self.x = 0
            self._fly_dx = abs(self._fly_dx)
        elif self.x >= screen_width - self.size:
            self.x = screen_width - self.size
            self._fly_dx = -abs(self._fly_dx)

        if self.y <= 0:
            self.y = 0
            self._fly_dy = abs(self._fly_dy)
        elif self.y >= screen_height - self.size:
            self.y = screen_height - self.size
            self._fly_dy = -abs(self._fly_dy)

        self.position_changed.emit(self.x, self.y)

    def _animate_idle(self):
        self.idle_offset += 0.5 * self.idle_direction
        if abs(self.idle_offset) > 5:
            self.idle_direction *= -1
        if random.random() < 0.05:
            screen_width, screen_height = self._get_screen_size()
            self.x += random.choice([-1, 1]) * 3
            self.x = max(0, min(self.x, screen_width - self.size))
            self.position_changed.emit(self.x, self.y)

    def _animate_happy(self):
        pass

    def _random_state_change(self):
        if self.state in (PetState.HAPPY, PetState.TALK):
            self._happy_count += 1
            if self._happy_count >= 2:
                self._happy_count = 0
                self.set_state(PetState.IDLE)
                self._state_timer.start(random.randint(3000, 8000))
                return
            self._state_timer.start(random.randint(2000, 4000))
            return

        now = time.time()
        idle_time = now - self._last_interaction

        if idle_time >= 10:
            if random.random() < 0.6:
                self._start_fly()
                self._state_timer.start(random.randint(3000, 6000))
                return

        roll = random.random()
        if roll < 0.5:
            self.set_state(PetState.WALK_RIGHT if random.random() < 0.5 else PetState.WALK_LEFT)
            self._state_timer.start(random.randint(1500, 4000))
        else:
            self.set_state(PetState.IDLE)
            self._state_timer.start(random.randint(1000, 3000))

    def _start_fly(self):
        self.set_state(PetState.FLY)
        speed = random.uniform(2, 4)
        angle = random.uniform(0, 360)
        import math
        self._fly_dx = speed * math.cos(math.radians(angle))
        self._fly_dy = speed * math.sin(math.radians(angle))

    def trigger_happy(self):
        self._last_interaction = time.time()
        self.set_state(PetState.HAPPY)
        self.bounce_scale = 1.2
        self.bounce_target = 1.0
        self._bounce_timer.start(30)
        self._state_timer.start(2000)

    def trigger_talk(self):
        self._last_interaction = time.time()
        self.set_state(PetState.TALK)
        self._state_timer.start(3000)

    def stop_talk(self):
        self._last_interaction = time.time()
        self.set_state(PetState.IDLE)
        self._state_timer.start(random.randint(3000, 8000))

    def _update_bounce(self):
        diff = self.bounce_target - self.bounce_scale
        if abs(diff) < 0.02:
            self.bounce_scale = self.bounce_target
            self._bounce_timer.stop()
            return
        self.bounce_scale += diff * 0.3

    def move_to(self, x, y):
        self._last_interaction = time.time()
        self.x = x
        self.y = y
        self.position_changed.emit(x, y)

    def update_size(self, new_size):
        self.size = new_size
        self._load_images(_get_asset_path())
        self._start_gif_timer()
