from dataclasses import dataclass, field


DISPOSITIONS = (
    "ALLOW",
    "ALLOW WITH LIMITS",
    "REQUIRE APPROVAL",
    "ESCALATE",
    "HOLD",
    "BLOCK",
)


@dataclass
class Action:
    case_id: str
    kind: str
    requester: str
    authority: bool
    counterparty: str
    counterparty_known: bool
    amount: int
    limit: int
    evidence_complete: bool
    intent: str


@dataclass
class Line:
    round_n: int
    speaker: str
    text: str


@dataclass
class Receipt:
    case_id: str
    disposition: str
    stopped_by: str | None
    votes: dict[str, str]
    chair: str
    lines: list[Line] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "disposition": self.disposition,
            "stopped_by": self.stopped_by,
            "votes": self.votes,
            "chair": self.chair,
            "floor": [
                {"round": line.round_n, "speaker": line.speaker, "text": line.text}
                for line in self.lines
            ],
        }
