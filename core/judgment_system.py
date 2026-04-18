from dataclasses import dataclass
from enum import Enum
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class Judgment(Enum):
    """Judgment tiers."""

    BEST = "BEST"
    COOL = "COOL"
    GOOD = "GOOD"
    MISS = "MISS"


@dataclass
class JudgmentResult:
    """Single note judgment result."""

    judgment: Judgment
    offset: float
    score: int
    combo: int
    lane: Optional[int] = None
    note: Optional[Any] = None

    # Backward compatibility for old code paths that still read/write time_diff.
    @property
    def time_diff(self) -> float:
        return self.offset

    @time_diff.setter
    def time_diff(self, value: float) -> None:
        self.offset = value


class ScoreCalculator:
    """Score and combo state accumulator."""

    def __init__(self) -> None:
        self.total_notes = 0
        self.max_combo = 0
        self.current_combo = 0
        self.total_score = 0
        self.judgment_counts: Dict[str, int] = {
            Judgment.BEST.value: 0,
            Judgment.COOL.value: 0,
            Judgment.GOOD.value: 0,
            Judgment.MISS.value: 0,
        }

    def calculate_judgment(self, abs_offset_seconds: float) -> Judgment:
        """Map absolute offset (seconds) to a judgment tier."""
        abs_offset_ms = abs_offset_seconds * 1000.0

        if abs_offset_ms <= 20:
            return Judgment.BEST
        if abs_offset_ms <= 35:
            return Judgment.COOL
        if abs_offset_ms <= 60:
            return Judgment.GOOD
        return Judgment.MISS

    def add_judgment(self, judgment: Judgment) -> JudgmentResult:
        """Apply a new judgment to score/combo counters."""
        self.total_notes += 1

        if judgment == Judgment.MISS:
            self.current_combo = 0
            score = 0
        else:
            self.current_combo += 1
            self.max_combo = max(self.max_combo, self.current_combo)
            if judgment == Judgment.BEST:
                score = 1000
            elif judgment == Judgment.COOL:
                score = 800
            else:
                score = 500

        self.total_score += score
        self.judgment_counts[judgment.value] += 1

        return JudgmentResult(
            judgment=judgment,
            offset=0.0,
            score=score,
            combo=self.current_combo,
        )

    def update_counts(self, judgment: Judgment) -> JudgmentResult:
        """Backward-compatible alias."""
        return self.add_judgment(judgment)

    def get_accuracy(self) -> float:
        """Return weighted accuracy in percent."""
        if self.total_notes == 0:
            return 100.0

        total_points = (
            self.judgment_counts[Judgment.BEST.value] * 1.0
            + self.judgment_counts[Judgment.COOL.value] * 0.8
            + self.judgment_counts[Judgment.GOOD.value] * 0.5
        )
        return (total_points / float(self.total_notes)) * 100.0

    def get_score(self) -> int:
        return self.total_score

    def get_combo(self) -> int:
        return self.current_combo

    def reset(self) -> None:
        self.total_notes = 0
        self.max_combo = 0
        self.current_combo = 0
        self.total_score = 0
        self.judgment_counts = {
            Judgment.BEST.value: 0,
            Judgment.COOL.value: 0,
            Judgment.GOOD.value: 0,
            Judgment.MISS.value: 0,
        }


class JudgmentSystem:
    """Gameplay judgment facade used by game engine."""

    def __init__(self) -> None:
        self.calculator = ScoreCalculator()
        self.windows = {
            Judgment.BEST.value: 20,
            Judgment.COOL.value: 35,
            Judgment.GOOD.value: 60,
            Judgment.MISS.value: 120,
        }
        self.judged_notes: Dict[int, JudgmentResult] = {}

    def judge_note(
        self,
        note: Optional[Any],
        current_time: float,
        note_time: float,
        is_auto_miss: bool = False,
    ) -> Optional[JudgmentResult]:
        """Judge one note event and return a structured result."""
        try:
            offset = 0.0 if note_time is None else (current_time - note_time)

            if is_auto_miss:
                judgment = Judgment.MISS
            else:
                judgment = self.calculator.calculate_judgment(abs(offset))

            result = self.calculator.add_judgment(judgment)
            result.offset = offset
            result.note = note
            result.lane = note.column if hasattr(note, "column") else None
            return result
        except Exception:
            logger.exception("Error while judging note")
            return None

    def get_accuracy(self) -> float:
        return self.calculator.get_accuracy()

    def get_score(self) -> int:
        return self.calculator.get_score()

    def get_combo(self) -> int:
        return self.calculator.get_combo()

    def reset(self) -> None:
        self.calculator.reset()
        self.judged_notes.clear()
