import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pymupdf
from PIL import Image

import extractor


def create_pdf(*, image_rect=None, native_lines=(), table=False, table_y=220):
    document = pymupdf.open()
    page = document.new_page(width=600, height=800)
    for position, text in native_lines:
        page.insert_text(position, text)
    if table:
        x_positions = (50, 220, 390)
        y_positions = (table_y, table_y + 35, table_y + 70)
        for x in x_positions:
            page.draw_line((x, y_positions[0]), (x, y_positions[-1]))
        for y in y_positions:
            page.draw_line((x_positions[0], y), (x_positions[-1], y))
        for row_index, row in enumerate((("Region", "Revenue"), ("North", "12"))):
            for column_index, value in enumerate(row):
                page.insert_text((x_positions[column_index] + 8, y_positions[row_index] + 23), value)
    if image_rect:
        image = Image.new("RGB", (700, 500), "white")
        output = io.BytesIO()
        image.save(output, format="PNG")
        image.close()
        page.insert_image(pymupdf.Rect(image_rect), stream=output.getvalue())
    return document.tobytes()


class ExtractorTests(unittest.TestCase):
    def write_pdf(self, data):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "report.pdf"
        path.write_bytes(data)
        return path

    def test_pdf_tables_are_extracted_and_not_repeated_as_paragraphs(self):
        path = self.write_pdf(create_pdf(
            native_lines=[((50, 50), "Introduction paragraph."), ((50, 400), "Conclusion paragraph.")],
            table=True,
        ))
        extracted = extractor.extract_pdf(str(path))
        self.assertEqual(len(extracted["tables"]), 1)
        self.assertEqual(extracted["tables"][0]["rows"], [["Region", "Revenue"], ["North", "12"]])
        self.assertEqual(extracted["paragraphs"], ["Introduction paragraph.", "Conclusion paragraph."])

    def test_repeated_header_region_is_not_returned_as_a_data_table(self):
        path = self.write_pdf(create_pdf(table=True, table_y=70))
        extracted = extractor.extract_pdf(str(path))
        self.assertEqual(extracted["tables"], [])

    def test_table_precheck_skips_prose_and_keeps_grid_pages(self):
        prose = self.write_pdf(create_pdf(native_lines=[((50, 50), "A regular sentence without aligned data columns.")]))
        grid = self.write_pdf(create_pdf(table=True))
        with pymupdf.open(prose) as document:
            self.assertIsNone(extractor._table_paths(document[0]))
        with pymupdf.open(grid) as document:
            self.assertIsNotNone(extractor._table_paths(document[0]))

    def test_large_mixed_image_is_ocrd_and_duplicate_text_is_removed(self):
        path = self.write_pdf(create_pdf(
            image_rect=(30, 100, 570, 700),
            native_lines=[((50, 50), "A native header longer than twenty characters")],
        ))
        with patch.object(extractor, "_ocr_image_box", return_value="A native header longer than twenty characters\nScanned result 12 mg") as ocr:
            extracted = extractor.extract_pdf(str(path))
        ocr.assert_called_once()
        self.assertEqual(extracted["paragraphs"], [
            "A native header longer than twenty characters", "Scanned result 12 mg"
        ])
        self.assertEqual(extracted["pages"][0]["extraction_method"], "pdf_text+ocr")

    def test_small_logo_does_not_trigger_ocr(self):
        path = self.write_pdf(create_pdf(
            image_rect=(20, 20, 60, 50),
            native_lines=[((80, 100), "This native page has enough text to stay selectable")],
        ))
        with patch.object(extractor, "_ocr_image_box") as ocr:
            extracted = extractor.extract_pdf(str(path))
        ocr.assert_not_called()
        self.assertEqual(extracted["pages"][0]["image_regions_ocr"], 0)
        self.assertEqual(extracted["pages"][0]["extraction_method"], "pdf_text")

    def test_multiple_image_regions_do_not_duplicate_ocr_lines(self):
        data = create_pdf(image_rect=(20, 30, 280, 400))
        document = pymupdf.open(stream=data, filetype="pdf")
        page = document[0]
        image = Image.new("RGB", (700, 500), "white")
        output = io.BytesIO()
        image.save(output, format="PNG")
        image.close()
        page.insert_image(pymupdf.Rect(320, 30, 580, 400), stream=output.getvalue())
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "two-images.pdf"
                path.write_bytes(document.tobytes())
                with patch.object(extractor, "_ocr_image_box", side_effect=["Scanned result 12 mg", "Scanned result 12 mg"]):
                    extracted = extractor.extract_pdf(str(path))
        finally:
            document.close()
        self.assertEqual(extracted["paragraphs"], ["Scanned result 12 mg"])

    def test_tesseract_is_configurable_and_missing_install_is_actionable(self):
        with tempfile.NamedTemporaryFile() as executable:
            with patch.dict(os.environ, {"TESSERACT_CMD": executable.name}):
                with patch.object(extractor.shutil, "which", return_value=None):
                    self.assertEqual(extractor._tesseract_executable(), executable.name)
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(extractor.shutil, "which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "set TESSERACT_CMD"):
                    extractor._tesseract_executable()

    def test_pdf_document_closes_when_ocr_raises(self):
        path = self.write_pdf(create_pdf(image_rect=(20, 30, 580, 750)))
        original_open = pymupdf.open
        opened = []

        def track_open(*args, **kwargs):
            document = original_open(*args, **kwargs)
            opened.append(document)
            return document

        with patch.object(extractor.pymupdf, "open", side_effect=track_open):
            with patch.object(extractor, "_ocr_image_box", side_effect=RuntimeError("OCR failed")):
                with self.assertRaisesRegex(RuntimeError, "OCR failed"):
                    extractor.extract_pdf(str(path))
        self.assertEqual(len(opened), 1)
        self.assertTrue(opened[0].is_closed)


if __name__ == "__main__":
    unittest.main()