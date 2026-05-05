# Smart File Organizer

This project is a small Python script that helps organize files by grouping similar documents together.

It scans a folder, reads file names and some file text, creates embeddings using a sentence transformer model, clusters similar files, and suggests folder names based on common words.

## What it does

- scans files in the target folder
- can scan subfolders too
- only looks at files from the last 30 days
- ignores some file types like installers, archives, images, and media
- reads text from:
  - `.pdf`
  - `.docx`
  - `.txt`, `.md`, `.csv`
- groups similar files together
- suggests folder names automatically
- can move files into those folders
- writes a move log when real moves are enabled

## Current behavior

The script is currently in dry run mode:

```python
DRY_RUN = True
```

That means it only prints the organization plan.

It does **not** move any files until you change `DRY_RUN` to `False`.

By default, the script targets the current user's `Downloads` folder, so someone else can run it on their own laptop without changing your personal path.

## Requirements

Install the needed packages with:

```powershell
pip install -r requirements.txt
```

## How to run it

From PowerShell:

```powershell
cd path\to\File_Organizer
python smart_organizer.py
```

That uses your own `Downloads` folder by default.

If you want to organize a different folder, use:

```powershell
python smart_organizer.py --folder "C:\Path\To\Folder"
```

## Safe workflow

Recommended steps:

1. Keep `DRY_RUN = True`
2. Run the script
3. Check the printed organization plan
4. If the grouping looks good, change:

```python
DRY_RUN = False
```

5. Run the script again to actually move files

## Main settings

These are the main options near the top of `smart_organizer.py`:

- `DRY_RUN`
  - if `True`, only prints the plan
  - if `False`, actually moves files
- `SCAN_SUBFOLDERS`
  - if `True`, scans recursively
  - if `False`, only scans one folder level
- `LOOKBACK_DAYS`
  - only includes files modified within this many days
- `IGNORED_SUFFIXES`
  - file types that will be skipped

Command line option:

- `--folder`
  - lets you choose which folder to organize at runtime
  - if you do not pass it, the script uses your own `Downloads` folder

## Supported file reading

The script tries to read:

- PDF files with `pypdf`
- Word files with `python-docx`
- plain text style files directly

If a PDF cannot be fully read, the script keeps going and will usually fall back to using the filename only.

## Output

In dry run mode, the script prints:

- any read issues
- the grouping plan
- the folder names it would create

In real move mode, it also:

- creates destination folders
- moves files
- saves an undo log to:

`<target folder>\organizer_log.json`

## Notes

- Folder names are based on common words in grouped filenames.
- If a file name already exists in the destination, the script adds `_1`, `_2`, etc.
- The clustering is based on semantic similarity, so results may not always be perfect.
- It is a good idea to test with `DRY_RUN = True` before moving anything.
- If someone else runs the script, they should still review the dry run first before allowing file moves.
