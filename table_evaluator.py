def normalise_cell(value):
    if value is None:
        return ""

    return " ".join(
        str(value).lower().split()
    )


def compare_table(source_table, ai_table):
    source_rows = source_table.get("rows", [])
    ai_rows = ai_table.get("rows", [])

    source_row_count = len(source_rows)
    ai_row_count = len(ai_rows)

    source_column_count = max(
        (len(row) for row in source_rows),
        default=0
    )

    ai_column_count = max(
        (len(row) for row in ai_rows),
        default=0
    )

    total_source_cells = sum(
        len(row)
        for row in source_rows
    )

    matched_cells = 0
    discrepancies = []

    for row_index, source_row in enumerate(source_rows):

        for column_index, source_value in enumerate(source_row):

            ai_value = ""

            if row_index < len(ai_rows):
                ai_row = ai_rows[row_index]

                if column_index < len(ai_row):
                    ai_value = ai_row[column_index]

            source_clean = normalise_cell(source_value)
            ai_clean = normalise_cell(ai_value)

            if source_clean == ai_clean:
                matched_cells += 1
            else:
                discrepancies.append({
                    "row": row_index + 1,
                    "column": column_index + 1,
                    "source": source_value,
                    "ai": ai_value
                })

    if total_source_cells == 0:
        cell_accuracy = 1.0
    else:
        cell_accuracy = (
            matched_cells / total_source_cells
        )

    schema_match = (
        source_row_count == ai_row_count
        and source_column_count == ai_column_count
    )

    return {
        "source_table_id": source_table["id"],
        "ai_table_id": ai_table["id"],

        "source_rows": source_row_count,
        "ai_rows": ai_row_count,

        "source_columns": source_column_count,
        "ai_columns": ai_column_count,

        "schema_match": schema_match,
        "matched_cells": matched_cells,
        "total_source_cells": total_source_cells,
        "cell_accuracy": round(cell_accuracy, 4),
        "discrepancies": discrepancies
    }


def get_tables(classified_document):
    return [
        item
        for item in classified_document["content"]
        if item["content_type"] == "table"
    ]


def evaluate_tables(source_document, ai_document):
    source_tables = get_tables(source_document)
    ai_tables = get_tables(ai_document)

    evaluated = []

    common_table_count = min(
        len(source_tables),
        len(ai_tables)
    )

    for index in range(common_table_count):
        evaluated.append(
            compare_table(
                source_tables[index],
                ai_tables[index]
            )
        )

    missing_tables = source_tables[common_table_count:]
    extra_tables = ai_tables[common_table_count:]

    return {
        "evaluated_tables": evaluated,
        "missing_tables": [
            table["id"]
            for table in missing_tables
        ],
        "extra_tables": [
            table["id"]
            for table in extra_tables
        ]
    }