from pathlib import Path
import shutil

# Root of your project
ROOT = Path(__file__).parent.resolve()
DIRS_TO_DELETE = ["data", "docs", "out", "__pycache__"]

def remove_dir(p: Path):
    if p.exists() and p.is_dir():
        print(f"🧹 Removing: {p}")
        shutil.rmtree(p, ignore_errors=True)

def main():
    for d in DIRS_TO_DELETE:
        remove_dir(ROOT / d)

    print("✅ Cleanup complete — ready for a fresh run!")

if __name__ == "__main__":
    main()
