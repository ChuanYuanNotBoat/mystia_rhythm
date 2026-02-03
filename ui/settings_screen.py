# mystia_rhythm/ui/settings_screen.py
"""
设置界面
"""
import logging
from pathlib import Path

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.animation import Animation

from .ui_base import BaseScreen, CustomButton, CustomLabel
from config import config

logger = logging.getLogger(__name__)


class SettingsScreen(BaseScreen):
    """设置界面"""
    
    def __init__(self, game_engine, **kwargs):
        logger.info("初始化设置界面")
        super().__init__(game_engine, **kwargs)
        
        # 保存控件引用
        self.speed_slider = None
        self.note_size_slider = None
        self.latency_slider = None
        self.volume_slider = None
        self.key_layout_buttons = {}
        
        self._create_ui()
        
    def _create_ui(self):
        """创建UI"""
        # 背景
        bg_path = Path(__file__).parent.parent / 'assets' / 'images' / 'bg_menu.png'
        if bg_path.exists():
            try:
                bg_image = Image(
                    source=str(bg_path),
                    allow_stretch=True,
                    size_hint=(1, 1),
                    pos_hint={'x': 0, 'y': 0}
                )
                self.add_widget(bg_image)
            except Exception as e:
                logger.error(f"背景图片加载失败: {e}")
        
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=50, spacing=20,
                                size_hint=(0.8, 0.8), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        # 标题
        title_label = CustomLabel(
            text='设置',
            font_size=36,
            size_hint_y=0.2,
            color=[1, 1, 1, 1]
        )
        
        # 设置项容器
        settings_layout = GridLayout(cols=2, spacing=20, size_hint_y=0.6)
        
        # 流速设置
        speed_label = CustomLabel(
            text='流速:',
            font_size=20,
            size_hint_x=0.3,
            color=[1, 1, 1, 1]
        )
        
        speed_slider_layout = BoxLayout(orientation='horizontal', spacing=10)
        
        current_speed = config.get('gameplay.scroll_speed', 1.0)
        current_speed = max(1.0, min(10.0, current_speed))
        
        self.speed_slider = Slider(
            min=1.0,
            max=10.0,
            value=current_speed,
            size_hint_x=0.7
        )
        self.speed_slider.bind(value=self._on_speed_change)
        
        self.speed_value_label = CustomLabel(
            text=f'{self.speed_slider.value:.1f}x',
            size_hint_x=0.3,
            color=[1, 1, 1, 1]
        )
        
        speed_slider_layout.add_widget(self.speed_slider)
        speed_slider_layout.add_widget(self.speed_value_label)
        
        # 音符大小设置
        note_size_label = CustomLabel(
            text='音符大小:',
            font_size=20,
            size_hint_x=0.3,
            color=[1, 1, 1, 1]
        )
        
        note_size_slider_layout = BoxLayout(orientation='horizontal', spacing=10)
        
        self.note_size_slider = Slider(
            min=0.5,
            max=2.0,
            value=config.get('gameplay.note_size', 1.0),
            size_hint_x=0.7
        )
        self.note_size_slider.bind(value=self._on_note_size_change)
        
        self.note_size_value_label = CustomLabel(
            text=f'{self.note_size_slider.value:.1f}',
            size_hint_x=0.3,
            color=[1, 1, 1, 1]
        )
        
        note_size_slider_layout.add_widget(self.note_size_slider)
        note_size_slider_layout.add_widget(self.note_size_value_label)
        
        # 音频延迟设置
        latency_label = CustomLabel(
            text='音频延迟:',
            font_size=20,
            size_hint_x=0.3,
            color=[1, 1, 1, 1]
        )
        
        latency_slider_layout = BoxLayout(orientation='horizontal', spacing=10)
        
        self.latency_slider = Slider(
            min=0.0,
            max=0.2,
            value=config.get('audio.audio_latency', 0.05),
            size_hint_x=0.7
        )
        self.latency_slider.bind(value=self._on_latency_change)
        
        self.latency_value_label = CustomLabel(
            text=f'{self.latency_slider.value:.3f}s',
            size_hint_x=0.3,
            color=[1, 1, 1, 1]
        )
        
        latency_slider_layout.add_widget(self.latency_slider)
        latency_slider_layout.add_widget(self.latency_value_label)
        
        # 音量设置
        volume_label = CustomLabel(
            text='主音量:',
            font_size=20,
            size_hint_x=0.3,
            color=[1, 1, 1, 1]
        )
        
        volume_slider_layout = BoxLayout(orientation='horizontal', spacing=10)
        
        self.volume_slider = Slider(
            min=0.0,
            max=1.0,
            value=config.get('audio.volume_master', 0.8),
            size_hint_x=0.7
        )
        self.volume_slider.bind(value=self._on_volume_change)
        
        self.volume_value_label = CustomLabel(
            text=f'{self.volume_slider.value:.1f}',
            size_hint_x=0.3,
            color=[1, 1, 1, 1]
        )
        
        volume_slider_layout.add_widget(self.volume_slider)
        volume_slider_layout.add_widget(self.volume_value_label)
        
        # 键位布局设置
        key_layout_label = CustomLabel(
            text='键位布局:',
            font_size=20,
            size_hint_x=0.3,
            color=[1, 1, 1, 1]
        )
        
        key_layout_buttons = BoxLayout(orientation='horizontal', spacing=10)
        
        layouts = ['standard', 'wasd', 'arrows']
        current_layout = config.get('gameplay.key_layout', 'standard')
        
        for layout in layouts:
            btn = ToggleButton(
                text=layout.upper(),
                group='key_layout',
                state='down' if layout == current_layout else 'normal'
            )
            btn.layout = layout
            btn.bind(on_press=self._on_key_layout_change)
            self.key_layout_buttons[layout] = btn
            key_layout_buttons.add_widget(btn)
        
        # 添加设置项
        settings_layout.add_widget(speed_label)
        settings_layout.add_widget(speed_slider_layout)
        settings_layout.add_widget(note_size_label)
        settings_layout.add_widget(note_size_slider_layout)
        settings_layout.add_widget(latency_label)
        settings_layout.add_widget(latency_slider_layout)
        settings_layout.add_widget(volume_label)
        settings_layout.add_widget(volume_slider_layout)
        settings_layout.add_widget(key_layout_label)
        settings_layout.add_widget(key_layout_buttons)
        
        # 按钮区域
        button_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=0.2)
        
        # 保存按钮
        save_btn = CustomButton(
            text='保存设置',
            size_hint_x=0.4
        )
        save_btn.bind(on_release=self._on_save)
        
        # 返回按钮
        back_btn = CustomButton(
            text='返回',
            size_hint_x=0.4
        )
        back_btn.bind(on_release=self._on_back)
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(back_btn)
        
        # 添加到主布局
        main_layout.add_widget(title_label)
        main_layout.add_widget(settings_layout)
        main_layout.add_widget(button_layout)
        
        self.add_widget(main_layout)
        
    def _on_speed_change(self, instance, value):
        """流速改变"""
        self.speed_value_label.text = f'{value:.1f}x'
        
    def _on_note_size_change(self, instance, value):
        """音符大小改变"""
        self.note_size_value_label.text = f'{value:.1f}'
        
    def _on_latency_change(self, instance, value):
        """音频延迟改变"""
        self.latency_value_label.text = f'{value:.3f}s'
        
    def _on_volume_change(self, instance, value):
        """音量改变"""
        self.volume_value_label.text = f'{value:.1f}'
        
    def _on_key_layout_change(self, instance):
        """键位布局改变"""
        if instance.state == 'down':
            logger.info(f"选择键位布局: {instance.layout}")
            
    def _on_save(self, *args):
        """保存设置"""
        logger.info("保存设置")
        
        try:
            # 使用保存的控件引用来获取值
            if self.speed_slider:
                config.set('gameplay.scroll_speed', self.speed_slider.value)
            
            if self.note_size_slider:
                config.set('gameplay.note_size', self.note_size_slider.value)
            
            if self.latency_slider:
                config.set('audio.audio_latency', self.latency_slider.value)
            
            if self.volume_slider:
                config.set('audio.volume_master', self.volume_slider.value)
            
            # 键位布局
            selected_layout = 'standard'
            for layout, btn in self.key_layout_buttons.items():
                if btn.state == 'down':
                    selected_layout = layout
                    break
            config.set('gameplay.key_layout', selected_layout)
            
            # 应用设置到游戏引擎
            if self.game_engine and self.speed_slider:
                self.game_engine.scroll_speed = self.speed_slider.value
                
            if self.game_engine and hasattr(self.game_engine, 'audio'):
                if hasattr(self.game_engine.audio, 'set_volume'):
                    self.game_engine.audio.set_volume(
                        master=config.get('audio.volume_master', 0.8)
                    )
            
            logger.info("设置已保存")
            
        except Exception as e:
            logger.error(f"保存设置时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        self._on_back()
        
    def _on_back(self, *args):
        """返回"""
        logger.info("返回")
        self.parent.current = 'menu'
        
    def on_enter(self, *args):
        """当进入界面时"""
        # 淡入效果
        self.opacity = 0
        Animation(opacity=1, duration=0.3).start(self)