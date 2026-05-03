from pathlib import Path
import re
from pypdf import PdfReader
from docx import Document

FOLDER = Path(r"C:\Users\ashma\Downloads")

SUPPORTED_TEXT_TYPES = {".txt", ".md", ".csv"}

def scan_files(folder: Path):
    return [item for item in folder.iterdir() if item.is_file()]

def clean_filename(path: Path):
    name = path.stem.lower()
    name = re.sub(r"[_\-\(\)\[\]\.]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

def extract_text(path: Path):
    suffix = path.suffix.lower()

    try:
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            text = []

            for page in reader.pages[:3]:
                text.append(page.extract_text() or "")

            return " ".join(text)

        if suffix == ".docx":
            doc = Document(str(path))
            return " ".join(paragraph.text for paragraph in doc.paragraphs[:80])

        if suffix in SUPPORTED_TEXT_TYPES:
            return path.read_text(errors="ignore")[:5000]

    except Exception as error:
        print(f"Could not read {path.name}: {error}")

    return ""

def main():
    files = scan_files(FOLDER)

    for file in files:
        cleaned_name = clean_filename(file)
        extracted_text = extract_text(file)

        print("\n--------------------")
        print(f"File: {file.name}")
        print(f"Clean name: {cleaned_name}")
        print(f"Text preview: {extracted_text[:300]}")

if __name__ == "__main__":
    main()