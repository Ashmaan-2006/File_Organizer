from pathlib import Path

FOLDER = Path(r"C:\Users\ashma\Downloads")

def scan_files(folder: Path):
    files = [item for item in folder.iterdir() if item.is_file()]
    return files

def main():
    files = scan_files(FOLDER)

    print(f"Found {len(files)} files:\n")

    for file in files:
        print(file.name)

if __name__ == "__main__":
    main()