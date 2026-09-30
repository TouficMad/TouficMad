"""Call Detail Record model and SIP response classification."""
from dataclasses import dataclass

ANSWERED = 200
# Final responses caused by the called party, not by the network.
# They count as "effective" for NER even though the call was not answered.
USER_CAUSED = {480, 486, 487, 603}


@dataclass(frozen=True)
class CDR:
    timestamp: float
    carrier: str
    destination: str
    sip_code: int
    pdd: float  # post-dial delay in seconds (INVITE -> first ringing/answer)
    duration: float = 0.0  # billable seconds, 0 if not answered

    @property
    def answered(self) -> bool:
        return self.sip_code == ANSWERED

    @property
    def network_effective(self) -> bool:
        return self.answered or self.sip_code in USER_CAUSED

    @classmethod
    def from_row(cls, row: dict) -> "CDR":
        return cls(
            timestamp=float(row["timestamp"]),
            carrier=row["carrier"],
            destination=row["destination"],
            sip_code=int(row["sip_code"]),
            pdd=float(row["pdd"]),
            duration=float(row.get("duration") or 0),
        )
