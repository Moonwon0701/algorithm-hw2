"""Compare separate chaining and linear probing search costs."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


CAPACITY = 4093
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
FAILED_QUERY_COUNT = 2000
RANDOM_SEED = 42
OUTPUT_DIRECTORY = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIRECTORY / "compare_results.csv"
SVG_PATH = OUTPUT_DIRECTORY / "compare.svg"

RESULT_FIELDS = (
    "alpha",
    "entries",
    "chaining_success_measured",
    "chaining_success_theoretical",
    "chaining_failed_measured",
    "chaining_failed_theoretical",
    "linear_success_measured",
    "linear_success_theoretical",
    "linear_failed_measured",
    "linear_failed_theoretical",
)

def _random_urls(rng: random.Random, count: int, namespace: str) -> list[str]:
    return [
        f"https://{rng.getrandbits(64):016x}.example/"
        f"{namespace}/{index}/{rng.getrandbits(64):016x}"
        for index in range(count)
    ]


def _measure() -> list[dict[str, float | int]]:
    rng = random.Random(RANDOM_SEED)
    largest_entry_count = round(max(LOAD_FACTORS) * CAPACITY)
    inserted_urls = _random_urls(rng, largest_entry_count, "insert")
    missing_urls = _random_urls(rng, FAILED_QUERY_COUNT, "missing")

    results: list[dict[str, float | int]] = []
    for alpha in LOAD_FACTORS:
        entry_count = round(alpha * CAPACITY)
        urls = inserted_urls[:entry_count]
        chaining_table = HashTable(capacity=CAPACITY)
        linear_table = LinearProbingHashTable(capacity=CAPACITY)

        for index, url in enumerate(urls):
            chaining_table.put(url, index)
            linear_table.put(url, index)

        chaining_success = sum(
            chaining_table.find(url)[1] for url in urls
        ) / entry_count
        linear_success = sum(linear_table.find(url)[1] for url in urls) / entry_count
        chaining_failed = sum(
            chaining_table.find(url)[1] for url in missing_urls
        ) / FAILED_QUERY_COUNT
        linear_failed = sum(
            linear_table.find(url)[1] for url in missing_urls
        ) / FAILED_QUERY_COUNT

        results.append(
            {
                "alpha": alpha,
                "entries": entry_count,
                "chaining_success_measured": chaining_success,
                "chaining_success_theoretical": 1 + alpha / 2,
                "chaining_failed_measured": chaining_failed,
                "chaining_failed_theoretical": alpha,
                "linear_success_measured": linear_success,
                "linear_success_theoretical": 0.5
                * (1 + 1 / (1 - alpha)),
                "linear_failed_measured": linear_failed,
                "linear_failed_theoretical": 0.5
                * (1 + 1 / (1 - alpha) ** 2),
            }
        )
    return results


def _write_csv(results: list[dict[str, float | int]]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    field: (
                        f"{result[field]:g}"
                        if field == "alpha"
                        else (
                            result[field]
                            if field == "entries"
                            else f"{result[field]:.6f}"
                        )
                    )
                    for field in RESULT_FIELDS
                }
            )


def _chart(
    results: list[dict[str, float | int]],
    *,
    title: str,
    measured_keys: tuple[str, str],
    theory_keys: tuple[str, str],
    top: int,
    y_min: float,
    y_max: float,
    y_ticks: tuple[float, ...],
) -> list[str]:
    left, right = 95, 860
    plot_top, plot_bottom = top + 52, top + 272

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
        (measured_keys[0], "chain-measured"),
        (theory_keys[0], "chain-theory"),
        (measured_keys[1], "linear-measured"),
        (theory_keys[1], "linear-theory"),
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
    for key, css_class in series:
        lines.append(
            f'<polyline points="{points(key)}" class="{css_class}"/>'
        )
        for row in results:
            lines.append(
                f'<circle cx="{x_position(float(row["alpha"])):.1f}" '
                f'cy="{y_position(float(row[key])):.1f}" r="3.5" '
                f'class="{css_class}-point"/>'
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
        (525, "Chaining measured", "chain-measured"),
        (655, "Chaining theory", "chain-theory"),
        (525, "Linear measured", "linear-measured"),
        (655, "Linear theory", "linear-theory"),
    )
    for index, (x, label, css_class) in enumerate(legend):
        y = top + 19 + (index // 2) * 18
        lines.extend(
            (
                f'<line x1="{x}" y1="{y - 4}" x2="{x + 22}" '
                f'y2="{y - 4}" class="{css_class}"/>',
                f'<text x="{x + 27}" y="{y}" class="legend">{label}</text>',
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
        ".chain-measured{fill:none;stroke:#1769aa;stroke-width:2.5}",
        ".chain-theory{fill:none;stroke:#1769aa;stroke-width:2.5;"
        "stroke-dasharray:7 5}",
        ".linear-measured{fill:none;stroke:#d04a35;stroke-width:2.5}",
        ".linear-theory{fill:none;stroke:#d04a35;stroke-width:2.5;"
        "stroke-dasharray:7 5}",
        ".chain-measured-point{fill:#1769aa}",
        ".chain-theory-point{fill:#1769aa}",
        ".linear-measured-point{fill:#d04a35}",
        ".linear-theory-point{fill:#d04a35}",
        "</style>",
        *_chart(
            results,
            title="Successful searches",
            measured_keys=("chaining_success_measured", "linear_success_measured"),
            theory_keys=(
                "chaining_success_theoretical",
                "linear_success_theoretical",
            ),
            top=12,
            y_min=1,
            y_max=6,
            y_ticks=(1, 2, 3, 4, 5, 6),
        ),
        *_chart(
            results,
            title="Unsuccessful searches",
            measured_keys=("chaining_failed_measured", "linear_failed_measured"),
            theory_keys=("chaining_failed_theoretical", "linear_failed_theoretical"),
            top=382,
            y_min=0,
            y_max=55,
            y_ticks=(0, 10, 20, 30, 40, 50),
        ),
        "</svg>",
    ]
    SVG_PATH.write_text("\n".join(svg) + "\n", encoding="utf-8")


def _print_table(results: list[dict[str, float | int]]) -> None:
    print(
        f"{'α':>4} {'항목 수':>7} {'체이닝 성공':>12} {'성공 이론':>10} "
        f"{'선형 성공':>10} {'성공 이론':>10} {'체이닝 실패':>12} "
        f"{'실패 이론':>10} {'선형 실패':>10} {'실패 이론':>10}"
    )
    for result in results:
        print(
            f"{result['alpha']:4.1f} {result['entries']:7d} "
            f"{result['chaining_success_measured']:12.4f} "
            f"{result['chaining_success_theoretical']:10.4f} "
            f"{result['linear_success_measured']:10.4f} "
            f"{result['linear_success_theoretical']:10.4f} "
            f"{result['chaining_failed_measured']:12.4f} "
            f"{result['chaining_failed_theoretical']:10.4f} "
            f"{result['linear_failed_measured']:10.4f} "
            f"{result['linear_failed_theoretical']:10.4f}"
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
