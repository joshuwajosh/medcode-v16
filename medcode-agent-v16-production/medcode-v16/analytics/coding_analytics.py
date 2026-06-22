"""
Enterprise Analytics Engine V17.
Tracks coding accuracy trends, denial trends, specialty distribution,
modifier usage, physician query frequency, documentation deficiency trends.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json
import os
import time
from collections import defaultdict


@dataclass
class AnalyticsSnapshot:
    timestamp: float = 0.0
    total_codes: int = 0
    approved_count: int = 0
    denied_count: int = 0
    avg_confidence: float = 0.0
    specialty_distribution: Dict[str, int] = field(default_factory=dict)
    modifier_usage: Dict[str, int] = field(default_factory=dict)
    query_count: int = 0
    doc_gap_count: int = 0
    top_denial_reasons: List[str] = field(default_factory=list)


class CodingAnalyticsEngine:
    """Deterministic analytics engine for tracking coding trends."""

    def __init__(self, storage_path: str = ""):
        self._storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "analytics.json"
        )
        self._snapshots: List[AnalyticsSnapshot] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path) as f:
                    data = json.load(f)
                    for item in data.get("snapshots", []):
                        self._snapshots.append(AnalyticsSnapshot(**item))
        except Exception:
            pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            with open(self._storage_path, "w") as f:
                json.dump({
                    "snapshots": [s.__dict__ for s in self._snapshots[-1000:]],
                }, f, indent=2)
        except Exception:
            pass

    def record_snapshot(self, snapshot: AnalyticsSnapshot):
        snapshot.timestamp = snapshot.timestamp or time.time()
        self._snapshots.append(snapshot)
        self._save()

    def get_accuracy_trend(self, window: int = 7) -> List[float]:
        """Get approval rate trend over the last N snapshots."""
        recent = self._snapshots[-window:]
        return [
            s.approved_count / max(s.approved_count + s.denied_count, 1)
            for s in recent
        ]

    def get_specialty_distribution(self) -> Dict[str, int]:
        """Get aggregated specialty distribution."""
        dist: Dict[str, int] = defaultdict(int)
        for s in self._snapshots[-50:]:
            for specialty, count in s.specialty_distribution.items():
                dist[specialty] += count
        return dict(dist)

    def get_modifier_usage_stats(self) -> Dict[str, int]:
        """Get modifier usage statistics."""
        usage: Dict[str, int] = defaultdict(int)
        for s in self._snapshots[-50:]:
            for mod, count in s.modifier_usage.items():
                usage[mod] += count
        return dict(usage)

    def get_denial_reasons(self) -> List[str]:
        """Get aggregated top denial reasons."""
        reasons: Dict[str, int] = defaultdict(int)
        for s in self._snapshots[-50:]:
            for reason in s.top_denial_reasons:
                reasons[reason] += 1
        return sorted(reasons, key=reasons.get, reverse=True)[:10]

    def get_dashboard_data(self) -> dict:
        """Get complete analytics dashboard data."""
        return {
            "total_snapshots": len(self._snapshots),
            "accuracy_trend": self.get_accuracy_trend(),
            "specialty_distribution": self.get_specialty_distribution(),
            "modifier_usage": self.get_modifier_usage_stats(),
            "top_denial_reasons": self.get_denial_reasons(),
            "recent": [
                {
                    "timestamp": s.timestamp,
                    "total_codes": s.total_codes,
                    "avg_confidence": s.avg_confidence,
                    "query_count": s.query_count,
                    "doc_gap_count": s.doc_gap_count,
                }
                for s in self._snapshots[-10:]
            ],
        }
