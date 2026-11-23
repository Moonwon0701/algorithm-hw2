"""Measure separate-chaining search costs at several table load factors."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from src.hash_table import HashTable


CAPACITY = 4093
LOAD_FACTORS = (0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4)
FAILED_QUERY_COUNT = 2000
RANDOM_SEED = 42
OUTPUT_DIRECTORY = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIRECTORY / "results.csv"
SVG_PATH = OUTPUT_DIRECTORY / "probe_experiment.svg"


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
        table = HashTable(capacity=CAPACITY)
        urls = inserted_urls[:entry_count]

        for index, url in enumerate(urls):
            table.put(url, index)

        successful_comparisons = sum(table.find(url)[1] for url in urls)
        failed_comparisons = sum(
            table.find(url)[1] for url in missing_urls
        )
        results.append(
            {
                "alpha": alpha,
                "entries": entry_count,
                "successful_measured": successful_comparisons / entry_count,
                "successful_theoretical": 1 + alpha / 2,
                "failed_measured": failed_comparisons / FAILED_QUERY_COUNT,
                "failed_theoretical": alpha,
            }
        )
    return results


def _write_csv(results: list[dict[str, float | int]]) -> None:
    fieldnames = (
        "alpha",
        "entries",
        "successful_measured",
        "successful_theoretical",
        "failed_measured",
        "failed_theoretical",
    )
    with CSV_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "alpha": f"{result['alpha']:g}",
                    "entries": result["entries"],
                    "successful_measured": f"{result['successful_measured']:.6f}",
                    "successful_theoretical": f"{result['successful_theoretical']:.6f}",
                    "failed_measured": f"{result['failed_measured']:.6f}",
                    "failed_theoretical": f"{result['failed_theoretical']:.6f}",
                }
            )


def _chart(
    results: list[dict[str, float | int]],
    *,
    title: str,
    measured_key: str,
    theoretical_key: str,
    top: int,
    y_min: float,
    y_max: float,
    y_ticks: tuple[float, ...],
) -> list[str]:
    left, right = 95, 850
    plot_top, plot_bottom = top + 48, top + 267

    def x_position(alpha: float) -> float:
        return left + alpha / max(LOAD_FACTORS) * (right - left)

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

    lines = [
        f'<text x="{left}" y="{top + 22}" class="title">{title}</text>',
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
    for tick in range(5):
        x = x_position(float(tick))
        lines.extend(
            (
                f'<line x1="{x:.1f}" y1="{plot_top}" x2="{x:.1f}" '
                f'y2="{plot_bottom}" class="grid"/>',
                f'<text x="{x:.1f}" y="{plot_bottom + 20}" '
                f'text-anchor="middle" class="tick">{tick}</text>',
            )
        )

    lines.extend(
        (
            f'<line x1="{left}" y1="{plot_bottom}" x2="{right}" '
            f'y2="{plot_bottom}" class="axis"/>',
            f'<polyline points="{points(measured_key)}" '
            'class="measured"/>',
            f'<polyline points="{points(theoretical_key)}" '
            'class="theoretical"/>',
        )
    )
    for row in results:
        for key, css_class in (
            (measured_key, "measured-point"),
            (theoretical_key, "theoretical-point"),
        ):
            lines.append(
                f'<circle cx="{x_position(float(row["alpha"])):.1f}" '
                f'cy="{y_position(float(row[key])):.1f}" r="4" '
                f'class="{css_class}"/>'
            )
    lines.extend(
        (
            f'<text x="22" y="{(plot_top + plot_bottom) / 2:.1f}" '
            f'transform="rotate(-90 22 {(plot_top + plot_bottom) / 2:.1f})" '
            'text-anchor="middle" class="axis-label">'
            "Node comparisons / search</text>",
            f'<text x="{(left + right) / 2:.1f}" '
            f'y="{plot_bottom + 43}" text-anchor="middle" '
            'class="axis-label">Load factor α</text>',
            f'<text x="{right - 190}" y="{top + 20}" '
            'class="legend measured-text">Measured</text>',
            f'<text x="{right - 95}" y="{top + 20}" '
            'class="legend theoretical-text">Theory</text>',
        )
    )
    return lines


def _write_svg(results: list[dict[str, float | int]]) -> None:
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="920" height="720" viewBox="0 0 920 720">',
        "<style>",
        "text{font-family:Arial,sans-serif;fill:#222}",
        ".title{font-size:18px;font-weight:bold}",
        ".tick{font-size:12px;fill:#555}",
        ".axis-label,.legend{font-size:13px}",
        ".grid{stroke:#ddd;stroke-width:1}",
        ".axis{stroke:#555;stroke-width:1.5}",
        ".measured{fill:none;stroke:#1769aa;stroke-width:2.5}",
        ".theoretical{fill:none;stroke:#d04a35;stroke-width:2.5;"
        "stroke-dasharray:7 5}",
        ".measured-point{fill:#1769aa}",
        ".theoretical-point{fill:#d04a35}",
        ".measured-text{fill:#1769aa}",
        ".theoretical-text{fill:#d04a35}",
        "</style>",
        *_chart(
            results,
            title="Successful searches",
            measured_key="successful_measured",
            theoretical_key="successful_theoretical",
            top=12,
            y_min=1,
            y_max=3.25,
            y_ticks=(1, 1.5, 2, 2.5, 3),
        ),
        *_chart(
            results,
            title="Unsuccessful searches",
            measured_key="failed_measured",
            theoretical_key="failed_theoretical",
            top=368,
            y_min=0,
            y_max=4.5,
            y_ticks=(0, 1, 2, 3, 4),
        ),
        "</svg>",
    ]
    SVG_PATH.write_text("\n".join(svg) + "\n", encoding="utf-8")


def _print_table(results: list[dict[str, float | int]]) -> None:
    print(
        f"{'α':>5} {'항목 수':>7} {'성공 측정':>11} {'성공 이론':>11} "
        f"{'실패 측정':>11} {'실패 이론':>11}"
    )
    for result in results:
        print(
            f"{result['alpha']:5g} {result['entries']:7d} "
            f"{result['successful_measured']:11.4f} "
            f"{result['successful_theoretical']:11.4f} "
            f"{result['failed_measured']:11.4f} "
            f"{result['failed_theoretical']:11.4f}"
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
