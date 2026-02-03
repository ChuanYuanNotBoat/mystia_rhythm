# mystia_rhythm/core/judgment_system.py
"""
判定系统 - 修复KeyError
"""
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Judgment(Enum):
    """判定等级"""
    BEST = "BEST"
    COOL = "COOL" 
    GOOD = "GOOD"
    MISS = "MISS"


@dataclass
class JudgmentResult:
    """判定结果"""
    judgment: Judgment
    offset: float  # 偏移（毫秒）
    score: int
    combo: int
    lane: Optional[int] = None
    note: Optional[object] = None


class ScoreCalculator:
    """分数计算器"""
    
    def __init__(self):
        self.total_notes = 0
        self.max_combo = 0
        self.current_combo = 0
        self.total_score = 0
        self.judgment_counts: Dict[str, int] = {
            "BEST": 0,
            "COOL": 0,
            "GOOD": 0,
            "MISS": 0
        }
        
    def add_judgment(self, judgment: Judgment) -> JudgmentResult:
        """添加判定"""
        self.total_notes += 1
        
        # 更新连击
        if judgment == Judgment.MISS:
            self.current_combo = 0
        else:
            self.current_combo += 1
            self.max_combo = max(self.max_combo, self.current_combo)
            
        # 计算分数
        if judgment == Judgment.BEST:
            score = 1000
        elif judgment == Judgment.COOL:
            score = 800
        elif judgment == Judgment.GOOD:
            score = 500
        else:  # MISS
            score = 0
            
        self.total_score += score
        
        # 更新判定计数
        self.judgment_counts[judgment.value] += 1
        
        return JudgmentResult(
            judgment=judgment,
            offset=0.0,
            score=score,
            combo=self.current_combo
        )

    def update_counts(self, judgment: Judgment) -> JudgmentResult:
        """兼容旧接口，更新判定统计"""
        return self.add_judgment(judgment)
        
    def get_accuracy(self) -> float:
        """计算准确率"""
        if self.total_notes == 0:
            return 100.0
            
        total_points = self.judgment_counts["BEST"] * 1.0 + \
                      self.judgment_counts["COOL"] * 0.8 + \
                      self.judgment_counts["GOOD"] * 0.5
        max_points = self.total_notes * 1.0
        
        return (total_points / max_points) * 100.0
        
    def get_score(self) -> int:
        """获取总分"""
        return self.total_score
        
    def get_combo(self) -> int:
        """获取当前连击"""
        return self.current_combo
        
    def reset(self) -> None:
        """重置计算器"""
        self.total_notes = 0
        self.max_combo = 0
        self.current_combo = 0
        self.total_score = 0
        self.judgment_counts = {
            "BEST": 0,
            "COOL": 0,
            "GOOD": 0,
            "MISS": 0
        }


class JudgmentSystem:
    """判定系统"""
    
    def __init__(self):
        self.calculator = ScoreCalculator()
        self.windows = {
            "BEST": 20,   # ±20ms
            "COOL": 40,   # ±40ms
            "GOOD": 80,   # ±80ms
            "MISS": 120   # ±120ms
        }
        self.judged_notes = {}
        
    def judge_note(self, note, current_time: float, note_time: float, pressed: bool = True) -> Optional[JudgmentResult]:
        """判定音符"""
        if not pressed:
            return None
            
        # 计算时间差（毫秒）
        time_diff = abs(current_time - note_time) * 1000
        
        # 确定判定等级
        judgment = Judgment.MISS
        if time_diff <= self.windows["BEST"]:
            judgment = Judgment.BEST
        elif time_diff <= self.windows["COOL"]:
            judgment = Judgment.COOL
        elif time_diff <= self.windows["GOOD"]:
            judgment = Judgment.GOOD
            
        # 创建判定结果
        result = self.calculator.add_judgment(judgment)
        result.offset = time_diff
        result.note = note
        if hasattr(note, "column"):
            result.lane = note.column
        
        return result
        
    def get_accuracy(self) -> float:
        """获取准确率"""
        return self.calculator.get_accuracy()
        
    def get_score(self) -> int:
        """获取分数"""
        return self.calculator.get_score()
        
    def get_combo(self) -> int:
        """获取连击"""
        return self.calculator.get_combo()
        
    def reset(self) -> None:
        """重置判定系统"""
        self.calculator.reset()
        self.judged_notes.clear()
