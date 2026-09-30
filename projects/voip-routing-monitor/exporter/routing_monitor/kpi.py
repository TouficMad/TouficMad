"""Sliding-window KPI calculation and least-cost routing with quality thresholds."""
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass

from .cdr import CDR


@dataclass
class RouteKPI:
    carrier: str
    destination: str
    attempts: int
    asr: float  # answer seizure ratio: answered / attempts
    ner: float  # network effectiveness ratio: (answered + user-caused) / attempts
    acd: float  # average call duration of answered calls, seconds
    pdd: float  # average post-dial delay, seconds

    def to_dict(self):
        return {k: round(v, 4) if isinstance(v, float) else v for k, v in asdict(self).items()}


def compute_kpi(carrier: str, destination: str, cdrs) -> RouteKPI:
    cdrs = list(cdrs)
    attempts = len(cdrs)
    if attempts == 0:
        return RouteKPI(carrier, destination, 0, 0.0, 0.0, 0.0, 0.0)
    answered = [c for c in cdrs if c.answered]
    return RouteKPI(
        carrier=carrier,
        destination=destination,
        attempts=attempts,
        asr=len(answered) / attempts,
        ner=sum(c.network_effective for c in cdrs) / attempts,
        acd=sum(c.duration for c in answered) / len(answered) if answered else 0.0,
        pdd=sum(c.pdd for c in cdrs) / attempts,
    )


class KPIWindow:
    """Keeps the CDRs of the last `window_seconds` per (carrier, destination)."""

    def __init__(self, window_seconds: float = 300, clock=time.time):
        self.window = window_seconds
        self.clock = clock
        self._cdrs = defaultdict(deque)
        self._lock = threading.Lock()

    def add(self, cdr: CDR) -> None:
        with self._lock:
            self._cdrs[(cdr.carrier, cdr.destination)].append(cdr)

    def _expire(self, now: float) -> None:
        cutoff = now - self.window
        for q in self._cdrs.values():
            while q and q[0].timestamp < cutoff:
                q.popleft()

    def kpis(self) -> list:
        with self._lock:
            self._expire(self.clock())
            return [compute_kpi(c, d, q) for (c, d), q in sorted(self._cdrs.items())]


def rank_routes(kpis, costs: dict, thresholds: dict, min_attempts: int = 20) -> dict:
    """Least-cost routing with a quality floor.

    For every destination, carriers meeting the ASR/PDD thresholds are ordered by
    price (cheapest first). Carriers that fail are listed afterwards as blocked,
    with the reasons, so the routing team can see why.
    """
    by_dest = defaultdict(list)
    for k in kpis:
        by_dest[k.destination].append(k)

    plan = {}
    for dest, routes in sorted(by_dest.items()):
        eligible, blocked = [], []
        for k in routes:
            cost = costs.get(k.carrier, {}).get(dest)
            reasons = []
            if k.attempts < min_attempts:
                reasons.append(f"not enough traffic ({k.attempts} < {min_attempts} calls)")
            else:
                if k.asr < thresholds["min_asr"]:
                    reasons.append(f"ASR {k.asr:.0%} < {thresholds['min_asr']:.0%}")
                if k.pdd > thresholds["max_pdd"]:
                    reasons.append(f"PDD {k.pdd:.1f}s > {thresholds['max_pdd']}s")
            if cost is None:
                reasons.append("no rate configured")
            entry = {**k.to_dict(), "cost_per_min": cost}
            if reasons:
                blocked.append({**entry, "reasons": reasons})
            else:
                eligible.append(entry)
        eligible.sort(key=lambda e: (e["cost_per_min"], -e["asr"]))
        for priority, entry in enumerate(eligible, start=1):
            entry["priority"] = priority
        plan[dest] = {"routes": eligible, "blocked": blocked}
    return plan
