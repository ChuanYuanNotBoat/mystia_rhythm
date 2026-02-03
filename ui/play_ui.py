# mystia_rhythm/ui/play_ui.py
"""
游玩界面
显示音符、判定线、分数、连击等游戏元素
"""
import logging
from typing import List, Dict, Optional, Tuple
from math import floor
from pathlib import Path

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse, Quad
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout

from .ui_base import BaseScreen, CustomButton, CustomLabel
from core.chart_parser import Note, NoteType
from core.judgment_system import Judgment
from config import config

logger = logging.getLogger(__name__)

class NoteWidget(Widget):
    """音符Widget"""
    
    def __init__(self, note: Note, lane_width: float, **kwargs):
        super().__init__(**kwargs)
        self.note = note
        self.lane_width = lane_width
        self.is_hold = note.endbeat is not None
        self.hold_length = 0.0
        self.judged = False
        
        # 根据音符类型设置颜色
        if note.type == NoteType.TAP:
            self.color = [0.2, 0.8, 1.0, 1.0]  # 蓝色
        elif note.type == NoteType.HOLD:
            self.color = [0.2, 1.0, 0.6, 1.0]  # 绿色
        elif note.type == NoteType.DRAG:
            self.color = [1.0, 0.6, 0.2, 1.0]  # 橙色
        elif note.type == NoteType.FLICK:
            self.color = [1.0, 0.2, 0.8, 1.0]  # 粉色
        else:
            self.color = [0.8, 0.8, 0.8, 1.0]
            
    def update_position(self, y_pos: float, hold_length: float = 0.0) -> None:
        """更新音符位置"""
        self.pos = (
            self.note.column * self.lane_width + self.lane_width * 0.05,  # 留5%边距
            y_pos
        )
        
        # 设置大小
        note_size = config.get('gameplay.note_size', 1.0)
        self.size = (self.lane_width * 0.9, 30 * note_size)  # 高度增加，改为长方形
            
        # 如果是长按，更新长度
        if self.is_hold:
            self.hold_length = hold_length
            
    def draw(self) -> None:
        """绘制音符"""
        self.canvas.clear()
        
        with self.canvas:
            # 设置颜色
            Color(*self.color)
            
            if self.is_hold:
                # 绘制长按音符（矩形）
                Rectangle(pos=self.pos, size=(self.size[0], self.hold_length))
                
                # 绘制长按端点（长方形）
                Rectangle(pos=self.pos, size=self.size)
                Rectangle(pos=(self.pos[0], self.pos[1] + self.hold_length - self.size[1]), 
                         size=self.size)
            else:
                # 绘制点击音符（长方形）
                Rectangle(pos=self.pos, size=self.size)
                
            # 如果已判定，添加效果
            if self.judged:
                Color(1, 1, 1, 0.5)
                Rectangle(pos=(self.pos[0] - 5, self.pos[1] - 5), 
                         size=(self.size[0] + 10, self.size[1] + 10))
                
    def update_position(self, y_pos: float, hold_length: float = 0.0) -> None:
        """更新音符位置"""
        self.pos = (
            self.note.column * self.lane_width,
            y_pos
        )
        
        # 设置大小
        note_size = config.get('gameplay.note_size', 1.0)
        self.size = (self.lane_width * 0.9, 20 * note_size)
        
        # 如果是长按，更新长度
        if self.is_hold:
            self.hold_length = hold_length
            
    def draw(self) -> None:
        """绘制音符"""
        self.canvas.clear()
        
        with self.canvas:
            # 设置颜色
            Color(*self.color)
            
            if self.is_hold:
                # 绘制长按音符（矩形）
                Rectangle(pos=self.pos, size=(self.size[0], self.hold_length))
                
                # 绘制长按端点（圆形）
                Ellipse(pos=(self.pos[0], self.pos[1]), size=(self.size[0], self.size[1]))
                Ellipse(pos=(self.pos[0], self.pos[1] + self.hold_length - self.size[1]), 
                       size=(self.size[0], self.size[1]))
            else:
                # 绘制点击音符（圆形）
                Ellipse(pos=self.pos, size=self.size)
                
            # 如果已判定，添加效果
            if self.judged:
                Color(1, 1, 1, 0.5)
                Ellipse(pos=(self.pos[0] - 5, self.pos[1] - 5), 
                       size=(self.size[0] + 10, self.size[1] + 10))


class JudgmentLine(Widget):
    """判定线"""
    
    def __init__(self, lane_width: float, num_lanes: int, **kwargs):
        super().__init__(**kwargs)
        self.lane_width = lane_width
        self.num_lanes = num_lanes
        
    def draw(self) -> None:
        """绘制判定线"""
        self.canvas.clear()
        
        with self.canvas:
            # 判定线颜色
            Color(1, 1, 1, 0.8)
            
            # 绘制横线
            Line(points=[0, self.y, self.num_lanes * self.lane_width, self.y], width=2)
            
            # 绘制轨道分隔线
            for i in range(1, self.num_lanes):
                x = i * self.lane_width
                Color(1, 1, 1, 0.3)
                Line(points=[x, self.y - 100, x, self.y + 100], width=1)


class JudgmentEffect(Widget):
    """判定效果显示"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = ""
        self.color = [1, 1, 1, 1]
        self.opacity = 0
        self.size_hint = (None, None)
        self.size = (100, 50)
        
    def show(self, judgment: Judgment, x: float, y: float) -> None:
        """显示判定效果"""
        self.pos = (x - self.width/2, y)
        
        # 设置文本和颜色
        if judgment == Judgment.BEST:
            self.text = "BEST"
            self.color = [0, 1, 1, 1]  # 青色
        elif judgment == Judgment.COOL:
            self.text = "COOL"
            self.color = [0, 1, 0, 1]  # 绿色
        elif judgment == Judgment.GOOD:
            self.text = "GOOD"
            self.color = [1, 1, 0, 1]  # 黄色
        elif judgment == Judgment.MISS:
            self.text = "MISS"
            self.color = [1, 0, 0, 1]  # 红色
            
        # 动画效果
        self.opacity = 1
        anim = Animation(y=y + 50, opacity=0, duration=0.5)
        anim.start(self)


class PlayUI(BaseScreen):
    """游玩界面"""
    
    def __init__(self, game_engine, **kwargs):
        logger.info("初始化游玩界面")
        super().__init__(game_engine, **kwargs)
        
        # 游戏参数
        self.lanes = config.get('gameplay.lanes', 4)
        self.scroll_speed = config.get('gameplay.scroll_speed', 1.0)
        self.note_size = config.get('gameplay.note_size', 1.0)
        
        # 屏幕参数
        self.lane_width = self.width / self.lanes
        self.judgment_line_y = 100  # 判定线Y坐标
        
        # 音符Widgets
        self.note_widgets: List[NoteWidget] = []
        self.active_notes: Dict[int, NoteWidget] = {}  # 活跃音符
        
        # UI组件
        self.judgment_line: Optional[JudgmentLine] = None
        self.judgment_effect: Optional[JudgmentEffect] = None
        self.score_label: Optional[CustomLabel] = None
        self.combo_label: Optional[CustomLabel] = None
        self.accuracy_label: Optional[CustomLabel] = None
        self.time_label: Optional[CustomLabel] = None
        
        # 背景图片
        self.background_image: Optional[Image] = None
        
        # 注册回调
        game_engine.register_callback('on_note_hit', self.on_note_hit)
        game_engine.register_callback('on_note_miss', self.on_note_miss)
        game_engine.register_callback('on_combo_change', self.on_combo_change)
        game_engine.register_callback('on_score_change', self.on_score_change)
        
        logger.debug(f"游玩界面参数 - 轨道数: {self.lanes}, 轨道宽度: {self.lane_width}")
        # 创建UI
        self._create_ui()
        logger.info("游玩界面创建完成")


    def _create_ui(self) -> None:
        """创建UI组件"""
        logger.debug("开始创建游玩UI组件")
        
        # 先设置背景颜色
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_bg_rect, size=self._update_bg_rect)
        
        # 创建主容器（用于放置所有游戏元素）
        from kivy.uix.floatlayout import FloatLayout
        main_container = FloatLayout()
        
        # 背景图片必须先添加
        bg_path = self._get_background_path()
        if bg_path:
            try:
                self.background_image = Image(
                    source=str(bg_path),
                    allow_stretch=True,
                    size_hint=(1, 1),
                    pos_hint={'x': 0, 'y': 0}
                )
                main_container.add_widget(self.background_image)
                logger.info(f"背景图片已加载: {bg_path}")
            except Exception as e:
                logger.error(f"背景图片加载失败: {e}")
        else:
            logger.debug("未找到背景图片，使用纯色背景")
        
        # 判定线
        self.judgment_line = JudgmentLine(self.lane_width, self.lanes)
        self.judgment_line.y = self.judgment_line_y
        self.judgment_line.size = (self.width, 200)
        
        # 判定效果
        self.judgment_effect = JudgmentEffect()
        
        # 左上角：歌曲信息
        self.song_info_label = CustomLabel(
            text=self._get_song_info(),
            font_size=16,
            pos=(20, self.height - 100),
            size_hint=(None, None),
            size=(400, 40),
            color=[1, 1, 1, 1],
            halign='left'
        )
        self.song_info_label.bind(size=self.song_info_label.setter('text_size'))
        
        # 右上角：流速显示和调整
        speed_layout = BoxLayout(orientation='horizontal', spacing=5,
                                size_hint=(None, None), size=(200, 40),
                                pos=(self.width - 220, self.height - 100))
        
        self.speed_label = CustomLabel(
            text=f'流速: {self.scroll_speed:.1f}x',
            size_hint=(0.6, 1),
            color=[0.8, 0.8, 1, 1]
        )
        
        speed_down_btn = CustomButton(
            text='-',
            size_hint=(0.2, 1),
            font_size=20
        )
        speed_down_btn.bind(on_release=lambda x: self._adjust_speed(-0.1))
        
        speed_up_btn = CustomButton(
            text='+',
            size_hint=(0.2, 1),
            font_size=20
        )
        speed_up_btn.bind(on_release=lambda x: self._adjust_speed(0.1))
        
        speed_layout.add_widget(self.speed_label)
        speed_layout.add_widget(speed_down_btn)
        speed_layout.add_widget(speed_up_btn)
        
        # 左上角：分数显示
        self.score_label = CustomLabel(
            text='分数: 0',
            font_size=24,
            pos=(20, self.height - 150),
            size_hint=(None, None),
            size=(200, 40),
            color=[1, 1, 1, 1]
        )
        
        # 中间顶部：准确率显示
        self.accuracy_label = CustomLabel(
            text='准确率: 100.00%',
            font_size=28,
            pos_hint={'center_x': 0.5, 'y': 0.9},
            size_hint=(None, None),
            size=(300, 50),
            color=[1, 1, 1, 1]
        )
        
        # 中间：连击显示
        self.combo_label = CustomLabel(
            text='连击: 0',
            font_size=32,
            pos_hint={'center_x': 0.5, 'y': 0.7},
            size_hint=(None, None),
            size=(200, 50),
            color=[1, 1, 1, 1]
        )
        
        # 右上角：判定统计
        self.judgment_stats_label = CustomLabel(
            text='BEST: 0\nCOOL: 0\nGOOD: 0\nMISS: 0',
            font_size=14,
            pos=(self.width - 150, self.height - 200),
            size_hint=(None, None),
            size=(120, 120),
            color=[1, 1, 1, 0.8],
            halign='left'
        )
        self.judgment_stats_label.bind(size=self.judgment_stats_label.setter('text_size'))
        
        # 底部：时间显示
        self.time_label = CustomLabel(
            text='00:00 / 00:00',
            font_size=18,
            pos_hint={'center_x': 0.5, 'y': 0.05},
            size_hint=(None, None),
            size=(200, 30),
            color=[1, 1, 1, 0.7]
        )
        
        # 暂停按钮 - 使用CustomButton
        self.pause_btn = CustomButton(
            text='|| 暂停',
            font_size=24,
            pos_hint={'right': 0.95, 'top': 0.95},
            size_hint=(None, None),
            size=(100, 50),
            background_color=[0.2, 0.2, 0.2, 0.8]
        )
        self.pause_btn.bind(on_release=self._on_pause)
        
        # 轨道按钮（用于触摸输入）
        self.lane_buttons = []
        for i in range(self.lanes):
            # 计算按钮位置和大小，覆盖整个轨道区域
            lane_btn = CustomButton(
                text='',
                size_hint=(None, None),
                size=(self.lane_width, self.height),  # 高度覆盖整个屏幕
                pos=(i * self.lane_width, 0),  # 从底部开始
                background_color=[1, 1, 1, 0.05]  # 非常透明，仅用于触摸检测
            )
            lane_btn.lane = i
            lane_btn.bind(
                on_touch_down=lambda instance, touch, lane=i: self._on_lane_touch(instance, touch, lane)
            )
            self.lane_buttons.append(lane_btn)
            main_container.add_widget(lane_btn)
        
        # 重要：按正确的顺序添加widget到main_container
        main_container.add_widget(self.judgment_line)
        main_container.add_widget(self.judgment_effect)
        main_container.add_widget(self.song_info_label)
        main_container.add_widget(speed_layout)  # 添加流速调整布局
        main_container.add_widget(self.score_label)
        main_container.add_widget(self.accuracy_label)
        main_container.add_widget(self.combo_label)
        main_container.add_widget(self.judgment_stats_label)
        main_container.add_widget(self.time_label)
        main_container.add_widget(self.pause_btn)
        
        # 将主容器添加到屏幕
        self.add_widget(main_container)
        
        logger.debug("游玩UI组件创建完成")
        
    def _on_lane_touch(self, instance, touch, lane: int):
        """处理轨道触摸"""
        if instance.collide_point(*touch.pos):
            if self.game_engine:
                self.game_engine.handle_input(lane, True)
                # 设置定时器释放按键
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self.game_engine.handle_input(lane, False), 0.1)
            return True
        return False
        
    def _on_pause(self, instance):
        """暂停按钮点击事件"""
        logger.info("点击暂停按钮")
        if self.game_engine:
            try:
                self.game_engine.pause_game()
            except Exception as e:
                logger.error(f"暂停游戏失败: {e}")
        
    def _get_song_info(self) -> str:
        """获取歌曲信息"""
        if not self.game_engine.current_chart:
            return "未加载谱面"
            
        chart = self.game_engine.current_chart
        return f"{chart.metadata.title} - {chart.metadata.artist}\n难度: {chart.metadata.difficulty}"
        
    def _adjust_speed(self, delta: float):
        """调整流速"""
        self.scroll_speed = max(0.5, min(10.0, self.scroll_speed + delta))
        if self.speed_label:
            self.speed_label.text = f'流速: {self.scroll_speed:.1f}x'
            
    def update(self, current_time: float) -> None:
        """更新UI"""
        if not self.game_engine.current_chart:
            return
            
        self._update_notes(current_time)
        
        # 更新分数
        if self.score_label:
            score = self.game_engine.judgment.get_score()
            self.score_label.text = f'分数: {score:,}'
            
        # 更新准确率
        if self.accuracy_label:
            accuracy = self.game_engine.judgment.get_accuracy()
            self.accuracy_label.text = f'准确率: {accuracy:.2f}%'
            
        # 更新连击
        if self.combo_label:
            combo = self.game_engine.judgment.get_combo()
            self.combo_label.text = f'连击: {combo}'
            
            # 连击颜色效果
            if combo >= 50:
                self.combo_label.color = [1, 1, 0, 1]  # 黄色
            elif combo >= 100:
                self.combo_label.color = [1, 0.5, 0, 1]  # 橙色
            elif combo >= 200:
                self.combo_label.color = [1, 0, 0, 1]  # 红色
            else:
                self.combo_label.color = [1, 1, 1, 1]  # 白色
                
        # 更新判定统计
        if self.judgment_stats_label:
            counts = self.game_engine.judgment.calculator.judgment_counts
            stats_text = f'BEST: {counts.get("BEST", 0)}\nCOOL: {counts.get("COOL", 0)}\nGOOD: {counts.get("GOOD", 0)}\nMISS: {counts.get("MISS", 0)}'
            self.judgment_stats_label.text = stats_text
            
        # 更新时间显示
        if self.time_label and self.game_engine.current_chart:
            duration = self.game_engine.current_chart.metadata.duration
            if duration > 0:
                current_str = self._format_time(current_time)
                total_str = self._format_time(duration)
                self.time_label.text = f'{current_str} / {total_str}'
            else:
                current_str = self._format_time(current_time)
                self.time_label.text = f'{current_str}'
                
        # 重绘
        self._redraw()
        
    def _update_bg_rect(self, *args):
        """更新背景矩形"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        
    def _get_background_path(self) -> Optional[Path]:
        """获取背景图片路径"""
        if not self.game_engine.current_chart:
            return None
            
        chart = self.game_engine.current_chart
        chart_metadata = chart.metadata
        
        # 从元数据中获取背景文件名
        bg_filename = chart_metadata.background or chart_metadata.cover
        if not bg_filename:
            return None
            
        # 获取谱面文件所在目录
        if hasattr(self.game_engine, 'current_chart_path'):
            chart_dir = self.game_engine.current_chart_path.parent
            bg_path = chart_dir / bg_filename
            
            if bg_path.exists():
                return bg_path
                
        return None
        
    def on_size(self, *args) -> None:
        """当窗口大小改变时"""
        self.lane_width = self.width / self.lanes
        
        if self.judgment_line:
            self.judgment_line.lane_width = self.lane_width
            self.judgment_line.size = (self.width, 200)
            
        # 更新所有音符位置
        for widget in self.note_widgets:
            widget.lane_width = self.lane_width

        
    def _update_notes(self, current_time: float) -> None:
        """更新音符位置"""
        if not self.game_engine.current_chart:
            return
            
        chart = self.game_engine.current_chart
        timing = chart.timing_system
        
        # 计算可见时间范围（提前2秒显示）
        visible_start = current_time - 2.0
        visible_end = current_time + 5.0 / self.scroll_speed
        
        # 清理超出范围的音符
        widgets_to_remove = []
        for i, widget in enumerate(self.note_widgets):
            note_time = timing.beat_to_time(widget.note.beat)
            if note_time > visible_end:
                widgets_to_remove.append(i)
                
        # 反向移除，避免索引问题
        for i in reversed(widgets_to_remove):
            widget = self.note_widgets.pop(i)
            self.remove_widget(widget)
            
        # 添加新音符
        for i, note in enumerate(chart.notes):
            note_time = timing.beat_to_time(note.beat)
            
            # 检查是否在可见范围内且尚未创建widget
            if visible_start <= note_time <= visible_end:
                # 检查是否已创建widget
                note_exists = any(w.note == note for w in self.note_widgets)
                if not note_exists:
                    widget = NoteWidget(note, self.lane_width)
                    self.note_widgets.append(widget)
                    self.add_widget(widget)
                    
        # 更新所有音符位置
        for widget in self.note_widgets:
            note_time = timing.beat_to_time(widget.note.beat)
            
            # 计算Y坐标
            time_diff = note_time - current_time
            y_pos = self.judgment_line_y + (time_diff * 300 * self.scroll_speed)
            
            # 如果是长按，计算长度
            hold_length = 0
            if widget.note.endbeat:
                end_time = timing.beat_to_time(widget.note.endbeat)
                hold_length = (end_time - note_time) * 300 * self.scroll_speed
                
            # 更新位置
            widget.update_position(y_pos, hold_length)
            
            # 检查是否被判定
            if i in self.game_engine.judgment.judged_notes:
                widget.judged = True
                
    def _redraw(self) -> None:
        """重绘所有元素"""
        # 绘制判定线
        if self.judgment_line:
            self.judgment_line.draw()
            
        # 绘制音符
        for widget in self.note_widgets:
            widget.draw()
            
    def _format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        if seconds <= 0:
            return "00:00"
            
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f'{mins:02d}:{secs:02d}'
        
    def on_note_hit(self, result) -> None:
        """音符命中回调"""
        # 显示判定效果
        if self.judgment_effect:
            lane = result.lane if hasattr(result, 'lane') else 0
            x = (lane + 0.5) * self.lane_width
            self.judgment_effect.show(result.judgment, x, self.judgment_line_y + 50)
            
        # 连击效果
        if result.combo >= 10 and result.combo % 10 == 0:
            self._show_combo_effect(result.combo)
            
    def on_note_miss(self, result) -> None:
        """音符错过回调"""
        if self.judgment_effect:
            lane = result.lane if hasattr(result, 'lane') else 0
            x = (lane + 0.5) * self.lane_width
            self.judgment_effect.show(result.judgment, x, self.judgment_line_y + 50)
            
    def on_combo_change(self, combo: int) -> None:
        """连击改变回调"""
        if self.combo_label:
            self.combo_label.text = f'Combo: {combo}'
            
            # 连击颜色效果
            if combo >= 50:
                self.combo_label.color = [1, 1, 0, 1]  # 黄色
            elif combo >= 100:
                self.combo_label.color = [1, 0.5, 0, 1]  # 橙色
            elif combo >= 200:
                self.combo_label.color = [1, 0, 0, 1]  # 红色
            else:
                self.combo_label.color = [1, 1, 1, 1]  # 白色
                
    def on_score_change(self, score: int) -> None:
        """分数改变回调"""
        pass  # 已经在update中更新
        
    def _show_combo_effect(self, combo: int) -> None:
        """显示连击效果"""
        if combo >= 100:
            # 大数字效果
            effect = CustomLabel(
                text=str(combo),
                font_size=80,
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                size_hint=(None, None),
                size=(300, 100),
                color=[1, 1, 1, 1]
            )
            self.add_widget(effect)
            
            # 动画
            anim = Animation(font_size=100, opacity=0, duration=1.0)
            anim.start(effect)
            
            # 1秒后移除
            Clock.schedule_once(lambda dt: self.remove_widget(effect), 1.0)
            
    def get_lane_from_touch(self, x: float, y: float) -> Optional[int]:
        """从触摸位置获取轨道编号"""
        if 0 <= x <= self.width and 0 <= y <= self.height:
            lane = int(x / self.lane_width)
            if 0 <= lane < self.lanes:
                return lane
        return None
        

    def _on_pause_touch(self, instance, touch) -> bool:
        """暂停按钮触摸事件"""
        if instance.collide_point(*touch.pos):
            logger.info("点击暂停按钮")
            if hasattr(self, 'game_engine') and self.game_engine:
                try:
                    self.game_engine.pause_game()
                except Exception as e:
                    logger.error(f"暂停游戏失败: {e}")
            return True
        return False
        
    def on_enter(self):
        """进入界面时"""
        # 开始更新循环
        Clock.schedule_interval(self._update_callback, 1.0 / 60.0)  # 60fps
        
    def on_leave(self):
        """离开界面时"""
        # 停止更新循环
        Clock.unschedule(self._update_callback)
        
    def _update_callback(self, dt):
        """更新回调"""
        if self.game_engine.state.value == 3:  # PLAYING
            self.update(self.game_engine.current_time)