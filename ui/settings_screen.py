import logging
from pathlib import Path

from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from .ui_base import BaseScreen, CustomButton, CustomLabel
from config import config

logger = logging.getLogger(__name__)


class SettingsScreen(BaseScreen):
    """Settings screen with tabbed, scrollable pages."""

    def __init__(self, game_engine, **kwargs):
        super().__init__(game_engine, **kwargs)

        self.speed_slider = None
        self.note_size_slider = None
        self.latency_slider = None
        self.volume_slider = None
        self.key_layout_buttons = {}
        self.custom_binding_inputs = {}

        self.page_buttons = {}
        self.page_views = {}
        self.current_page = None
        self.page_host = None
        self.main_layout = None
        self.title_label = None
        self.tab_bar = None
        self.button_layout = None
        self._row_labels = []
        self._row_widgets = []

        self._create_ui()

    def _create_ui(self):
        bg_path = Path(__file__).parent.parent / 'assets' / 'images' / 'bg_menu.png'
        if bg_path.exists():
            try:
                bg_image = Image(
                    source=str(bg_path),
                    allow_stretch=True,
                    size_hint=(1, 1),
                    pos_hint={'x': 0, 'y': 0},
                )
                self.add_widget(bg_image)
            except Exception:
                logger.exception("Failed to load settings background")

        main_layout = BoxLayout(
            orientation='vertical',
            padding=24,
            spacing=12,
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
        )

        title_label = CustomLabel(
            text='Settings',
            font_size=34,
            size_hint_y=None,
            height=56,
            color=[1, 1, 1, 1],
        )

        tab_bar = BoxLayout(
            orientation='horizontal',
            spacing=8,
            size_hint_y=None,
            height=48,
        )

        for page_key, page_title in [
            ('gameplay', 'Gameplay'),
            ('audio', 'Audio'),
            ('controls', 'Controls'),
        ]:
            btn = ToggleButton(
                text=page_title,
                group='settings_pages',
                state='down' if page_key == 'gameplay' else 'normal',
            )
            btn.page_key = page_key
            btn.bind(on_release=self._on_switch_page)
            self.page_buttons[page_key] = btn
            tab_bar.add_widget(btn)

        self.page_host = BoxLayout(orientation='vertical')

        self.page_views['gameplay'] = self._build_gameplay_page()
        self.page_views['audio'] = self._build_audio_page()
        self.page_views['controls'] = self._build_controls_page()

        self._show_page('gameplay')

        button_layout = BoxLayout(
            orientation='horizontal',
            spacing=12,
            size_hint_y=None,
            height=56,
        )

        save_btn = CustomButton(text='Save', size_hint_x=0.5)
        save_btn.bind(on_release=self._on_save)

        back_btn = CustomButton(text='Back', size_hint_x=0.5)
        back_btn.bind(on_release=self._on_back)

        button_layout.add_widget(save_btn)
        button_layout.add_widget(back_btn)

        main_layout.add_widget(title_label)
        main_layout.add_widget(tab_bar)
        main_layout.add_widget(self.page_host)
        main_layout.add_widget(button_layout)

        self.main_layout = main_layout
        self.title_label = title_label
        self.tab_bar = tab_bar
        self.button_layout = button_layout

        self.bind(size=lambda *_: self._apply_responsive_layout())
        self.bind(pos=lambda *_: self._apply_responsive_layout())

        self.add_widget(main_layout)
        self._apply_responsive_layout()

    def _build_gameplay_page(self) -> ScrollView:
        content = self._new_page_content()

        content.add_widget(self._section_title('Gameplay Timing'))

        current_speed = config.get('gameplay.scroll_speed', 1.0)
        current_speed = max(1.0, min(10.0, current_speed))
        self.speed_slider = Slider(min=1.0, max=10.0, value=current_speed)
        self.speed_slider.bind(value=self._on_speed_change)
        self.speed_value_label = CustomLabel(text=f'{current_speed:.1f}x', size_hint_x=None, width=90)
        speed_control = BoxLayout(orientation='horizontal', spacing=8)
        speed_control.add_widget(self.speed_slider)
        speed_control.add_widget(self.speed_value_label)
        content.add_widget(self._row('Scroll Speed', speed_control))

        note_size = config.get('gameplay.note_size', 1.0)
        self.note_size_slider = Slider(min=0.5, max=2.0, value=note_size)
        self.note_size_slider.bind(value=self._on_note_size_change)
        self.note_size_value_label = CustomLabel(text=f'{note_size:.1f}', size_hint_x=None, width=90)
        note_control = BoxLayout(orientation='horizontal', spacing=8)
        note_control.add_widget(self.note_size_slider)
        note_control.add_widget(self.note_size_value_label)
        content.add_widget(self._row('Note Size', note_control))

        return self._wrap_scroll(content)

    def _build_audio_page(self) -> ScrollView:
        content = self._new_page_content()

        content.add_widget(self._section_title('Audio'))

        latency = config.get('audio.audio_latency', 0.05)
        self.latency_slider = Slider(min=0.0, max=0.2, value=latency)
        self.latency_slider.bind(value=self._on_latency_change)
        self.latency_value_label = CustomLabel(text=f'{latency:.3f}s', size_hint_x=None, width=90)
        latency_control = BoxLayout(orientation='horizontal', spacing=8)
        latency_control.add_widget(self.latency_slider)
        latency_control.add_widget(self.latency_value_label)
        content.add_widget(self._row('Audio Latency', latency_control))

        volume = config.get('audio.volume_master', 0.8)
        self.volume_slider = Slider(min=0.0, max=1.0, value=volume)
        self.volume_slider.bind(value=self._on_volume_change)
        self.volume_value_label = CustomLabel(text=f'{volume:.1f}', size_hint_x=None, width=90)
        volume_control = BoxLayout(orientation='horizontal', spacing=8)
        volume_control.add_widget(self.volume_slider)
        volume_control.add_widget(self.volume_value_label)
        content.add_widget(self._row('Master Volume', volume_control))

        return self._wrap_scroll(content)

    def _build_controls_page(self) -> ScrollView:
        content = self._new_page_content()

        content.add_widget(self._section_title('Key Layout'))

        key_layout_buttons = BoxLayout(
            orientation='horizontal',
            spacing=8,
            size_hint_y=None,
            height=44,
        )

        layouts = ['standard', 'wasd', 'arrows', 'custom']
        current_layout = config.get('gameplay.key_layout', 'standard')

        for layout in layouts:
            btn = ToggleButton(
                text=layout.upper(),
                group='key_layout',
                state='down' if layout == current_layout else 'normal',
            )
            btn.layout = layout
            btn.bind(on_press=self._on_key_layout_change)
            self.key_layout_buttons[layout] = btn
            key_layout_buttons.add_widget(btn)

        content.add_widget(key_layout_buttons)

        content.add_widget(self._section_title('Custom Bindings (comma separated)'))

        custom_bindings_layout = GridLayout(
            cols=2,
            spacing=8,
            size_hint_y=None,
        )
        custom_bindings_layout.bind(minimum_height=custom_bindings_layout.setter('height'))

        saved_custom = config.get('gameplay.key_bindings', {})
        lane_count = max(1, int(config.get('gameplay.lanes', 4)))

        for lane in range(lane_count):
            lane_label = CustomLabel(
                text=f'Lane {lane + 1}',
                size_hint_y=None,
                height=38,
                color=[1, 1, 1, 1],
            )

            default_value = ''
            if isinstance(saved_custom, dict):
                lane_keys = saved_custom.get(str(lane), saved_custom.get(lane, []))
                if isinstance(lane_keys, list):
                    default_value = ','.join([str(k) for k in lane_keys])
                elif isinstance(lane_keys, str):
                    default_value = lane_keys

            lane_input = TextInput(
                text=default_value,
                multiline=False,
                size_hint_y=None,
                height=38,
                hint_text='example: d,f',
            )
            self.custom_binding_inputs[lane] = lane_input

            custom_bindings_layout.add_widget(lane_label)
            custom_bindings_layout.add_widget(lane_input)

        content.add_widget(custom_bindings_layout)

        return self._wrap_scroll(content)

    def _new_page_content(self) -> BoxLayout:
        content = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=[8, 8, 8, 8],
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter('height'))
        return content

    def _wrap_scroll(self, content: BoxLayout) -> ScrollView:
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=8)
        scroll.add_widget(content)
        return scroll

    def _section_title(self, text: str) -> CustomLabel:
        return CustomLabel(
            text=text,
            font_size=18,
            size_hint_y=None,
            height=34,
            color=[1, 1, 1, 1],
        )

    def _row(self, label_text: str, control_widget) -> BoxLayout:
        row = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint_y=None,
            height=44,
        )
        label = CustomLabel(
            text=label_text,
            size_hint_x=None,
            width=180,
            color=[1, 1, 1, 1],
        )
        row.add_widget(label)
        row.add_widget(control_widget)
        self._row_labels.append(label)
        self._row_widgets.append(row)
        return row

    def _apply_responsive_layout(self):
        """Apply responsive sizing based on current screen size."""
        if not self.main_layout:
            return

        w = max(640, float(self.width))
        h = max(360, float(self.height))
        scale = min(w / 1280.0, h / 720.0)
        scale = max(0.75, min(1.35, scale))

        pad = int(18 * scale)
        spacing = int(10 * scale)
        self.main_layout.padding = [pad, pad, pad, pad]
        self.main_layout.spacing = spacing

        if self.title_label:
            self.title_label.font_size = int(34 * scale)
            self.title_label.height = int(56 * scale)

        if self.tab_bar:
            self.tab_bar.height = int(46 * scale)
            self.tab_bar.spacing = max(6, int(8 * scale))

        if self.button_layout:
            self.button_layout.height = int(54 * scale)
            self.button_layout.spacing = max(8, int(12 * scale))

        label_width = max(120, min(280, int(w * 0.2)))
        row_height = max(40, int(44 * scale))
        for label in self._row_labels:
            label.width = label_width
        for row in self._row_widgets:
            row.height = row_height

    def _on_switch_page(self, instance):
        if instance.state == 'down':
            self._show_page(instance.page_key)

    def _show_page(self, page_key: str):
        if page_key not in self.page_views:
            return

        self.page_host.clear_widgets()
        self.page_host.add_widget(self.page_views[page_key])
        self.current_page = page_key

    def _on_speed_change(self, instance, value):
        self.speed_value_label.text = f'{value:.1f}x'

    def _on_note_size_change(self, instance, value):
        self.note_size_value_label.text = f'{value:.1f}'

    def _on_latency_change(self, instance, value):
        self.latency_value_label.text = f'{value:.3f}s'

    def _on_volume_change(self, instance, value):
        self.volume_value_label.text = f'{value:.1f}'

    def _on_key_layout_change(self, instance):
        if instance.state == 'down':
            logger.info(f"Selected key layout: {instance.layout}")

    def _on_save(self, *args):
        logger.info("Saving settings")

        try:
            if self.speed_slider:
                config.set('gameplay.scroll_speed', self.speed_slider.value)

            if self.note_size_slider:
                config.set('gameplay.note_size', self.note_size_slider.value)

            if self.latency_slider:
                config.set('audio.audio_latency', self.latency_slider.value)

            if self.volume_slider:
                config.set('audio.volume_master', self.volume_slider.value)

            selected_layout = 'standard'
            for layout, btn in self.key_layout_buttons.items():
                if btn.state == 'down':
                    selected_layout = layout
                    break
            config.set('gameplay.key_layout', selected_layout)

            custom_bindings = {}
            for lane, input_widget in self.custom_binding_inputs.items():
                raw = input_widget.text.strip().lower()
                keys = [k.strip() for k in raw.split(',') if k.strip()]
                keys = [k for k in keys if len(k) == 1]
                custom_bindings[str(lane)] = keys
            config.set('gameplay.key_bindings', custom_bindings)

            if self.game_engine and self.speed_slider:
                self.game_engine.scroll_speed = self.speed_slider.value

            if self.game_engine and hasattr(self.game_engine, 'audio'):
                if hasattr(self.game_engine.audio, 'set_volume'):
                    self.game_engine.audio.set_volume(
                        master=config.get('audio.volume_master', 0.8)
                    )

            logger.info("Settings saved")

        except Exception:
            logger.exception("Failed to save settings")

        self._on_back()

    def _on_back(self, *args):
        logger.info("Back to menu")
        self.parent.current = 'menu'

    def on_enter(self, *args):
        self.opacity = 0
        Animation(opacity=1, duration=0.3).start(self)
        self._apply_responsive_layout()

    def on_window_resize(self, width, height):
        self._apply_responsive_layout()
