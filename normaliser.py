from pathlib import Path
from models import Paragraph, Table, CanonicalDocument


def normalise_document(file_path: str, extracted: dict) -> CanonicalDocument:

    paragraphs = []

    for i, text in enumerate(extracted.get("paragraphs", []), start=1):
        paragraphs.append(
            Paragraph(
                id=f"P{i}",
                text=clean_text(text)
            )
        )

    tables = []

    for i, table in enumerate(extracted.get("tables", []), start=1):
        tables.append(
            Table(
                id=f"T{i}",
                rows=table["rows"]
            )
        )

    return CanonicalDocument(
        document_name=Path(file_path).name,
        paragraphs=paragraphs,
        tables=tables
    )


def clean_text(text: str) -> str:
    return " ".join(text.split())