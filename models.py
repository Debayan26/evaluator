from dataclasses import dataclass, field
from typing import List


@dataclass
class Paragraph:
    id: str
    text: str


@dataclass
class Table:
    id: str
    rows: List[List[str]] = field(default_factory=list)


@dataclass
class CanonicalDocument:
    document_name: str
    paragraphs: List[Paragraph]
    tables: List[Table]