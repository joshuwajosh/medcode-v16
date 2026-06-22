"""
MedCode AI V19 — Coder Performance Analytics
=============================================
AAPC Module 8: Customized Training and Feedback
- Tracks coder accuracy over time
- Identifies weak areas for training
- Provides personalized feedback
- Trend analysis for continuous improvement
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import time
import json
import os


@dataclass
class CoderSession:
    """A single coding session record."""
    session_id: str = ""
    coder_id: str = ""
    note_text_hash: str = ""
    specialty: str = ""
    codes_generated: List[Dict] = field(default_factory=list)
    codes_confirmed: List[Dict] = field(default_factory=list)
    codes_corrected: List[Dict] = field(default_factory=list)
    accuracy_score: float = 0.0
    processing_time_ms: float = 0.0
    timestamp: float = 0.0


@dataclass
class CoderPerformance:
    """Aggregated coder performance metrics."""
    coder_id: str = ""
    total_sessions: int = 0
    average_accuracy: float = 0.0
    accuracy_trend: str = "stable"  # improving, declining, stable
    specialty_accuracy: Dict[str, float] = field(default_factory=dict)
    weak_areas: List[Dict] = field(default_factory=list)
    strong_areas: List[Dict] = field(default_factory=list)
    total_corrections: int = 0
    common_errors: List[Dict] = field(default_factory=list)
    training_recommendations: List[str] = field(default_factory=list)


@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    metric: str = ""
    current_value: float = 0.0
    previous_value: float = 0.0
    change_percent: float = 0.0
    trend_direction: str = "stable"  # up, down, stable
    period: str = "30d"


class CoderPerformanceTracker:
    """
    Tracks and analyzes coder performance over time.
    Provides personalized training recommendations.
    """

    def __init__(self, data_dir: str = "data"):
        self._data_dir = data_dir
        self._sessions: List[CoderSession] = []
        self._load_sessions()

    def _load_sessions(self):
        path = os.path.join(self._data_dir, "coder_sessions.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                self._sessions = [CoderSession(**s) for s in data]
            except (json.JSONDecodeError, IOError):
                pass

    def _save_sessions(self):
        os.makedirs(self._data_dir, exist_ok=True)
        path = os.path.join(self._data_dir, "coder_sessions.json")
        with open(path, "w") as f:
            json.dump([s.__dict__ for s in self._sessions], f, indent=2)

    def record_session(self, session: CoderSession):
        """Record a coding session."""
        session.timestamp = time.time()
        self._sessions.append(session)
        self._save_sessions()

    def get_performance(self, coder_id: str, days: int = 30) -> CoderPerformance:
        """Get aggregated performance for a coder."""
        cutoff = time.time() - (days * 86400)
        sessions = [
            s for s in self._sessions
            if s.coder_id == coder_id and s.timestamp >= cutoff
        ]

        if not sessions:
            return CoderPerformance(coder_id=coder_id)

        total = len(sessions)
        avg_accuracy = sum(s.accuracy_score for s in sessions) / total

        # Specialty breakdown
        specialty_scores: Dict[str, List[float]] = defaultdict(list)
        for s in sessions:
            specialty_scores[s.specialty].append(s.accuracy_score)
        specialty_accuracy = {
            sp: sum(scores) / len(scores)
            for sp, scores in specialty_scores.items()
        }

        # Identify weak/strong areas
        weak_areas = []
        strong_areas = []
        for sp, acc in specialty_accuracy.items():
            if acc < 0.70:
                weak_areas.append({"specialty": sp, "accuracy": round(acc, 3)})
            elif acc > 0.90:
                strong_areas.append({"specialty": sp, "accuracy": round(acc, 3)})

        # Common errors
        error_counts: Dict[str, int] = defaultdict(int)
        for s in sessions:
            for correction in s.codes_corrected:
                error_type = correction.get("error_type", "unknown")
                error_counts[error_type] += 1
        common_errors = [
            {"error_type": k, "count": v}
            for k, v in sorted(error_counts.items(), key=lambda x: -x[1])[:5]
        ]

        # Training recommendations
        recommendations = []
        if avg_accuracy < 0.80:
            recommendations.append("Focus on overall coding accuracy improvement")
        for area in weak_areas:
            recommendations.append(
                f"Additional training recommended for {area['specialty']}"
            )
        if len(sessions) < 10:
            recommendations.append("Complete more coding sessions for reliable metrics")

        # Accuracy trend
        if len(sessions) >= 10:
            mid = len(sessions) // 2
            first_half = sum(s.accuracy_score for s in sessions[:mid]) / mid
            second_half = sum(s.accuracy_score for s in sessions[mid:]) / (len(sessions) - mid)
            if second_half - first_half > 0.05:
                trend = "improving"
            elif first_half - second_half > 0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return CoderPerformance(
            coder_id=coder_id,
            total_sessions=total,
            average_accuracy=round(avg_accuracy, 3),
            accuracy_trend=trend,
            specialty_accuracy={k: round(v, 3) for k, v in specialty_accuracy.items()},
            weak_areas=weak_areas,
            strong_areas=strong_areas,
            total_corrections=sum(len(s.codes_corrected) for s in sessions),
            common_errors=common_errors,
            training_recommendations=recommendations,
        )

    def get_trends(self, days: int = 30) -> List[TrendAnalysis]:
        """Analyze trends across all coders."""
        cutoff = time.time() - (days * 86400)
        recent = [s for s in self._sessions if s.timestamp >= cutoff]
        older = [s for s in self._sessions if s.timestamp < cutoff]

        trends = []

        if recent and older:
            recent_acc = sum(s.accuracy_score for s in recent) / len(recent)
            older_acc = sum(s.accuracy_score for s in older) / len(older)

            change = ((recent_acc - older_acc) / older_acc * 100) if older_acc > 0 else 0
            direction = "up" if change > 2 else ("down" if change < -2 else "stable")

            trends.append(TrendAnalysis(
                metric="overall_accuracy",
                current_value=round(recent_acc, 3),
                previous_value=round(older_acc, 3),
                change_percent=round(change, 1),
                trend_direction=direction,
                period=f"{days}d",
            ))

        # Specialty trends
        specialty_recent: Dict[str, List[float]] = defaultdict(list)
        for s in recent:
            specialty_recent[s.specialty].append(s.accuracy_score)

        for sp, scores in specialty_recent.items():
            avg = sum(scores) / len(scores)
            trends.append(TrendAnalysis(
                metric=f"accuracy_{sp}",
                current_value=round(avg, 3),
                trend_direction="up" if avg > 0.85 else ("down" if avg < 0.70 else "stable"),
                period=f"{days}d",
            ))

        return trends


from collections import defaultdict

class TrendAnalyzer:
    """
    Analyzes coding trends and patterns.
    Identifies opportunities for improvement.
    """

    def analyze_coding_patterns(self, sessions: List[Dict]) -> Dict:
        """Analyze coding patterns across sessions."""
        if not sessions:
            return {"error": "No sessions to analyze"}

        # Code frequency analysis
        code_freq: Dict[str, int] = defaultdict(int)
        specialty_freq: Dict[str, int] = defaultdict(int)
        error_types: Dict[str, int] = defaultdict(int)

        for session in sessions:
            specialty_freq[session.get("specialty", "unknown")] += 1
            for code in session.get("codes_generated", []):
                code_freq[code.get("code", "")] += 1
            for correction in session.get("codes_corrected", []):
                error_types[correction.get("error_type", "unknown")] += 1

        # Top codes
        top_codes = sorted(code_freq.items(), key=lambda x: -x[1])[:20]

        # Top specialties
        top_specialties = sorted(specialty_freq.items(), key=lambda x: -x[1])[:10]

        # Error patterns
        top_errors = sorted(error_types.items(), key=lambda x: -x[1])[:10]

        # Accuracy by specialty
        specialty_accuracy = {}
        for session in sessions:
            sp = session.get("specialty", "unknown")
            if sp not in specialty_accuracy:
                specialty_accuracy[sp] = []
            specialty_accuracy[sp].append(session.get("accuracy_score", 0))

        avg_by_specialty = {
            sp: round(sum(scores) / len(scores), 3)
            for sp, scores in specialty_accuracy.items()
        }

        return {
            "total_sessions": len(sessions),
            "top_codes": top_codes,
            "top_specialties": top_specialties,
            "top_errors": top_errors,
            "accuracy_by_specialty": avg_by_specialty,
        }


def generate_training_plan(performance: CoderPerformance) -> Dict:
    """Generate a personalized training plan based on performance."""
    plan = {
        "coder_id": performance.coder_id,
        "priority_areas": [],
        "recommended_modules": [],
        "practice_cases": [],
        "timeline": "30 days",
    }

    # Priority areas based on weak spots
    for area in performance.weak_areas:
        plan["priority_areas"].append({
            "specialty": area["specialty"],
            "current_accuracy": area["accuracy"],
            "target_accuracy": 0.85,
            "gap": round(0.85 - area["accuracy"], 3),
        })

    # Module recommendations
    if performance.average_accuracy < 0.70:
        plan["recommended_modules"].extend([
            "AAPC Module 1: AI in Healthcare Basics",
            "AAPC Module 2: NLP and Medical Coding",
            "AAPC Module 4: Enhancing Coding Accuracy",
        ])
    elif performance.average_accuracy < 0.85:
        plan["recommended_modules"].extend([
            "AAPC Module 3: Continuous Learning",
            "AAPC Module 4: Enhancing Coding Accuracy",
        ])

    for area in performance.weak_areas:
        sp = area["specialty"]
        if "cardiac" in sp.lower():
            plan["recommended_modules"].append("Cardiac Surgery Coding Review")
        elif "ortho" in sp.lower():
            plan["recommended_modules"].append("Orthopedic Coding Review")
        elif "em" in sp.lower() or "emergency" in sp.lower():
            plan["recommended_modules"].append("E/M Coding Mastery")

    # Practice recommendations
    if performance.total_sessions < 50:
        plan["practice_cases"].append("Complete 50+ coding sessions for statistical significance")

    for error in performance.common_errors[:3]:
        plan["practice_cases"].append(
            f"Practice cases targeting: {error['error_type']} (occurred {error['count']} times)"
        )

    return plan
