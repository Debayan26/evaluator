# Document Validation Pipeline

A local Python command-line tool that compares an approved source document with an AI-generated report. It extracts text and tables, aligns paragraphs, checks numeric values, units, and qualifiers, calculates scores, and writes a detailed JSON report. It does not use a language model or make a semantic determination that a statement is true.

## Requirements

- Python 3.11 recommended.
- Tesseract OCR installed separately if PDFs contain substantial embedded images that need OCR. Tesseract is an operating-system application; `pip install` does not install it.
- The Python packages listed in `requirements.txt`.

## Install And Run

Run commands from the project directory. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `tesseract.exe` is not on `PATH`, set its location for the current PowerShell session:

```powershell
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Then run the pipeline:

```powershell
.\.venv\Scripts\python.exe main.py
```

On macOS/Linux, create the environment with `python3 -m venv .venv`, install using `.venv/bin/python -m pip install -r requirements.txt`, optionally set `export TESSERACT_CMD=/path/to/tesseract`, then run `.venv/bin/python main.py`.

`main.py` currently selects `MET-val100190816.pdf` as the source and `MET-sugammadex-sodium.pdf` as the AI report. Put the input files in the project directory or change the `source_file` and `ai_file` values near the bottom of `main.py`. The script writes or overwrites `validation_report.json` in the current directory.

## Pipeline

1. **Extract**: `extractor.py` reads PDF text blocks, detects line-based tables in the page body, and OCRs qualifying embedded image regions. OCR lines are approximately deduplicated against native text. DOCX extraction reads body paragraphs and tables. Small images such as logos are skipped. PDF tables in the top and bottom 20% of a page are filtered to avoid repeating headers and footers.
2. **Normalize**: `normaliser.py` converts extracted paragraphs and tables into the shared structures in `models.py` and cleans paragraph whitespace.
3. **Classify**: `classifier.py` labels paragraph text as `numeric_fact` when it contains both a number and a recognized unit; other paragraphs are classified as text. Tables are kept as separate items.
4. **Align text**: `aligner.py` uses TF-IDF word and two-word features with cosine similarity. For each source paragraph, it greedily chooses the best unused AI paragraph at or above the default `0.30` threshold. Each AI paragraph can be used only once. Unmatched source paragraphs are reported as missing; unmatched AI paragraphs are extra.
5. **Evaluate**: `evaluator.py` checks matched paragraphs for text similarity, numeric values, units, and recognized qualifiers. `table_evaluator.py` compares tables, rows, and cells by their order and position.
6. **Score and report**: `scorer.py` calculates summary scores and the validation gate. `reporter.py` writes the full result to `validation_report.json`.

## Scores And Gate

- **Text accuracy**: average `SequenceMatcher` text similarity over matched paragraph pairs only.
- **Content coverage**: matched source paragraphs / (matched source paragraphs + missing source paragraphs). Extra AI paragraphs are not part of this denominator.
- **Numeric accuracy**: exact ordered numeric-list matches / matched paragraph pairs that contain numbers on either side.
- **Unit accuracy**: exact ordered unit-list matches / matched paragraph pairs that contain units on either side. Values are not converted between units.
- **Qualifier accuracy**: matching normalized qualifier lists / matched paragraph pairs that contain recognized qualifiers. For example, `NLT` and `not less than` both normalize to `>=`.
- **Table accuracy**: average of each evaluated table's matching source-cell fraction. Cells are compared at the same row and column positions after lowercasing and collapsing whitespace. Table pairing is by document order, not semantic table matching.
- **Overall score**: when tables exist, `25% text + 20% coverage + 20% numeric + 10% unit + 10% qualifier + 15% table`. Without tables, the weights are `35% text + 25% coverage + 20% numeric + 10% unit + 10% qualifier`.
- **Critical errors**: one for each matched paragraph pair with a numeric or unit mismatch, plus one for each evaluated table whose cell accuracy is below 100%. The gate is `FAIL` if this count is greater than zero; otherwise it is `PASS`.

Missing and extra paragraphs are reported but do not count as critical errors under the current gate. Qualifier-only mismatches are major, not critical. Missing tables are reported, but are not included in the critical table error count. Review these limitations before treating a `PASS` as a release decision.

## Supported Files And Limitations

- **PDF**: selectable text, line-based table detection, and OCR for embedded image regions at least 100 points wide, 40 points tall, and 2% of page area. OCR uses a 2x rendered crop. Small image text can be missed; large figures may be OCR'd even when they are not scans.
- **DOCX**: body paragraphs and tables. Embedded images, headers, and footers are not extracted.
- **DOC**: not supported; convert to DOCX first.

Borderless PDF tables may not be detected. OCR can misread numbers, units, and punctuation; text found inside images is returned as prose rather than reconstructed as table cells. Table matching is positional, so reordered rows can reduce accuracy even if their values are otherwise identical. Inspect extracted content and the detailed report before making a validation decision.

## Project Files

| File | Purpose |
| --- | --- |
| `main.py` | Configured source/AI paths and end-to-end pipeline orchestration. |
| `extractor.py` | PDF/DOCX extraction, PDF table detection, and Tesseract OCR. |
| `normaliser.py` | Converts extracted dictionaries into canonical document objects. |
| `classifier.py` | Labels paragraphs and table content for evaluation. |
| `aligner.py` | TF-IDF paragraph alignment. |
| `evaluator.py` | Text similarity and number/unit/qualifier checks. |
| `table_evaluator.py` | Positional table and cell comparison. |
| `scorer.py` | Summary metrics, overall score, and PASS/FAIL gate. |
| `reporter.py` | Writes the JSON validation report. |
| `models.py` | Paragraph, table, and canonical document data classes. |
| `requirements.txt` | Python package dependencies. |
| `tests/test_extractor.py` | Extractor regression tests. |

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

The extractor tests cover PDF tables, mixed native-text and image OCR, duplicate OCR lines, small-logo filtering, Tesseract configuration, and PDF cleanup after errors.
