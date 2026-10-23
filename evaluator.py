import re
from difflib import SequenceMatcher


NUMBER_PATTERN = re.compile(
    r"[-+]?\d+(?:\.\d+)?"
)

UNIT_PATTERN = re.compile(
    r"mg/mL|mmol/mL|µg/mL|mcg/mL|"
    r"mg|kg|mcg|µg|g|"
    r"mL|L|"
    r"°C|"
    r"hours?|hrs?|minutes?|mins?|"
    r"%",
    re.IGNORECASE
)

QUALIFIER_PATTERN = re.compile(
    r"\b("
    r"NLT|NMT|"
    r"not less than|"
    r"not more than|"
    r"at least|"
    r"at most|"
    r"greater than|"
    r"less than"
    r")\b",
    re.IGNORECASE
)


def normalise_value(value):
    return value.strip().lower()


def extract_numbers(text):
    return NUMBER_PATTERN.findall(text)


def extract_units(text):
    return [
        normalise_value(value)
        for value in UNIT_PATTERN.findall(text)
    ]


def extract_qualifiers(text):
    return [
        normalise_qualifier(value)
        for value in QUALIFIER_PATTERN.findall(text)
    ]


def normalise_qualifier(value):
    value = value.strip().lower()

    mapping = {
        "nlt": ">=",
        "not less than": ">=",
        "at least": ">=",

        "nmt": "<=",
        "not more than": "<=",
        "at most": "<=",

        "greater than": ">",
        "less than": "<"
    }

    return mapping.get(value, value)


def calculate_text_similarity(source_text, ai_text):
    return round(
        SequenceMatcher(
            None,
            source_text.lower(),
            ai_text.lower()
        ).ratio(),
        4
    )


def compare_list(source_values, ai_values):
    source_normalised = [
        normalise_value(value)
        for value in source_values
    ]

    ai_normalised = [
        normalise_value(value)
        for value in ai_values
    ]

    return {
        "source": source_values,
        "ai": ai_values,
        "match": source_normalised == ai_normalised
    }


def evaluate_pair(match):
    source_item = match["source"]
    ai_item = match["ai"]

    source_text = source_item["text"]
    ai_text = ai_item["text"]

    source_numbers = extract_numbers(source_text)
    ai_numbers = extract_numbers(ai_text)

    source_units = extract_units(source_text)
    ai_units = extract_units(ai_text)

    source_qualifiers = extract_qualifiers(source_text)
    ai_qualifiers = extract_qualifiers(ai_text)

    number_result = compare_list(
        source_numbers,
        ai_numbers
    )

    unit_result = compare_list(
        source_units,
        ai_units
    )

    qualifier_result = {
        "source": source_qualifiers,
        "ai": ai_qualifiers,
        "match": source_qualifiers == ai_qualifiers
    }

    text_similarity = calculate_text_similarity(
        source_text,
        ai_text
    )

    errors = []
    severity = "none"

    if not number_result["match"]:
        errors.append("numeric_mismatch")
        severity = "critical"

    if not unit_result["match"]:
        errors.append("unit_mismatch")
        severity = "critical"

    if not qualifier_result["match"]:
        errors.append("qualifier_mismatch")

        if severity != "critical":
            severity = "major"

    if text_similarity < 0.50:
        errors.append("low_text_similarity")

        if severity == "none":
            severity = "major"

    if not errors:
        status = "match"
    elif severity == "critical":
        status = "critical_mismatch"
    else:
        status = "partial_match"

    return {
        "source_id": source_item["id"],
        "ai_id": ai_item["id"],

        "source_text": source_text,
        "ai_text": ai_text,

        "alignment_score": match["alignment_score"],
        "text_similarity": text_similarity,

        "numbers": number_result,
        "units": unit_result,
        "qualifiers": qualifier_result,

        "status": status,
        "severity": severity,
        "errors": errors
    }


def evaluate_alignment(alignment):
    evaluated_matches = [
        evaluate_pair(match)
        for match in alignment["matched"]
    ]

    missing = [
        {
            "id": item["id"],
            "text": item["text"],
            "status": "missing",
            "severity": "major"
        }
        for item in alignment["missing"]
    ]

    extra = [
        {
            "id": item["id"],
            "text": item["text"],
            "status": "extra",
            "severity": "major"
        }
        for item in alignment["extra"]
    ]

    return {
        "evaluated_matches": evaluated_matches,
        "missing": missing,
        "extra": extra
    }