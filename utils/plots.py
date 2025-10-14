# utils/plots.py
from pathlib import Path

# Try to import Matplotlib in a headless-safe way; fall back to no-op if it fails
try:
    import matplotlib
    matplotlib.use("Agg")  # headless backend
    from matplotlib import pyplot as plt
    _PLOTS_OK = True
except Exception as e:
    print(f"[plots] Matplotlib unavailable ({e}). Charts will be skipped locally.")
    plt = None
    _PLOTS_OK = False

def bar_plot(title: str, labels: list[str], values: list[float], out_path: Path):
    if not _PLOTS_OK or plt is None:
        # No-op fallback: just return without raising, so the rest of the run succeeds
        return
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure()
    plt.bar(range(len(values)), values)
    plt.xticks(range(len(labels)), labels, rotation=45, ha="right")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
