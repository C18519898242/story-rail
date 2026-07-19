from dataclasses import dataclass


@dataclass(frozen=True)
class Choice:
    id: str
    text: str
    result: str
    next_node: str


@dataclass(frozen=True)
class Node:
    id: str
    text: str
    choices: tuple[Choice, ...] = ()
    ending: bool = False


@dataclass(frozen=True)
class Script:
    schema_version: int
    id: str
    title: str
    start_node: str
    nodes: dict[str, Node]
