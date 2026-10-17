import json
import os
import random
from dataclasses import asdict, dataclass, field


@dataclass
class State:
    cycle: int = 0
    order: list = field(default_factory=list)
    cursor: int = 0
    pending: dict | None = None
    history: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "State":
        return cls(
            cycle=data.get("cycle", 0),
            order=data.get("order", []),
            cursor=data.get("cursor", 0),
            pending=data.get("pending"),
            history=data.get("history", []),
        )

    def to_dict(self) -> dict:
        return asdict(self)


class StateStore:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> State:
        if not os.path.exists(self.path):
            return State()
        with open(self.path, encoding="utf-8") as fh:
            return State.from_dict(json.load(fh))

    def save(self, state: State) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(state.to_dict(), fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp_path, self.path)


def shuffled_order(ids: list) -> list:
    order = list(ids)
    random.shuffle(order)
    return order
