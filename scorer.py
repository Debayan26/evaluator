def safe_average(values):
    if not values:
        return 0.0

    return sum(values) / len(values)


def calculate_scores(
    evaluation,
    table_evaluation
):
    matches = evaluation["evaluated_matches"]

    matched_count = len(matches)
    missing_count = len(evaluation["missing"])
    extra_count = len(evaluation["extra"])

    source_item_count = (
        matched_count + missing_count
    )

    if source_item_count == 0:
        coverage_score = 0.0
    else:
        coverage_score = (
            matched_count / source_item_count
        )

    text_scores = [
        item["text_similarity"]
        for item in matches
    ]

    numeric_results = [
        item["numbers"]["match"]
        for item in matches
        if (
            item["numbers"]["source"]
            or item["numbers"]["ai"]
        )
    ]

    unit_results = [
        item["units"]["match"]
        for item in matches
        if (
            item["units"]["source"]
            or item["units"]["ai"]
        )
    ]

    qualifier_results = [
        item["qualifiers"]["match"]
        for item in matches
        if (
            item["qualifiers"]["source"]
            or item["qualifiers"]["ai"]
        )
    ]

    text_score = safe_average(text_scores)

    numeric_score = safe_average([
        1.0 if value else 0.0
        for value in numeric_results
    ])

    unit_score = safe_average([
        1.0 if value else 0.0
        for value in unit_results
    ])

    qualifier_score = safe_average([
        1.0 if value else 0.0
        for value in qualifier_results
    ])

    table_scores = [
        table["cell_accuracy"]
        for table in table_evaluation[
            "evaluated_tables"
        ]
    ]

    table_score = safe_average(table_scores)

    # Only include table weight when tables exist.
    has_tables = bool(
        table_evaluation["evaluated_tables"]
        or table_evaluation["missing_tables"]
        or table_evaluation["extra_tables"]
    )

    if has_tables:
        overall_score = (
            0.25 * text_score
            + 0.20 * coverage_score
            + 0.20 * numeric_score
            + 0.10 * unit_score
            + 0.10 * qualifier_score
            + 0.15 * table_score
        )
    else:
        overall_score = (
            0.35 * text_score
            + 0.25 * coverage_score
            + 0.20 * numeric_score
            + 0.10 * unit_score
            + 0.10 * qualifier_score
        )

    critical_errors = [
        item
        for item in matches
        if item["severity"] == "critical"
    ]

    critical_table_errors = [
        table
        for table in table_evaluation[
            "evaluated_tables"
        ]
        if table["cell_accuracy"] < 1.0
    ]

    critical_error_count = (
        len(critical_errors)
        + len(critical_table_errors)
    )

    validation_status = (
        "FAIL"
        if critical_error_count > 0
        else "PASS"
    )

    return {
        "text_accuracy": round(
            text_score * 100,
            2
        ),

        "content_coverage": round(
            coverage_score * 100,
            2
        ),

        "numeric_accuracy": round(
            numeric_score * 100,
            2
        ),

        "unit_accuracy": round(
            unit_score * 100,
            2
        ),

        "qualifier_accuracy": round(
            qualifier_score * 100,
            2
        ),

        "table_accuracy": round(
            table_score * 100,
            2
        ) if has_tables else None,

        "overall_score": round(
            overall_score * 100,
            2
        ),

        "matched_items": matched_count,
        "missing_items": missing_count,
        "extra_items": extra_count,

        "critical_error_count": (
            critical_error_count
        ),

        "validation_status": validation_status
    }