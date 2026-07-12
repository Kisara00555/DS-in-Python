"""
plot_evaluation.py
------------------
Generates professional evaluation charts from results.json.

Charts generated:
  1. Radar chart     – Per-question spider plot of all 7 metrics
  2. Bar chart       – Side-by-side metric comparison per question
  3. Summary chart   – Aggregate averages with threshold lines
  4. Heatmap         – Questions × Metrics colour-intensity matrix

Usage:
    python plot_evaluation.py
    python plot_evaluation.py --results ./data/evaluation/results.json

All charts are saved as PNG files to the same directory as results.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Fix for Windows terminal emoji printing
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# ── Colour Palette ─────────────────────────────────────────────────────────────

COLOURS = {
    "bg": "#0f172a",
    "surface": "#1e293b",
    "text": "#e2e8f0",
    "muted": "#94a3b8",
    "accent": "#6366f1",
    "green": "#22c55e",
    "amber": "#f59e0b",
    "red": "#ef4444",
    "blue": "#3b82f6",
    "purple": "#a855f7",
    "pink": "#ec4899",
    "cyan": "#06b6d4",
}

METRIC_COLOURS = [
    COLOURS["accent"],    # Ctx Relevance
    COLOURS["green"],     # Faithfulness
    COLOURS["blue"],      # Ans Relevance
    COLOURS["amber"],     # RAG Score
    COLOURS["purple"],    # Precision
    COLOURS["pink"],      # Recall
    COLOURS["cyan"],      # F1
]

METRIC_LABELS = [
    "Ctx Relevance",
    "Faithfulness",
    "Ans Relevance",
    "RAG Score",
    "Precision",
    "Recall",
    "F1 Score",
]


def _style_axes(ax):
    """Apply dark-theme styling to an axes object."""
    ax.set_facecolor(COLOURS["surface"])
    ax.tick_params(colors=COLOURS["text"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(COLOURS["muted"])


def _load_results(path: Path) -> dict:
    """Load and return the results.json contents."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Chart 1: Summary Bar Chart ────────────────────────────────────────────────

def plot_summary_bars(data: dict, output_dir: Path) -> Path:
    """Generate aggregate summary bar chart with threshold lines."""
    summary = data["summary"]
    metrics = {
        "Context\nRelevance": summary["avg_context_relevance"],
        "Faithful-\nness": summary["avg_faithfulness"],
        "Answer\nRelevance": summary["avg_answer_relevance"],
        "RAG\nScore": summary["avg_rag_score"],
        "Precision": summary["avg_precision"],
        "Recall": summary["avg_recall"],
        "F1\nScore": summary["avg_f1_score"],
        "Cosine\nSimilarity": summary["avg_cosine_similarity"],
    }

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(COLOURS["bg"])
    _style_axes(ax)

    names = list(metrics.keys())
    values = list(metrics.values())
    bar_colours = [
        COLOURS["green"] if v >= 0.8 else COLOURS["amber"] if v >= 0.6 else COLOURS["red"]
        for v in values
    ]

    bars = ax.bar(names, values, color=bar_colours, width=0.6, edgecolor="none",
                  zorder=3, alpha=0.9)

    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
            f"{val:.0%}", ha="center", va="bottom",
            fontsize=10, fontweight="bold", color=COLOURS["text"],
        )

    # Threshold lines
    ax.axhline(y=0.8, color=COLOURS["green"], linestyle="--", alpha=0.5, linewidth=1,
               label="Good (≥80%)")
    ax.axhline(y=0.6, color=COLOURS["amber"], linestyle="--", alpha=0.5, linewidth=1,
               label="Acceptable (≥60%)")

    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score", color=COLOURS["text"], fontsize=10)
    ax.set_title("Aggregate Evaluation Metrics",
                 color=COLOURS["text"], fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="upper right", fontsize=8, facecolor=COLOURS["surface"],
              edgecolor=COLOURS["muted"], labelcolor=COLOURS["text"])
    ax.grid(axis="y", alpha=0.15, color=COLOURS["muted"])

    out = output_dir / "chart_summary.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=COLOURS["bg"])
    plt.close(fig)
    print(f"  ✅ Summary chart  → {out}")
    return out


# ── Chart 2: Per-Question Bar Chart ───────────────────────────────────────────

def plot_per_question_bars(data: dict, output_dir: Path) -> Path:
    """Generate grouped bar chart showing all metrics per question."""
    records = data["records"]
    n = len(records)
    q_ids = [r["question_id"] for r in records]

    metric_keys = [
        "context_relevance_score", "faithfulness_score", "answer_relevance_score",
        "rag_score", "precision", "recall", "f1_score",
    ]

    fig, ax = plt.subplots(figsize=(max(14, n * 1.5), 6))
    fig.patch.set_facecolor(COLOURS["bg"])
    _style_axes(ax)

    x = np.arange(n)
    width = 0.11
    offsets = np.arange(len(metric_keys)) - len(metric_keys) / 2 + 0.5

    for i, (key, label, colour) in enumerate(zip(metric_keys, METRIC_LABELS, METRIC_COLOURS)):
        values = [r.get(key, 0) for r in records]
        ax.bar(x + offsets[i] * width, values, width, label=label,
               color=colour, alpha=0.85, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(q_ids, fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score", color=COLOURS["text"], fontsize=10)
    ax.set_xlabel("Question", color=COLOURS["text"], fontsize=10)
    ax.set_title("Per-Question Metric Breakdown",
                 color=COLOURS["text"], fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="upper right", ncol=4, fontsize=7, facecolor=COLOURS["surface"],
              edgecolor=COLOURS["muted"], labelcolor=COLOURS["text"])
    ax.grid(axis="y", alpha=0.15, color=COLOURS["muted"])

    out = output_dir / "chart_per_question.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=COLOURS["bg"])
    plt.close(fig)
    print(f"  ✅ Per-question   → {out}")
    return out


# ── Chart 3: Heatmap ──────────────────────────────────────────────────────────

def plot_heatmap(data: dict, output_dir: Path) -> Path:
    """Generate a Questions × Metrics heatmap."""
    records = data["records"]
    q_ids = [r["question_id"] for r in records]

    metric_keys = [
        "context_relevance_score", "faithfulness_score", "answer_relevance_score",
        "rag_score", "precision", "recall", "f1_score", "cosine_similarity",
    ]
    metric_labels = METRIC_LABELS + ["Cos. Similarity"]

    matrix = np.array([
        [r.get(k, 0) for k in metric_keys]
        for r in records
    ])

    fig, ax = plt.subplots(figsize=(12, max(4, len(records) * 0.5 + 1)))
    fig.patch.set_facecolor(COLOURS["bg"])
    ax.set_facecolor(COLOURS["surface"])

    # Custom colourmap: red → amber → green
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "rag_cmap", [COLOURS["red"], COLOURS["amber"], COLOURS["green"]]
    )

    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(np.arange(len(metric_labels)))
    ax.set_xticklabels(metric_labels, fontsize=8, rotation=35, ha="right",
                       color=COLOURS["text"])
    ax.set_yticks(np.arange(len(q_ids)))
    ax.set_yticklabels(q_ids, fontsize=9, color=COLOURS["text"])

    # Add score text in each cell
    for i in range(len(q_ids)):
        for j in range(len(metric_labels)):
            val = matrix[i, j]
            text_colour = "#000" if val >= 0.6 else "#fff"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=8, fontweight="bold", color=text_colour)

    ax.set_title("Evaluation Heatmap (Questions x Metrics)",
                 color=COLOURS["text"], fontsize=14, fontweight="bold", pad=15)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.ax.tick_params(colors=COLOURS["text"], labelsize=8)
    cbar.set_label("Score", color=COLOURS["text"], fontsize=9)

    out = output_dir / "chart_heatmap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=COLOURS["bg"])
    plt.close(fig)
    print(f"  ✅ Heatmap        → {out}")
    return out


# ── Chart 4: Radar Chart ──────────────────────────────────────────────────────

def plot_radar(data: dict, output_dir: Path) -> Path:
    """Generate a radar (spider) chart of aggregate metric scores."""
    summary = data["summary"]

    labels = [
        "Context Relevance", "Faithfulness", "Answer Relevance",
        "Precision", "Recall", "F1 Score", "Cosine Similarity",
    ]
    values = [
        summary["avg_context_relevance"],
        summary["avg_faithfulness"],
        summary["avg_answer_relevance"],
        summary["avg_precision"],
        summary["avg_recall"],
        summary["avg_f1_score"],
        summary["avg_cosine_similarity"],
    ]

    n_metrics = len(labels)
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    values_plot = values + [values[0]]   # Close the polygon
    angles += [angles[0]]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(COLOURS["bg"])
    ax.set_facecolor(COLOURS["surface"])

    # Plot data
    ax.plot(angles, values_plot, "o-", linewidth=2, color=COLOURS["accent"],
            markersize=6, zorder=3)
    ax.fill(angles, values_plot, alpha=0.2, color=COLOURS["accent"])

    # Reference circles
    for threshold, colour, label in [
        (0.8, COLOURS["green"], "Good"),
        (0.6, COLOURS["amber"], "Acceptable"),
    ]:
        circle_vals = [threshold] * (n_metrics + 1)
        ax.plot(angles, circle_vals, "--", color=colour, alpha=0.4, linewidth=1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8, color=COLOURS["text"])
    ax.set_ylim(0, 1)
    ax.set_rticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.tick_params(colors=COLOURS["muted"], labelsize=7)
    ax.grid(color=COLOURS["muted"], alpha=0.3)
    ax.spines["polar"].set_color(COLOURS["muted"])

    # Add value labels
    for angle, value in zip(angles[:-1], values):
        ax.text(angle, value + 0.07, f"{value:.0%}", ha="center", va="center",
                fontsize=9, fontweight="bold", color=COLOURS["text"])

    ax.set_title("Aggregate Metric Radar",
                 color=COLOURS["text"], fontsize=14, fontweight="bold",
                 pad=25)

    out = output_dir / "chart_radar.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=COLOURS["bg"])
    plt.close(fig)
    print(f"  ✅ Radar chart    → {out}")
    return out


# ── Main Entry Point ──────────────────────────────────────────────────────────

def generate_all_charts(results_path: Path) -> list[Path]:
    """
    Generate all evaluation charts from a results.json file.

    Args:
        results_path: Path to the evaluation results JSON file.

    Returns:
        List of paths to the generated chart PNG files.
    """
    data = _load_results(results_path)
    output_dir = results_path.parent

    charts = [
        plot_summary_bars(data, output_dir),
        plot_per_question_bars(data, output_dir),
        plot_heatmap(data, output_dir),
        plot_radar(data, output_dir),
    ]

    return charts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate evaluation charts from results.json."
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("./data/evaluation/results.json"),
        help="Path to evaluation results JSON (default: ./data/evaluation/results.json)",
    )
    args = parser.parse_args()

    if not args.results.exists():
        print(f"❌ Results file not found: {args.results}")
        print("   Run `python evaluate.py` first to generate results.")
        sys.exit(1)

    print(f"\n📈 Generating evaluation charts from {args.results} …\n")
    charts = generate_all_charts(args.results)
    print(f"\n✅ Generated {len(charts)} charts in {args.results.parent}\n")


if __name__ == "__main__":
    main()
