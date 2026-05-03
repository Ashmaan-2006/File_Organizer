from pathlib import Path
import re
import shutil
import json
from datetime import datetime
from collections import Counter
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

FOLDER = Path(r"C:\Users\ashma\Downloads")
DRY_RUN = True
LOG_FILE = FOLDER / "organizer_log.json"

SUPPORTED_TEXT_TYPES = {".txt", ".md", ".csv"}

STOP_WORDS = {
    "the", "and", "for", "with", "from", "that", "this",
    "file", "final", "copy", "new", "old", "version",
    "download", "document", "pdf", "docx"
}

def scan_files(folder: Path):
    return [
        item for item in folder.iterdir()
        if item.is_file() and item.name != LOG_FILE.name
    ]

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

def generate_folder_name(files):
    words = []

    for file in files:
        cleaned = clean_filename(file)
        for word in cleaned.split():
            if len(word) > 2 and word not in STOP_WORDS:
                words.append(word)

    common_words = [word for word, _ in Counter(words).most_common(4)]

    if not common_words:
        return "Misc"

    folder_name = "_".join(common_words).title()
    return folder_name[:50]

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

def get_safe_destination(target_folder: Path, file: Path):
    destination = target_folder / file.name

    if not destination.exists():
        return destination

    counter = 1

    while True:
        new_name = f"{file.stem}_{counter}{file.suffix}"
        destination = target_folder / new_name

        if not destination.exists():
            return destination

        counter += 1

def move_files(groups):
    log_entries = []

    for grouped_files in groups.values():
        folder_name = generate_folder_name(grouped_files)
        target_folder = FOLDER / folder_name

        for file in grouped_files:
            destination = get_safe_destination(target_folder, file)

            print(f"Moving: {file.name} -> {destination}")

            if not DRY_RUN:
                target_folder.mkdir(exist_ok=True)
                shutil.move(str(file), str(destination))

                log_entries.append({
                    "original_path": str(file),
                    "new_path": str(destination),
                    "moved_at": datetime.now().isoformat()
                })

    if not DRY_RUN:
        LOG_FILE.write_text(json.dumps(log_entries, indent=2))

def main():
    files = scan_files(FOLDER)

    if len(files) < 2:
        print("Not enough files to organize.")
        return

    groups = cluster_files(files)

    print("\nOrganization plan:")

    for grouped_files in groups.values():
        folder_name = generate_folder_name(grouped_files)

        print(f"\nFolder: {folder_name}")
        for file in grouped_files:
            print(f"  - {file.name}")

    if DRY_RUN:
        print("\nDry run complete. No files were moved.")
        print("Change DRY_RUN to False when you are ready.")
    else:
        move_files(groups)
        print(f"\nFiles moved. Undo log saved to: {LOG_FILE}")

if __name__ == "__main__":
    main()