"""
CPT & ICD-10 Book OCR Full Extraction
=====================================
Extracts all text from scanned PDF books using Tesseract OCR.
Supports resume (skips already-processed pages).
"""
import os
import sys
import time
import json
import argparse
import pytesseract
import fitz
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

BOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BOOKS_DIR, "ocr_tmp")
os.makedirs(TEMP_DIR, exist_ok=True)

PDFS = {
    "cpt": {
        "path": os.path.join(BOOKS_DIR, "CPT - 2026(NEW).pdf"),
        "output": os.path.join(BOOKS_DIR, "cpt_ocr_full.txt"),
        "progress": os.path.join(BOOKS_DIR, "cpt_ocr_progress.json"),
    },
    "icd": {
        "path": os.path.join(BOOKS_DIR, "ICD-2026  (NEW).pdf"),
        "output": os.path.join(BOOKS_DIR, "icd_ocr_full.txt"),
        "progress": os.path.join(BOOKS_DIR, "icd_ocr_progress.json"),
    },
}


def load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            return json.load(f)
    return {"completed_pages": [], "total_pages": 0}


def save_progress(progress_file, progress):
    with open(progress_file, "w") as f:
        json.dump(progress, f)


def extract_page(pdf, page_num, dpi=200):
    page = pdf[page_num]
    pix = page.get_pixmap(dpi=dpi)
    img_path = os.path.join(TEMP_DIR, f"tmp_{page_num}.png")
    pix.save(img_path)
    img = Image.open(img_path)
    text = pytesseract.image_to_string(img, lang="eng")
    os.unlink(img_path)
    return text


def extract_book(book_key, start_page=0, end_page=None, dpi=200):
    config = PDFS[book_key]
    pdf_path = config["path"]
    output_file = config["output"]
    progress_file = config["progress"]

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    doc = fitz.open(pdf_path)
    total = doc.page_count
    if end_page is None:
        end_page = total

    progress = load_progress(progress_file)
    completed = set(progress["completed_pages"])
    done_count = len(completed)

    print(f"\n{'='*60}")
    print(f"  OCR Extraction: {book_key.upper()}")
    print(f"  Pages: {start_page}-{end_page-1} ({end_page-start_page} total)")
    print(f"  Already done: {done_count}")
    print(f"  Remaining: {end_page - start_page - len([p for p in range(start_page, end_page) if p in completed])}")
    print(f"{'='*60}")

    all_text = []
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing:
            all_text.append(existing)

    pages_to_process = [p for p in range(start_page, end_page) if p not in completed]
    batch_text = []
    t_start = time.time()

    for idx, page_num in enumerate(pages_to_process):
        try:
            text = extract_page(doc, page_num, dpi=dpi)
            if text.strip():
                batch_text.append(f"\n--- PAGE {page_num + 1} ---\n{text}")
            completed.add(page_num)

            if (idx + 1) % 10 == 0 or idx == len(pages_to_process) - 1:
                elapsed = time.time() - t_start
                rate = (idx + 1) / elapsed if elapsed > 0 else 0
                remaining = (len(pages_to_process) - idx - 1) / rate if rate > 0 else 0
                pct = (idx + 1) / len(pages_to_process) * 100
                print(f"  [{pct:5.1f}%] Page {page_num+1}/{total} | "
                      f"{idx+1}/{len(pages_to_process)} done | "
                      f"{rate:.1f} pages/s | ETA {remaining/60:.0f}min")

            if (idx + 1) % 50 == 0:
                all_text.extend(batch_text)
                batch_text = []
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("".join(all_text))
                progress["completed_pages"] = list(completed)
                progress["total_pages"] = total
                save_progress(progress_file, progress)

        except Exception as e:
            print(f"  ERROR on page {page_num+1}: {e}")

    all_text.extend(batch_text)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("".join(all_text))
    progress["completed_pages"] = list(completed)
    progress["total_pages"] = total
    save_progress(progress_file, progress)

    doc.close()
    elapsed = time.time() - t_start
    print(f"\n  DONE: {len(pages_to_process)} pages in {elapsed/60:.1f} min")
    print(f"  Output: {output_file}")
    print(f"  Total text: {len(''.join(all_text))} chars")


def main():
    parser = argparse.ArgumentParser(description="OCR Extract CPT/ICD books")
    parser.add_argument("--book", choices=["cpt", "icd", "all"], default="all")
    parser.add_argument("--start", type=int, default=0, help="Start page (0-indexed)")
    parser.add_argument("--end", type=int, default=None, help="End page (exclusive)")
    parser.add_argument("--dpi", type=int, default=200, help="Rendering DPI")
    parser.add_argument("--resume", action="store_true", help="Skip already processed pages")
    args = parser.parse_args()

    books = ["cpt", "icd"] if args.book == "all" else [args.book]
    for book in books:
        extract_book(book, args.start, args.end, args.dpi)


if __name__ == "__main__":
    main()
