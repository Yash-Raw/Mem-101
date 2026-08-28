"""Lab: assemble a model of the person, and keep what does not fit.

    uv run python curriculum/advanced/from-facts-to-a-user-model/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory, MemoryType, Scope


@dataclass(frozen=True)
class Attribute:
    """One slot of the model: what is believed now, and how settled it is."""

    slot: str
    beliefs: tuple[Memory, ...]
    superseded: int

    @property
    def volatile(self) -> bool:
        """Has this attribute ever been replaced?"""
        raise NotImplementedError("implement Attribute.volatile")

    @property
    def values(self) -> tuple[str, ...]:
        return tuple(m.content for m in self.beliefs)


@dataclass(frozen=True)
class UserModel:
    scope: Scope
    attributes: dict[str, Attribute]
    unkeyed: tuple[Memory, ...]     # true, stated, and about no modelled attribute
    third_party: tuple[Memory, ...]  # about someone else entirely

    @property
    def stable(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, a in self.attributes.items() if not a.volatile))

    @property
    def volatile(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, a in self.attributes.items() if a.volatile))


def build(memories: list[Memory], scope: Scope) -> UserModel:
    """Assemble the model, and keep what would not fit rather than dropping it.

    `unkeyed` and `third_party` are returned, not discarded. A model that
    silently omits a third of what it was built from reports the same shape
    as one with nothing to omit, and the omission is where the next question
    lives.
    """
    raise NotImplementedError("implement build")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-usermodel.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()

    naive = [m for m in memories if m.type is MemoryType.SEMANTIC and m.is_live]
    model = build(memories, scope)
    print(f"naive model: {len(naive)} statements")
    print(f"model      : {len(model.attributes)} attributes, "
          f"{len(model.unkeyed)} unkeyed, {len(model.third_party)} third-party\n")

    for slot, attribute in model.attributes.items():
        state = "volatile" if attribute.volatile else "stable  "
        values = "; ".join(v.replace("Priya ", "") for v in attribute.values)
        print(f"   {slot:16} {state} ({attribute.superseded})  {values[:62]}")

    print(f"\n   stable  : {model.stable}")
    print(f"   volatile: {model.volatile}")

    print("\n   cannot enter the model:")
    for memory in model.unkeyed:
        print(f"      {memory.content}")

    print("\n   about someone else:")
    for memory in model.third_party:
        print(f"      {memory.content}")


if __name__ == "__main__":
    main()
