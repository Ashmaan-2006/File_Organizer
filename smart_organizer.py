from pathlib import Path
import re
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

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
            return " ".join((page.extract_text() or "") for page in reader.pages[:3])

        if suffix == ".docx":
            doc = Document(str(path))
            return " ".join(paragraph.text for paragraph in doc.paragraphs[:80])

        if suffix in SUPPORTED_TEXT_TYPES:
            return path.read_text(errors="ignore")[:5000]

    except Exception as error:
        print(f"Could not read {path.name}: {error}")

    return ""

def build_file_context(file: Path):
    return f"{clean_filename(file)} {extract_text(file)}"

def cluster_files(files):
    texts = [build_file_context(file) for file in files]

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode(texts)

    clusterer = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1.15
    )

    labels = clusterer.fit_predict(embeddings)

    groups = {}

    for file, label in zip(files, labels):
        groups.setdefault(label, []).append(file)

    return groups

def main():
    files = scan_files(FOLDER)

    if len(files) < 2:
        print("Not enough files to organize.")
        return

    groups = cluster_files(files)

    for label, grouped_files in groups.items():
        print(f"\nGroup {label}:")
        for file in grouped_files:
            print(f"  {file.name}")

if __name__ == "__main__":
    main()