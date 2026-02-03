# mystia_rhythm/main.py
"""
主程序入口
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到sys.path
sys.path.insert(0, str(Path(__file__).parent))

# 配置递归深度
sys.setrecursionlimit(10000)

# 导入日志配置
from log_config import logger

logger.info("应用启动初始化")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.clock import Clock

# 导入配置
from config import config
from core.game_engine import GameEngine
from ui.menu import MenuScreen
from ui.song_select import SongSelectScreen
from ui.play_ui import PlayUI
from ui.pause_screen import PauseScreen
from ui.result_ui import ResultScreen
from ui.settings_screen import SettingsScreen

class MystiaRhythmApp(App):
    """主应用类"""
    
    def __init__(self, **kwargs):
        logger.info("=" * 60)
        logger.info("Mystia Rhythm 应用启动")
        logger.info("=" * 60)
        
        super().__init__(**kwargs)
        self.game_engine = None
        self.screen_manager = None
        
    def build(self):
        """构建应用界面"""
        logger.info("构建应用界面")
        
        try:
            # 设置窗口
            resolution = config.get('graphics.resolution', [1280, 720])
            Window.size = tuple(resolution)
            Window.title = 'Mystia Rhythm'
            
            if config.get('graphics.fullscreen', False):
                Window.fullscreen = 'auto'
                
            # 创建游戏引擎
            self.game_engine = GameEngine(self)
            
            # 创建屏幕管理器
            self.screen_manager = ScreenManager(transition=FadeTransition())
            
            # 创建各个屏幕
            menu_screen = MenuScreen(
                game_engine=self.game_engine
            )
            menu_screen.name = 'menu'
            
            song_select_screen = SongSelectScreen(
                game_engine=self.game_engine
            )
            song_select_screen.name = 'song_select'
            
            play_screen = PlayUI(
                game_engine=self.game_engine
            )
            play_screen.name = 'play'
            self.game_engine.play_ui = play_screen
            
            pause_screen = PauseScreen(
                game_engine=self.game_engine
            )
            pause_screen.name = 'pause'
            
            result_screen = ResultScreen(
                game_engine=self.game_engine
            )
            result_screen.name = 'result'
            
            # 修复：实例化SettingsScreen而不是直接添加类
            settings_screen = SettingsScreen(
                game_engine=self.game_engine
            )
            settings_screen.name = 'settings'
            
            # 添加屏幕
            self.screen_manager.add_widget(menu_screen)
            self.screen_manager.add_widget(song_select_screen)
            self.screen_manager.add_widget(play_screen)
            self.screen_manager.add_widget(pause_screen)
            self.screen_manager.add_widget(result_screen)
            self.screen_manager.add_widget(settings_screen)  # 修复：添加实例
            # 设置初始屏幕为菜单
            self.screen_manager.current = 'menu'
            
            # 启动游戏引擎更新循环
            Clock.schedule_interval(self.game_engine.update, 1.0 / 60.0)
            
            logger.info("应用构建完成")
            return self.screen_manager
        except Exception as e:
            logger.error(f"应用构建失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
    def on_start(self):
        """应用启动时调用"""
        logger.info("应用已启动")
        
    def on_stop(self):
        """应用停止时调用"""
        logger.info("应用停止中...")
        
        # 保存配置
        config.save()
        
        logger.info("=" * 60)
        logger.info("Mystia Rhythm 应用已关闭")
        logger.info("=" * 60)


def main():
    """主函数"""
    try:
        logger.info(f"项目根目录: {Path(__file__).parent}")
        
        # 在main.py的main()函数中，修改字体配置部分：
        try:
            from kivy.core.text import LabelBase
            from kivy.config import Config
            
            # 使用项目中字体
            font_dir = Path(__file__).parent / 'assets' / 'fonts'
            font_path = font_dir / 'SourceHanSansSC-Regular.otf'
            
            if font_path.exists():
                # 注册字体
                LabelBase.register(name='DefaultFont', fn_regular=str(font_path))
                # 设置默认字体
                Config.set('kivy', 'default_font', ['DefaultFont', 'SourceHanSansSC-Regular', 'Roboto', 'Arial', 'symbola'])
                logger.info(f"使用自定义字体: {font_path}")
            else:
                # 使用系统默认字体，但添加中文字体支持
                logger.warning(f"字体文件不存在: {font_path}")
                Config.set('kivy', 'default_font', ['Roboto', 'Arial', 'symbola'])
                logger.info("使用系统默认字体")
                
        except Exception as e:
            logger.warning(f"字体配置失败: {e}")
            # 设置默认字体
            Config.set('kivy', 'default_font', ['Roboto', 'Arial', 'symbola'])      
        
        logger.info("启动Kivy应用")
        MystiaRhythmApp().run()
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()