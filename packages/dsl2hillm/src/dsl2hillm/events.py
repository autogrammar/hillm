from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StoredEvent:
    id: str
    ts_unix: int
    command: dict[str, Any]
    result: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HillmEventStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def for_workdir(cls, workdir: Path) -> HillmEventStore:
        root = workdir.expanduser().resolve()
        events_dir = root / ".hillm" / "events"
        events_dir.mkdir(parents=True, exist_ok=True)
        return cls(events_dir / "app.hillm.events.jsonl")

    def append_command(self, command: dict[str, Any], result: dict[str, Any]) -> str:
        event_id = uuid.uuid4().hex
        event = StoredEvent(id=event_id, ts_unix=int(time.time()), command=command, result=result)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        return event_id

    def read_all(self) -> list[StoredEvent]:
        if not self.path.is_file():
            return []
        events: list[StoredEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            events.append(
                StoredEvent(
                    id=str(data["id"]),
                    ts_unix=int(data["ts_unix"]),
                    command=data["command"],
                    result=data["result"],
                )
            )
        return events


EventStore = HillmEventStore
