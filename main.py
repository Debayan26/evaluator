from extractor import extract_document
from normaliser import normalise_document
from classifier import classify_document
from aligner import ContentAligner, get_text_items

from evaluator import evaluate_alignment
from table_evaluator import evaluate_tables
from scorer import calculate_scores
from reporter import build_report, save_report


def process_document(file_path):

    print(f"\nProcessing: {file_path}")

    # Block 1
    extracted = extract_document(file_path)
    print("Block 1 - Extraction complete")

    # Block 2
    normalised = normalise_document(
        file_path,
        extracted
    )
    print("Block 2 - Normalisation complete")

    # Block 3
    classified = classify_document(normalised)
    print("Block 3 - Classification complete")

    return classified


if __name__ == "__main__":

    source_file = "MET-val100190816.pdf"
    ai_file = "MET-sugammadex-sodium.pdf"

    # Blocks 1, 2 and 3
    source_classified = process_document(
        source_file
    )

    ai_classified = process_document(
        ai_file
    )

    # Block 4: Alignment
    source_text = get_text_items(
        source_classified
    )

    ai_text = get_text_items(
        ai_classified
    )

    aligner = ContentAligner()

    alignment = aligner.align_text(
        source_text,
        ai_text
    )

    print("Block 4 - Alignment complete")

    # Block 5A: Text, numeric, unit and
    # qualifier evaluation
    evaluation = evaluate_alignment(
        alignment
    )

    # Block 5B: Table evaluation
    table_evaluation = evaluate_tables(
        source_classified,
        ai_classified
    )

    print("Block 5 - Accuracy evaluation complete")

    # Block 6: Score and validation gate
    scores = calculate_scores(
        evaluation,
        table_evaluation
    )

    print("Block 6 - Scoring complete")

    # Block 7: Validation report
    report = build_report(
        source_file,
        ai_file,
        scores,
        evaluation,
        table_evaluation
    )

    save_report(
        report,
        "validation_report.json"
    )

    print("Block 7 - Report generated")

    print("\n===== VALIDATION SUMMARY =====")

    print(
        "Text accuracy:",
        scores["text_accuracy"],
        "%"
    )

    print(
        "Content coverage:",
        scores["content_coverage"],
        "%"
    )

    print(
        "Numeric accuracy:",
        scores["numeric_accuracy"],
        "%"
    )

    print(
        "Unit accuracy:",
        scores["unit_accuracy"],
        "%"
    )

    print(
        "Qualifier accuracy:",
        scores["qualifier_accuracy"],
        "%"
    )

    if scores["table_accuracy"] is not None:
        print(
            "Table accuracy:",
            scores["table_accuracy"],
            "%"
        )

    print(
        "Overall score:",
        scores["overall_score"],
        "%"
    )

    print(
        "Critical errors:",
        scores["critical_error_count"]
    )

    print(
        "Validation status:",
        scores["validation_status"]
    )

    print(
        "\nDetailed report: validation_report.json"
    )