"""Compare separate chaining and linear probing search costs."""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


CAPACITY = 4093
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
FAILED_QUERY_COUNT = 2000
REPEAT_COUNT = 20
OUTPUT_DIRECTORY = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIRECTORY / "compare_results.csv"
SVG_PATH = OUTPUT_DIRECTORY / "compare.svg"

METRICS = (
    "chaining_success",
    "chaining_failed",
    "linear_success",
    "linear_failed",
)
RESULT_FIELDS = tuple(
    field
    for metric in METRICS
    for field in (
        f"{metric}_average",
        f"{metric}_min",
        f"{metric}_max",
        f"{metric}_theoretical",
    )
)
RESULT_FIELDS = ("alpha", "entries", *RESULT_FIELDS)

def _random_urls(rng: random.Random, count: int, namespace: str) -> list[str]:
    return [
        f"https://{rng.getrandbits(64):016x}.example/"
        f"{namespace}/{index}/{rng.getrandbits(64):016x}"
        for index in range(count)
    ]


def _measure() -> list[dict[str, float | int]]:
    largest_entry_count = round(max(LOAD_FACTORS) * CAPACITY)
    results: list[dict[str, float | int]] = []
    for alpha in LOAD_FACTORS:
        entry_count = round(alpha * CAPACITY)
        measurements = {metric: [] for metric in METRICS}

        for seed in range(REPEAT_COUNT):
            rng = random.Random(seed)
            inserted_urls = _random_urls(rng, largest_entry_count, "insert")
            missing_urls = _random_urls(rng, FAILED_QUERY_COUNT, "missing")
            urls = inserted_urls[:entry_count]
            chaining_table = HashTable(capacity=CAPACITY)
            linear_table = LinearProbingHashTable(capacity=CAPACITY)

            for index, url in enumerate(urls):
                chaining_table.put(url, index)
                linear_table.put(url, index)

            measurements["chaining_success"].append(
                sum(chaining_table.find(url)[1] for url in urls) / entry_count
            )
            measurements["linear_success"].append(
                sum(linear_table.find(url)[1] for url in urls) / entry_count
            )
            measurements["chaining_failed"].append(
                sum(chaining_table.find(url)[1] for url in missing_urls)
                / FAILED_QUERY_COUNT
            )
            measurements["linear_failed"].append(
                sum(linear_table.find(url)[1] for url in missing_urls)
                / FAILED_QUERY_COUNT
            )

        theoretical_values = {
            "chaining_success": 1 + alpha / 2,
            "chaining_failed": alpha,
            "linear_success": 0.5 * (1 + 1 / (1 - alpha)),
            "linear_failed": 0.5 * (1 + 1 / (1 - alpha) ** 2),
        }
        result: dict[str, float | int] = {
            "alpha": alpha,
            "entries": entry_count,
        }
        for metric, values in measurements.items():
            result[f"{metric}_average"] = sum(values) / len(values)
            result[f"{metric}_min"] = min(values)
            result[f"{metric}_max"] = max(values)
            result[f"{metric}_theoretical"] = theoretical_values[metric]
        results.append(result)
    return results


def _write_csv(results: list[dict[str, float | int]]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file, fieldnames=RESULT_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    field: (
                        f"{result[field]:g}"
                        if field == "alpha"
                        else result[field]
                        if field == "entries"
                        else f"{result[field]:.6f}"
                    )
                    for field in RESULT_FIELDS
                }
            )


def _chart(
    results: list[dict[str, float | int]],
    *,
    title: str,
    metric_keys: tuple[str, str],
    theory_keys: tuple[str, str],
    top: int,
    y_min: float,
) -> list[str]:
    left, right = 95, 860
    plot_top, plot_bottom = top + 52, top + 272
    bounds_keys = tuple(
        f"{metric}_{bound}"
        for metric in metric_keys
        for bound in ("min", "max")
    ) + theory_keys
    y_max = max(
        y_min + 1,
        math.ceil(
            max(float(row[key]) for row in results for key in bounds_keys) * 1.1
        ),
    )
    y_ticks = tuple(
        y_min + (y_max - y_min) * tick / 5 for tick in range(6)
    )

    def x_position(alpha: float) -> float:
        return left + (alpha - 0.1) / 0.8 * (right - left)

    def y_position(value: float) -> float:
        return plot_bottom - (value - y_min) / (y_max - y_min) * (
            plot_bottom - plot_top
        )

    def points(key: str) -> str:
        return " ".join(
            f"{x_position(float(row['alpha'])):.1f},"
            f"{y_position(float(row[key])):.1f}"
            for row in results
        )

    series = (
        (metric_keys[0], theory_keys[0], "chain"),
        (metric_keys[1], theory_keys[1], "linear"),
    )
    lines = [
        f'<text x="{left}" y="{top + 23}" class="title">{title}</text>',
    ]
    for tick in y_ticks:
        y = y_position(tick)
        lines.extend(
            (
                f'<line x1="{left}" y1="{y:.1f}" x2="{right}" '
                f'y2="{y:.1f}" class="grid"/>',
                f'<text x="{left - 12}" y="{y + 4:.1f}" '
                f'text-anchor="end" class="tick">{tick:g}</text>',
            )
        )
    for step in range(1, 10):
        alpha = step / 10
        x = x_position(alpha)
        lines.extend(
            (
                f'<line x1="{x:.1f}" y1="{plot_top}" x2="{x:.1f}" '
                f'y2="{plot_bottom}" class="grid"/>',
                f'<text x="{x:.1f}" y="{plot_bottom + 20}" '
                f'text-anchor="middle" class="tick">{alpha:.1f}</text>',
            )
        )

    lines.append(
        f'<line x1="{left}" y1="{plot_bottom}" x2="{right}" '
        f'y2="{plot_bottom}" class="axis"/>'
    )
    for metric, theory, css_class in series:
        average_key = f"{metric}_average"
        lines.append(
            f'<polyline points="{points(average_key)}" '
            f'class="{css_class}-average"/>'
        )
        for row in results:
            x = x_position(float(row["alpha"]))
            low_y = y_position(float(row[f"{metric}_min"]))
            high_y = y_position(float(row[f"{metric}_max"]))
            lines.append(
                f'<line x1="{x:.1f}" y1="{high_y:.1f}" '
                f'x2="{x:.1f}" y2="{low_y:.1f}" '
                f'class="{css_class}-range"/>'
            )
            lines.extend(
                (
                    f'<line x1="{x - 4:.1f}" y1="{high_y:.1f}" '
                    f'x2="{x + 4:.1f}" y2="{high_y:.1f}" '
                    f'class="{css_class}-range"/>',
                    f'<line x1="{x - 4:.1f}" y1="{low_y:.1f}" '
                    f'x2="{x + 4:.1f}" y2="{low_y:.1f}" '
                    f'class="{css_class}-range"/>',
                    f'<circle cx="{x:.1f}" '
                    f'cy="{y_position(float(row[average_key])):.1f}" '
                    f'r="3.5" class="{css_class}-point"/>',
                )
            )
        lines.append(
            f'<polyline points="{points(theory)}" '
            f'class="{css_class}-theory"/>'
        )
    lines.extend(
        (
            f'<text x="22" y="{(plot_top + plot_bottom) / 2:.1f}" '
            f'transform="rotate(-90 22 {(plot_top + plot_bottom) / 2:.1f})" '
            'text-anchor="middle" class="axis-label">'
            "Probes / search</text>",
            f'<text x="{(left + right) / 2:.1f}" '
            f'y="{plot_bottom + 43}" text-anchor="middle" '
            'class="axis-label">Load factor α</text>',
        )
    )
    legend = (
        (500, "Chaining avg/range", "chain", "average"),
        (700, "Chaining theory", "chain", "theory"),
        (500, "Linear avg/range", "linear", "average"),
        (700, "Linear theory", "linear", "theory"),
    )
    for index, (x, label, css_class, line_type) in enumerate(legend):
        y = top + 19 + (index // 2) * 18
        lines.extend(
            (
                f'<line x1="{x}" y1="{y - 4}" x2="{x + 22}" '
                f'y2="{y - 4}" class="{css_class}-{line_type}"/>',
                f'<text x="{x + 27}" y="{y}" class="legend">{label}</text>',
            )
        )
        if line_type == "average":
            lines.extend(
                (
                    f'<circle cx="{x + 11}" cy="{y - 4}" r="3" '
                    f'class="{css_class}-point"/>',
                    f'<line x1="{x + 11}" y1="{y - 8}" '
                    f'x2="{x + 11}" y2="{y}" '
                    f'class="{css_class}-range"/>',
                )
            )
    return lines


def _write_svg(results: list[dict[str, float | int]]) -> None:
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="940" height="760" viewBox="0 0 940 760">',
        "<style>",
        "text{font-family:Arial,sans-serif;fill:#222}",
        ".title{font-size:18px;font-weight:bold}",
        ".tick{font-size:12px;fill:#555}",
        ".axis-label,.legend{font-size:12px}",
        ".grid{stroke:#ddd;stroke-width:1}",
        ".axis{stroke:#555;stroke-width:1.5}",
        ".chain-average{fill:none;stroke:#1769aa;stroke-width:2.5}",
        ".chain-theory{fill:none;stroke:#1769aa;stroke-width:2.5;"
        "stroke-dasharray:7 5}",
        ".linear-average{fill:none;stroke:#d04a35;stroke-width:2.5}",
        ".linear-theory{fill:none;stroke:#d04a35;stroke-width:2.5;"
        "stroke-dasharray:7 5}",
        ".chain-range{stroke:#1769aa;stroke-width:1.5}",
        ".linear-range{stroke:#d04a35;stroke-width:1.5}",
        ".chain-point{fill:#1769aa}",
        ".linear-point{fill:#d04a35}",
        "</style>",
        *_chart(
            results,
            title="Successful searches",
            metric_keys=("chaining_success", "linear_success"),
            theory_keys=(
                "chaining_success_theoretical",
                "linear_success_theoretical",
            ),
            top=12,
            y_min=1,
        ),
        *_chart(
            results,
            title="Unsuccessful searches",
            metric_keys=("chaining_failed", "linear_failed"),
            theory_keys=("chaining_failed_theoretical", "linear_failed_theoretical"),
            top=382,
            y_min=0,
        ),
        "</svg>",
    ]
    SVG_PATH.write_text("\n".join(svg) + "\n", encoding="utf-8")


def _print_table(results: list[dict[str, float | int]]) -> None:
    print(
        f"{'α':>4} {'항목 수':>7} {'체인 성공 avg[min,max]':>25} "
        f"{'이론':>8} {'선형 성공 avg[min,max]':>25} {'이론':>8} "
        f"{'체인 실패 avg[min,max]':>25} {'이론':>8} "
        f"{'선형 실패 avg[min,max]':>25} {'이론':>8}"
    )
    metrics = (
        "chaining_success",
        "linear_success",
        "chaining_failed",
        "linear_failed",
    )
    for result in results:
        formatted_metrics = [
            (
                f"{result[f'{metric}_average']:.4f}"
                f"[{result[f'{metric}_min']:.4f},"
                f"{result[f'{metric}_max']:.4f}]"
            )
            for metric in metrics
        ]
        print(
            f"{result['alpha']:4.1f} {result['entries']:7d} "
            f"{formatted_metrics[0]:>25} "
            f"{result['chaining_success_theoretical']:8.4f} "
            f"{formatted_metrics[1]:>25} "
            f"{result['linear_success_theoretical']:8.4f} "
            f"{formatted_metrics[2]:>25} "
            f"{result['chaining_failed_theoretical']:8.4f} "
            f"{formatted_metrics[3]:>25} "
            f"{result['linear_failed_theoretical']:8.4f}"
        )


def main() -> None:
    results = _measure()
    _write_csv(results)
    _write_svg(results)
    _print_table(results)
    print(f"\nCSV: {CSV_PATH}")
    print(f"SVG: {SVG_PATH}")


if __name__ == "__main__":
    main()
