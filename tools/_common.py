"""Shared helpers for the validator suite."""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CURRICULUM = ROOT / "curriculum"
CONCEPTS = ROOT / "concepts"
LANDSCAPE = ROOT / "landscape"

FM_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


@dataclass
class Doc:
    path: pathlib.Path
    meta: dict
    body: str

    @property
    def id(self) -> str:
        return self.meta.get("id", "")

    @property
    def rel(self) -> str:
        return str(self.path.relative_to(ROOT))


@dataclass
class Problems:
    items: list[str] = field(default_factory=list)

    def add(self, where: str, msg: str) -> None:
        self.items.append(f"{where}: {msg}")

    def report(self, name: str) -> int:
        if not self.items:
            print(f"  ok  {name}")
            return 0
        print(f"FAIL  {name}")
        for i in self.items:
            print(f"        {i}")
        return 1


def parse(path: pathlib.Path) -> Doc | None:
    m = FM_RE.match(path.read_text())
    if not m:
        return None
    return Doc(path=path, meta=yaml.safe_load(m.group(1)) or {}, body=m.group(2))


def lessons() -> list[Doc]:
    out = []
    for p in sorted(CURRICULUM.glob("*/*/index.md")):
        if d := parse(p):
            out.append(d)
    return out


def concepts() -> list[Doc]:
    out = []
    for p in sorted(CONCEPTS.glob("*.md")):
        if p.name == "index.md":
            continue
        if d := parse(p):
            out.append(d)
    return out


def landscape() -> list[Doc]:
    out = []
    for p in sorted(LANDSCAPE.rglob("*.md")):
        if p.name == "index.md":
            continue
        if d := parse(p):
            out.append(d)
    return out


def syllabus() -> dict:
    return yaml.safe_load((CURRICULUM / "syllabus.yml").read_text())


def syllabus_lessons(doc: dict | None = None) -> list[tuple[str, str, dict]]:
    """(level_id, module_id, lesson) in linear order."""
    doc = doc or syllabus()
    return [
        (lv["id"], m["id"], l)
        for lv in doc["levels"]
        for m in lv["modules"]
        for l in m["lessons"]
    ]
