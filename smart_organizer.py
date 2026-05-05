from pathlib import Path
import argparse
import re
import shutil
import json
import logging
from datetime import datetime, timedelta
from collections import Counter
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

# default to the current user's Downloads folder so the script is portable
DEFAULT_FOLDER = Path.home() / "Downloads"
FOLDER = DEFAULT_FOLDER
DRY_RUN = True
SCAN_SUBFOLDERS = True
LOOKBACK_DAYS = 30
LOG_FILE = FOLDER / "organizer_log.json"

SUPPORTED_TEXT_TYPES = {".txt", ".md", ".csv"}
PDF_READ_ERRORS = []
IGNORED_SUFFIXES = {
    ".exe", ".msi", ".zip", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".mp3", ".mp4", ".mov", ".avi",
    ".iso", ".dll",
}

STOP_WORDS = {
    "the", "and", "for", "with", "from", "that", "this",
    "file", "final", "copy", "new", "old", "version",
    "download", "document", "pdf", "docx"
}

# keeps pypdf from filling the terminal with low-level warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)

def scan_files(folder: Path):
    iterator = folder.rglob("*") if SCAN_SUBFOLDERS else folder.iterdir()
    cutoff_time = datetime.now() - timedelta(days=LOOKBACK_DAYS)
    return [
        item for item in iterator
        if item.is_file()
        and item.name != LOG_FILE.name
        and item.suffix.lower() not in IGNORED_SUFFIXES
        and datetime.fromtimestamp(item.stat().st_mtime) >= cutoff_time
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
        message = str(error)

        # encrypted PDFs sometimes need cryptography installed
        if "cryptography>=3.1 is required for AES algorithm" in message:
            note = f"{path.name}: encrypted PDF needs the 'cryptography' package"
        else:
            note = f"{path.name}: {message}"

        PDF_READ_ERRORS.append(note)

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


def print_read_issues():
    if not PDF_READ_ERRORS:
        return

    print("\nSome files could not be fully read:")
    for issue in sorted(set(PDF_READ_ERRORS)):
        print(f"  - {issue}")
    print("Those files were still included, but mostly based on their filenames.")

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

def move_files(groups, target_root: Path):
    log_entries = []
    log_file = target_root / "organizer_log.json"

    for grouped_files in groups.values():
        folder_name = generate_folder_name(grouped_files)
        target_folder = target_root / folder_name

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
        log_file.write_text(json.dumps(log_entries, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Group similar files and organize them into folders.")
    parser.add_argument(
        "--folder",
        default=str(FOLDER),
        help="Folder to organize. Defaults to your Downloads folder.",
    )
    args = parser.parse_args()

    folder = Path(args.folder).expanduser()
    files = scan_files(folder)

    if len(files) < 2:
        print("Not enough files to organize.")
        return

    groups = cluster_files(files)
    print_read_issues()

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
        move_files(groups, folder)
        print(f"\nFiles moved. Undo log saved to: {folder / 'organizer_log.json'}")

if __name__ == "__main__":
    main()
