import matplotlib
matplotlib.use("Agg")  # headless for CI
import matplotlib.pyplot as plt
from pathlib import Path

def bar_plot(title, labels, values, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(8,4.5))
    plt.title(title)
    plt.bar(labels, values)
    plt.xticks(rotation=25, ha='right')
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
