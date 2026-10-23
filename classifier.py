import re


# Units important for scientific/pharma documents
UNIT_PATTERN = re.compile(
    r"\b("
    r"mg|g|kg|mcg|µg|"
    r"mL|L|"
    r"mg/mL|g/L|mmol/mL|"
    r"°C|"
    r"hour|hours|hr|hrs|"
    r"minute|minutes|min|"
    r"%"
    r")\b",
    re.IGNORECASE
)

NUMBER_PATTERN = re.compile(
    r"[-+]?\d*\.?\d+"
)

QUALIFIER_PATTERN = re.compile(
    r"\b(NLT|NMT|at least|not less than|not more than)\b",
    re.IGNORECASE
)


def classify_text(text: str) -> dict:

    numbers = NUMBER_PATTERN.findall(text)
    units = UNIT_PATTERN.findall(text)
    qualifiers = QUALIFIER_PATTERN.findall(text)

    if numbers and units:
        content_type = "numeric_fact"
    else:
        content_type = "text"

    return {
        "content_type": content_type,
        "text": text,
        "numbers": numbers,
        "units": units,
        "qualifiers": qualifiers
    }

def classify_document(document):

    classified = {
        "document_name": document.document_name,
        "content": []
    }

    for paragraph in document.paragraphs:

        result = classify_text(paragraph.text)

        result["id"] = paragraph.id

        classified["content"].append(result)

    for table in document.tables:

        classified["content"].append({
            "id": table.id,
            "content_type": "table",
            "rows": table.rows
        })

    return classified