# mystia_rhythm/config.py
"""
配置文件 - 定义常量、路径和默认设置
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 基础路径
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

# 数据目录 - 优先使用项目相对目录，否则使用用户目录
PROJECT_DATA_DIR = BASE_DIR / 'data'

# 如果项目目录存在，使用项目目录；否则使用用户目录
if PROJECT_DATA_DIR.exists() or os.environ.get('DEV_MODE'):
    DATA_DIR = PROJECT_DATA_DIR
else:
    # 用户数据目录（跨平台）
    if sys.platform == 'win32':
        DATA_DIR = Path(os.environ.get('APPDATA', '')) / 'MystiaRhythm'
    elif sys.platform == 'darwin':
        DATA_DIR = Path.home() / 'Library' / 'Application Support' / 'MystiaRhythm'
    elif sys.platform.startswith('linux'):
        DATA_DIR = Path.home() / '.local' / 'share' / 'MystiaRhythm'
    else:
        DATA_DIR = BASE_DIR / 'data'

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    """配置管理类"""
    
    DEFAULTS = {
        'graphics': {
            'resolution': [1280, 720],
            'fullscreen': False,
            'vsync': True,
            'fps_limit': 60,
            'ui_scale': 1.0,
        },
        'audio': {
            'volume_master': 0.8,
            'volume_music': 1.0,
            'volume_effect': 1.0,
            'audio_latency': 0.05,
            'audio_backend': 'auto',
        },
        'gameplay': {
            'judgment_offset': 0,
            'scroll_speed': 2.0,
            'note_size': 1.0,
            'key_layout': 'standard',
            'key_bindings': {
                '0': ['d'],
                '1': ['f'],
                '2': ['j'],
                '3': ['k'],
            },
            'lanes': 4,
        },
        'mods': {
            'enabled_mods': [],
            'mod_load_order': [],
            'allow_unsafe_mods': False,
        },
        'paths': {
            'beatmaps': str(DATA_DIR / 'beatmaps'),
            'mods': str(DATA_DIR / 'mods'),
            'cache': str(DATA_DIR / 'cache'),
            'scores': str(DATA_DIR / 'scores'),
            'skins': str(DATA_DIR / 'skins'),
            'saves': str(DATA_DIR / 'saves'),
        },
        'skin': {
            'current_skin': 'default',
            'note_style': 'circle',
            'judge_line_style': 'default',
            'ui_theme': 'dark',
        }
    }
    
    def __init__(self):
        self.config_path = DATA_DIR / 'config.json'
        self.settings = {}
        self._deep_copy(self.DEFAULTS, self.settings)
        self.load()
        
    def _deep_copy(self, source: Dict, target: Dict) -> None:
        """深度复制字典"""
        for key, value in source.items():
            if isinstance(value, dict):
                target[key] = {}
                self._deep_copy(value, target[key])
            else:
                target[key] = value
        
    def load(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._deep_update(self.settings, loaded)
            except (json.JSONDecodeError, IOError) as e:
                print(f"配置文件加载失败: {e}")
                
    def save(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"配置文件保存失败: {e}")
            
    def get(self, key: str, default=None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
        
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        target = self.settings
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
            
        target[keys[-1]] = value
        self.save()
        
    def _deep_update(self, target: Dict, source: Dict) -> None:
        """深度更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
                
    def get_path(self, path_type: str) -> Path:
        """获取路径"""
        path_str = self.get(f'paths.{path_type}')
        if path_str:
            path = Path(path_str)
        else:
            path = DATA_DIR / path_type
            
        path.mkdir(parents=True, exist_ok=True)
        return path


# 全局配置实例
config = Config()

# 导出常量
BEATMAP_DIR = config.get_path('beatmaps')
MOD_DIR = config.get_path('mods')
CACHE_DIR = config.get_path('cache')
SCORES_DIR = config.get_path('scores')
SKINS_DIR = config.get_path('skins')
SAVES_DIR = config.get_path('saves')
