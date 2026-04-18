from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen


class CustomButton(Button):
    """Custom rounded button."""

    background_color = ListProperty([0.2, 0.2, 0.2, 1])
    hover_color = ListProperty([0.3, 0.3, 0.3, 1])
    font_name = StringProperty('DefaultFont')

    def __init__(self, **kwargs):
        if 'font_name' not in kwargs:
            kwargs['font_name'] = 'DefaultFont'
        super().__init__(**kwargs)

        self.bind(
            pos=self._update_rect,
            size=self._update_rect,
            background_color=self._update_rect,
        )
        self._is_hovering = False

    def _update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            color = self.hover_color if self._is_hovering else self.background_color
            Color(*color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._is_hovering = True
            self._update_rect()
            return super().on_touch_down(touch)
        return False

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self._is_hovering = False
            self._update_rect()
        return super().on_touch_up(touch)


class CustomLabel(Label):
    """Custom label with default font."""

    def __init__(self, **kwargs):
        if 'font_name' not in kwargs:
            kwargs['font_name'] = 'DefaultFont'
        super().__init__(**kwargs)


class BaseScreen(Screen):
    """Base screen class."""

    def __init__(self, game_engine, **kwargs):
        super().__init__(**kwargs)
        self.game_engine = game_engine

    def on_enter(self, *args):
        pass

    def on_leave(self, *args):
        pass

    def on_window_resize(self, width, height):
        """Window resize hook for responsive screens."""
        pass
