"""Generates realistic synthetic CDRs so the stack can be demoed without a switch."""
import random
import threading
import time

from .cdr import CDR

FAILURE_CODES = [
    (486, 0.45),  # busy
    (480, 0.30),  # no answer
    (487, 0.10),  # caller hung up before answer
    (503, 0.10),  # service unavailable (network)
    (404, 0.05),  # number not found
]


class Simulator:
    def __init__(self, config: dict, seed: int = None):
        self.profiles = config["carriers"]
        self.rng = random.Random(seed)
        self._incidents = {}  # carrier -> degradation dict
        self._lock = threading.Lock()

    # ---- incident injection (for demoing alerts) ----
    def set_incident(self, carrier: str, asr_drop: float = 0.4, extra_pdd: float = 6.0):
        if carrier not in self.profiles:
            raise KeyError(carrier)
        with self._lock:
            self._incidents[carrier] = {"asr_drop": asr_drop, "extra_pdd": extra_pdd}

    def clear_incident(self, carrier: str):
        with self._lock:
            self._incidents.pop(carrier, None)

    def incidents(self) -> dict:
        with self._lock:
            return dict(self._incidents)

    # ---- CDR generation ----
    def generate(self, now: float = None) -> CDR:
        now = time.time() if now is None else now
        carrier = self.rng.choice(sorted(self.profiles))
        profile = self.profiles[carrier]
        destination = self.rng.choice(sorted(profile["destinations"]))
        base = profile["destinations"][destination]

        incident = self.incidents().get(carrier, {})
        asr = max(0.0, base["asr"] - incident.get("asr_drop", 0.0))
        pdd = max(0.5, self.rng.gauss(base["pdd"] + incident.get("extra_pdd", 0.0), 0.8))

        if self.rng.random() < asr:
            duration = max(1.0, self.rng.expovariate(1 / base["acd"]))
            return CDR(now, carrier, destination, 200, pdd, duration)

        # During an incident most failures are network congestion.
        if incident and self.rng.random() < 0.6:
            code = 503
        else:
            codes, weights = zip(*FAILURE_CODES)
            code = self.rng.choices(codes, weights)[0]
        return CDR(now, carrier, destination, code, pdd, 0.0)

    def run(self, sink, calls_per_second: float, stop: threading.Event):
        interval = 1.0 / calls_per_second
        while not stop.is_set():
            sink(self.generate())
            stop.wait(self.rng.expovariate(1 / interval))
