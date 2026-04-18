# mystia_rhythm/core/game_engine.py
"""
游戏引擎主循环 - 修复判定和按键处理
"""
import logging
from typing import Dict, List, Optional, Callable
from enum import Enum
from pathlib import Path

from kivy.app import App
from kivy.core.window import Window

from .timing import GameClock
from .audio_manager import AudioManager
from .chart_parser import Chart, Note, NoteType
from .judgment_system import JudgmentSystem, Judgment, JudgmentResult
from config import config
from ui.play_ui import PlayUI


# 配置日志
logger = logging.getLogger(__name__)

class GameState(Enum):
    """游戏状态"""
    LOADING = 0
    MENU = 1
    SONG_SELECT = 2
    PLAYING = 3
    PAUSED = 4
    RESULT = 5
    EDITOR = 6


class GameEngine:
    """
    游戏引擎
    管理游戏主循环和状态
    """
    
    def __init__(self, app: App):
        logger.info("初始化游戏引擎")
        self.app = app
        self.state = GameState.LOADING
        
        # 时间系统
        self.clock = GameClock()
        
        # 音频系统
        self.audio = AudioManager(config)
        
        # 谱面数据
        self.current_chart: Optional[Chart] = None
        
        # 判定系统
        self.judgment = JudgmentSystem()
        
        # 游玩参数
        self.scroll_speed = config.get('gameplay.scroll_speed', 1.0)
        self.note_size = config.get('gameplay.note_size', 1.0)
        self.lanes = config.get('gameplay.lanes', 4)
        
        # 当前游戏数据
        self.current_time = 0.0
        self.is_playing = False
        self.keys_pressed = [False] * self.lanes
        self._active_key_lanes: Dict[int, int] = {}
        
        # 音符数据
        self.notes: List[Note] = []
        self.note_times: List[float] = []
        self.note_positions: List[float] = []
        self.hold_notes: Dict[int, Dict] = {}

        # Note scan caches (for performance)
        self.note_order_by_time: List[int] = []
        self.miss_scan_cursor = 0
        self.lane_note_indices: Dict[int, List[int]] = {lane: [] for lane in range(self.lanes)}
        self.lane_scan_cursors: Dict[int, int] = {lane: 0 for lane in range(self.lanes)}
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            'on_note_hit': [],
            'on_note_miss': [],
            'on_combo_change': [],
            'on_score_change': [],
            'on_game_start': [],
            'on_game_end': [],
            'on_state_change': []
        }
        
        # UI引用
        self.play_ui: Optional[PlayUI] = None
        
        # 当前谱面文件路径（用于查找背景等资源）
        self.current_chart_path: Optional[Path] = None
        
        # 设置窗口事件
        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)
        # 注释掉触摸事件，让UI自己处理触摸
        # Window.bind(on_touch_down=self._on_touch_down)
        # Window.bind(on_touch_up=self._on_touch_up)
        
        logger.debug(f"游戏参数 - 轨道: {self.lanes}, 滚动速度: {self.scroll_speed}, 音符大小: {self.note_size}")
        
    def load_chart(self, chart: Chart) -> bool:
        """Load chart and prebuild note scan indices."""
        logger.info(f"Loading chart: {chart.metadata.title} - {chart.metadata.artist}")
        logger.debug(f"Note count: {len(chart.notes)}")

        self.current_chart = chart
        self.notes = chart.notes

        self.note_times = []
        self.note_positions = []

        for note in self.notes:
            note_time = chart.timing_system.beat_to_time(note.beat)
            self.note_times.append(note_time)

            if note.endbeat:
                end_time = chart.timing_system.beat_to_time(note.endbeat)
                note.duration = end_time - note_time
            else:
                note.duration = 0.0

        # Build note scan indices once per chart load.
        self.note_order_by_time = sorted(
            range(len(self.notes)),
            key=lambda i: self.note_times[i] if self.note_times[i] is not None else float('inf'),
        )
        self.lane_note_indices = {lane: [] for lane in range(self.lanes)}
        for idx, note in enumerate(self.notes):
            if 0 <= note.column < self.lanes:
                self.lane_note_indices[note.column].append(idx)

        self.reset_game()

        if chart.metadata.audio_path:
            logger.debug(f"Audio file: {chart.metadata.audio_path}")
            audio_loaded = self.audio.load_music(chart.metadata.audio_path)
            if not audio_loaded:
                logger.warning(f"Audio load failed: {chart.metadata.audio_path}")

        logger.info("Chart loaded")
        return True

    def reset_game(self) -> None:
        """Reset gameplay state."""
        logger.info("Reset game state")
        self.current_time = 0.0
        self.is_playing = False
        self.keys_pressed = [False] * self.lanes
        self.judgment.reset()

        self.miss_scan_cursor = 0
        self.lane_scan_cursors = {lane: 0 for lane in range(self.lanes)}

        self.clock.reset()

    def start_game(self) -> None:
        """开始游戏"""
        logger.info("游戏开始")
        if not self.current_chart:
            logger.error("没有加载谱面，无法开始游戏")
            return
            
        self.reset_game()
        
        # 确保音频加载
        if self.current_chart.metadata.audio_path:
            audio_loaded = self.audio.load_music(self.current_chart.metadata.audio_path)
            if not audio_loaded:
                logger.warning("音频加载失败，但继续游戏")
        else:
            logger.warning("没有音频文件")
            
        # 开始音乐播放
        if self.current_chart.metadata.audio_path:
            self.audio.play_music()
            
        self.is_playing = True
        self._trigger_callbacks('on_game_start')
        self.change_state(GameState.PLAYING)
        logger.debug("游戏状态: 游玩中")
        
    def pause_game(self) -> None:
        """暂停游戏"""
        if self.state == GameState.PAUSED:
            logger.debug("游戏已经在暂停状态")
            return
            
        logger.info("游戏暂停")
        if not self.is_playing:
            logger.debug("游戏未在运行中")
            return
            
        self.is_playing = False
        self.clock.pause()
        self.audio.pause_music()
        self.change_state(GameState.PAUSED)
        logger.debug("游戏状态: 暂停")
        
        # 切换到暂停界面
        if hasattr(self, 'app') and self.app and hasattr(self.app, 'screen_manager'):
            logger.info("切换到暂停界面")
            try:
                self.app.screen_manager.current = 'pause'
            except Exception as e:
                logger.error(f"切换到暂停界面失败: {e}")
        else:
            logger.error("无法切换到暂停界面：screen_manager 不可用")
        
    def resume_game(self) -> None:
        """恢复游戏"""
        if self.state == GameState.PLAYING:
            logger.debug("游戏已经在运行状态")
            return
            
        logger.info("游戏恢复")
        
        # 先恢复音乐
        self.audio.resume_music()
        
        # 然后恢复时钟和状态
        self.clock.resume()
        self.is_playing = True
        self.change_state(GameState.PLAYING)
        logger.debug("游戏状态: 游玩中")
        
        # 切换到游玩界面
        if hasattr(self, 'app') and self.app and hasattr(self.app, 'screen_manager'):
            logger.info("切换到游玩界面")
            try:
                self.app.screen_manager.current = 'play'
            except Exception as e:
                logger.error(f"切换到游玩界面失败: {e}")
                
    def end_game(self) -> None:
        """结束游戏"""
        logger.info(f"游戏结束 - 分数: {self.judgment.get_score()}, 准确率: {self.judgment.get_accuracy():.2f}%")
        self.is_playing = False
        self.audio.stop_music()
        self._trigger_callbacks('on_game_end')
        self.change_state(GameState.RESULT)
        logger.debug("游戏状态: 结算")
        
        # 切换到结算界面
        if hasattr(self, 'app') and self.app and hasattr(self.app, 'screen_manager'):
            logger.info("切换到结算界面")
            try:
                self.app.screen_manager.current = 'result'
            except Exception as e:
                logger.error(f"Failed to switch to result screen: {e}")
        else:
            logger.error("无法切换到结算界面：screen_manager 不可用")
            
    def update(self, dt: float) -> None:
        """更新游戏逻辑"""
        # 更新时钟
        self.clock.update(dt)
        
        # 如果不在游玩状态，跳过
        if not self.is_playing or self.state != GameState.PLAYING:
            return
            
        # 更新当前时间
        self.current_time = self.clock.game_time
        
        # 检查游戏是否应该结束（音乐播放完毕）
        if self.current_chart and self.current_chart.metadata.duration:
            if self.current_time >= self.current_chart.metadata.duration + 1.0:
                logger.info("音乐播放完毕，游戏结束")
                self.end_game()
                
        # 更新音符位置和判定
        self._update_notes()
        
        # 更新UI
        if self.play_ui:
            try:
                self.play_ui.update(self.current_time)
            except Exception as e:
                logger.error(f"PlayUI update failed: {e}")
            
    def _update_notes(self) -> None:
        """Update notes with cursor-based scan (avoid full scan each frame)."""
        if not self.current_chart:
            return

        current_time = self.current_time
        judgment_window = 0.12
        judged_notes = self.judgment.judged_notes

        while self.miss_scan_cursor < len(self.note_order_by_time):
            note_idx = self.note_order_by_time[self.miss_scan_cursor]

            if note_idx in judged_notes:
                self.miss_scan_cursor += 1
                continue

            note_time = self.note_times[note_idx]
            if note_time is None:
                self.miss_scan_cursor += 1
                continue

            if current_time <= note_time + judgment_window:
                break

            note = self.notes[note_idx]
            result = self.judgment.judge_note(note, current_time, note_time, True)
            if result:
                judged_notes[note_idx] = result
                self._trigger_callbacks('on_note_miss', result)
                self._trigger_callbacks('on_combo_change', self.judgment.get_combo())
                self._trigger_callbacks('on_score_change', self.judgment.get_score())

            self.miss_scan_cursor += 1

    def handle_input(self, lane: int, pressed: bool) -> None:
        """
        处理输入
        
        Args:
            lane: 轨道编号 (0-3)
            pressed: 是否按下
        """
        if not self.is_playing or self.state != GameState.PLAYING or lane < 0 or lane >= self.lanes:
            return
            
        self.keys_pressed[lane] = pressed
        
        # 处理长按音符
        if not pressed:
            # 松开时检查长按音符
            self._check_hold_release(lane)
        else:
            # 按下时检查所有音符
            self._check_note_hit(lane)
            
    def _check_note_hit(self, lane: int) -> None:
        """Check hit on lane with cursor-based scan."""
        if not self.current_chart:
            return

        current_time = self.current_time
        judgment_window = 0.12
        judged_notes = self.judgment.judged_notes

        lane_notes = self.lane_note_indices.get(lane, [])
        cursor = self.lane_scan_cursors.get(lane, 0)

        while cursor < len(lane_notes):
            note_idx = lane_notes[cursor]

            if note_idx in judged_notes:
                cursor += 1
                continue

            note_time = self.note_times[note_idx]
            if note_time is None:
                cursor += 1
                continue

            # Too late for this note, move cursor forward.
            if current_time > note_time + judgment_window:
                cursor += 1
                continue

            # Next note has not reached judgment window yet.
            if current_time < note_time - judgment_window:
                break

            note = self.notes[note_idx]
            result = self.judgment.judge_note(note, current_time, note_time, False)
            if result:
                judged_notes[note_idx] = result
                if note.type == NoteType.HOLD:
                    self.hold_notes[note_idx] = {
                        'note': note,
                        'start_time': current_time,
                        'pressed': True,
                    }

                self._trigger_callbacks('on_note_hit', result)
                self._trigger_callbacks('on_combo_change', self.judgment.get_combo())
                self._trigger_callbacks('on_score_change', self.judgment.get_score())

                if note.sound:
                    self.audio.play_sound(note.sound, note.volume)

                cursor += 1
                break

            break

        self.lane_scan_cursors[lane] = cursor

    def _check_hold_release(self, lane: int) -> None:
        """检查长按音符释放"""
        current_time = self.current_time
        
        # 检查所有追踪中的长按音符
        for note_idx, hold_info in list(self.hold_notes.items()):
            note = hold_info['note']
            
            # 只检查指定轨道的音符
            if note.column != lane:
                continue
                
            # 如果音符已经结束
            if note.endbeat:
                end_time = self.current_chart.timing_system.beat_to_time(note.endbeat)
                if current_time < end_time and hold_info['pressed']:
                    # 提前松开，判定为MISS
                    result = JudgmentResult(
                        judgment=Judgment.MISS,
                        note=note,
                        offset=0.0,
                        score=0,
                        combo=self.judgment.get_combo(),
                        lane=note.column
                    )
                    
                    # 更新判定
                    if note_idx in self.judgment.judged_notes:
                        self.judgment.judged_notes[note_idx].judgment = Judgment.MISS
                    
                    # 触发回调
                    self._trigger_callbacks('on_note_miss', result)
                    self._trigger_callbacks('on_combo_change', self.judgment.get_combo())
                    self._trigger_callbacks('on_score_change', self.judgment.get_score())
                    
                    # 移除追踪
                    self.hold_notes.pop(note_idx, None)
            
    def change_state(self, new_state: GameState) -> None:
        """改变游戏状态"""
        old_state = self.state
        self.state = new_state
        
        # 触发回调
        self._trigger_callbacks('on_state_change', old_state, new_state)
        
    def register_callback(self, event: str, callback: Callable) -> None:
        """注册回调函数"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            
    def unregister_callback(self, event: str, callback: Callable) -> None:
        """取消注册回调函数"""
        if event in self.callbacks:
            if callback in self.callbacks[event]:
                self.callbacks[event].remove(callback)
                
    def _trigger_callbacks(self, event: str, *args, **kwargs) -> None:
        """Trigger registered callbacks for a given event."""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception:
                    logger.exception(f"Callback execution failed: {event}")

    def _on_key_down(self, window, key, scancode, codepoint, modifiers) -> bool:
        """Handle key down events."""
        lane = self._resolve_lane_from_key_down(key, codepoint)
        if lane is not None:
            self.handle_input(lane, True)
            return True

        if key == 27:  # ESC
            if self.state == GameState.PLAYING:
                self.pause_game()
            elif self.state == GameState.PAUSED:
                self.resume_game()
            return True

        if key == 32:  # SPACE
            if self.state == GameState.PLAYING:
                self.pause_game()
            elif self.state == GameState.PAUSED:
                self.resume_game()
            return True

        return False

    def _on_key_up(self, window, key, scancode) -> bool:
        """Handle key up events."""
        if key in self._active_key_lanes:
            lane = self._active_key_lanes.pop(key)
            self.handle_input(lane, False)
            return True

        key_layout = config.get('gameplay.key_layout', 'standard')
        key_map = self._get_key_map(key_layout)
        for lane, keys in key_map.items():
            if key in keys:
                self.handle_input(lane, False)
                return True

        return False

    def _resolve_lane_from_key_down(self, key: int, codepoint: str) -> Optional[int]:
        """Resolve lane from key-down event using keycode + codepoint fallback."""
        key_layout = config.get('gameplay.key_layout', 'standard')
        key_map = self._get_key_map(key_layout)

        for lane, keys in key_map.items():
            if key in keys:
                self._active_key_lanes[key] = lane
                return lane

        if not codepoint:
            return None

        c = codepoint.lower()
        char_map = self._get_char_map(key_layout)
        lane = char_map.get(c)
        if lane is not None:
            self._active_key_lanes[key] = lane

        return lane

    def _get_key_map(self, layout: str) -> Dict[int, List[int]]:
        """Return lane keycode mapping for current layout."""
        # Standard: D F J K
        if layout == 'standard':
            return {
                0: [100],  # D
                1: [102],  # F
                2: [106],  # J
                3: [107],  # K
            }

        # WASD
        if layout == 'wasd':
            return {
                0: [97],   # A
                1: [119],  # W
                2: [115],  # S
                3: [100],  # D
            }

        # Arrow keys
        if layout == 'arrows':
            return {
                0: [276],  # Left
                1: [273],  # Up
                2: [274],  # Down
                3: [275],  # Right
            }

        # Custom bindings from config
        if layout == 'custom':
            custom_codes: Dict[int, List[int]] = {}
            custom_chars = self._get_custom_bindings_by_lane()
            for lane in range(self.lanes):
                lane_chars = custom_chars.get(lane, [])
                keycodes: List[int] = []
                for ch in lane_chars:
                    if len(ch) == 1:
                        keycodes.append(ord(ch.lower()))
                custom_codes[lane] = keycodes
            return custom_codes

        # Default to standard layout
        return {
            0: [100],
            1: [102],
            2: [106],
            3: [107],
        }

    def _get_char_map(self, layout: str) -> Dict[str, int]:
        """Return character -> lane mapping for current layout."""
        if layout == 'standard':
            return {'d': 0, 'f': 1, 'j': 2, 'k': 3}
        if layout == 'wasd':
            return {'a': 0, 'w': 1, 's': 2, 'd': 3}
        if layout == 'custom':
            custom_chars = self._get_custom_bindings_by_lane()
            char_map: Dict[str, int] = {}
            for lane, chars in custom_chars.items():
                for ch in chars:
                    char_map[ch] = lane
            return char_map
        return {}

    def _get_custom_bindings_by_lane(self) -> Dict[int, List[str]]:
        """Return normalized custom bindings from config."""
        raw = config.get('gameplay.key_bindings', {})
        result: Dict[int, List[str]] = {lane: [] for lane in range(self.lanes)}

        if isinstance(raw, dict):
            for lane in range(self.lanes):
                lane_keys = raw.get(str(lane), raw.get(lane, []))
                if isinstance(lane_keys, str):
                    lane_keys = [lane_keys]
                if not isinstance(lane_keys, list):
                    lane_keys = []

                normalized: List[str] = []
                for key_name in lane_keys:
                    if not isinstance(key_name, str):
                        continue
                    key_name = key_name.strip().lower()
                    if len(key_name) == 1:
                        normalized.append(key_name)

                if normalized:
                    result[lane] = normalized

        # Fallback to standard bindings when custom lane is empty
        fallback = {0: ['d'], 1: ['f'], 2: ['j'], 3: ['k']}
        for lane in range(self.lanes):
            if not result[lane]:
                result[lane] = fallback.get(lane, [])

        return result
