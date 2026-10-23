import json
from pathlib import Path


def build_report(
    source_file,
    ai_file,
    scores,
    evaluation,
    table_evaluation
):
    return {
        "source_document": Path(source_file).name,
        "ai_document": Path(ai_file).name,

        "summary": scores,

        "text_evaluation": {
            "matched": evaluation[
                "evaluated_matches"
            ],

            "missing": evaluation["missing"],
            "extra": evaluation["extra"]
        },

        "table_evaluation": table_evaluation
    }


def save_report(
    report,
    output_file="validation_report.json"
):
    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )