"""HTTP server for the in-memory URL shortener."""

from __future__ import annotations

import argparse
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable
from src.shortener import Shortener


class ShortenerRequestHandler(BaseHTTPRequestHandler):
    server: ShortenerHTTPServer

    def do_GET(self) -> None:
        if self.path == "/":
            self._send_html(
                200,
                '<h1>URL Shortener</h1>'
                '<form method="post" action="/shorten">'
                '<label>URL <input type="url" name="url" required></label>'
                '<button type="submit">Shorten</button>'
                "</form>",
            )
            return

        if self.path == "/table":
            self._send_html(200, self._render_table())
            return

        if self.path.startswith("/s/"):
            code = self.path[len("/s/") :]
            url = self.server.shortener.expand(code)
            if url is None:
                self.send_error(404, "Short URL not found")
                return
            self.send_response(302)
            self.send_header("Location", url)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/shorten":
            self.send_error(404)
            return

        content_length = self.headers.get("Content-Length")
        try:
            body_length = int(content_length) if content_length is not None else -1
        except ValueError:
            self.send_error(400, "Invalid form body")
            return
        if body_length < 0:
            self.send_error(400, "Invalid form body")
            return

        encoded_body = self.rfile.read(body_length).decode("utf-8", errors="replace")
        url = ""
        for field, value in parse_qsl(encoded_body, keep_blank_values=True):
            if field == "url":
                url = value
                break

        try:
            code = self.server.shortener.shorten(url)
        except ValueError as error:
            message = html.escape(str(error))
            self._send_html(
                400,
                "<h1>Invalid URL</h1>"
                f"<p>{message}</p>",
            )
            return
        except OverflowError:
            self._send_html(
                503,
                "<h1>Service Unavailable</h1>"
                "<p>테이블이 가득 찼습니다</p>",
            )
            return

        short_url = self._short_url(code)
        escaped_url = html.escape(self.server.shortener.expand(code))
        escaped_short_url = html.escape(short_url, quote=True)
        self._send_html(
            200,
            "<h1>Short URL created</h1>"
            f'<p>Original URL: <a href="{escaped_url}">{escaped_url}</a></p>'
            f'<p>Short URL: <a href="{escaped_short_url}">'
            f"{escaped_short_url}</a></p>",
        )

    def _short_url(self, code: str) -> str:
        host = self.headers.get("X-Forwarded-Host") or self.headers.get(
            "Host", "localhost"
        )
        scheme = self.headers.get("X-Forwarded-Proto") or "http"
        return f"{scheme}://{host}/s/{code}"

    def _render_table(self) -> str:
        table = self.server.shortener.table
        sections = [
            "<h1>Hash table</h1>",
            f"<p>Table type: {self.server.table_type}</p>",
            f"<p>Load factor: {table.load_factor():.4f}</p>",
        ]
        if isinstance(table, LinearProbingHashTable):
            sections.extend(self._render_linear_table(table))
            return "".join(sections)

        for bucket_index, first_node in table.iter_buckets():
            sections.append(f"<section><h2>Bucket {bucket_index}</h2><div>")
            node = first_node
            if node is None:
                sections.append("NULL")
            while node is not None:
                key = html.escape(node.key)
                code = html.escape(str(node.value))
                short_url = html.escape(self._short_url(str(node.value)), quote=True)
                sections.append(
                    '<article class="node">'
                    f"<p>URL: <code>{key}</code></p>"
                    f"<p>Code: <code>{code}</code></p>"
                    f'<p>Short URL: <a href="{short_url}">{short_url}</a></p>'
                    f"{self._render_hash_trace(node.key)}"
                    "</article> → "
                )
                node = node.next
            if first_node is not None:
                sections.append("NULL")
            sections.append("</div></section>")
        return "".join(sections)

    def _render_linear_table(self, table: LinearProbingHashTable) -> list[str]:
        sections = []
        for slot_index, slot in enumerate(table.slots):
            sections.append(f"<section><h2>Slot {slot_index}</h2><div>")
            if slot is None:
                sections.append("빈칸")
            else:
                key, value = slot
                escaped_key = html.escape(key)
                escaped_code = html.escape(str(value))
                short_url = html.escape(self._short_url(str(value)), quote=True)
                sections.append(
                    '<article class="slot">'
                    f"<p>URL: <code>{escaped_key}</code></p>"
                    f"<p>Code: <code>{escaped_code}</code></p>"
                    f'<p>Short URL: <a href="{short_url}">'
                    f"{short_url}</a></p>"
                    f"{self._render_hash_trace(key)}"
                    f"{self._render_probe_trace(key)}"
                    "</article>"
                )
            sections.append("</div></section>")
        return sections

    def _render_probe_trace(self, key: str) -> str:
        table = self.server.shortener.table
        if not isinstance(table, LinearProbingHashTable):
            raise TypeError("probe traces require a linear probing table")

        start = table.bucket_index(key)
        _, probes = table.find(key)
        probe_indices = [
            (start + offset) % table.capacity for offset in range(probes)
        ]
        steps = []
        for index in probe_indices:
            slot = table.slots[index]
            state = (
                "match" if slot is not None and slot[0] == key else "different key"
            )
            steps.append(f"<li>Slot {index}: {state}</li>")
        order = " → ".join(str(index) for index in probe_indices)
        return (
            "<details><summary>Probe sequence</summary>"
            f"<p>Probe order: {order}</p><ol>{''.join(steps)}</ol></details>"
        )

    def _render_hash_trace(self, key: str) -> str:
        table = self.server.shortener.table
        trace = table.hash_trace(key)
        starting_slot = table.bucket_index(key)
        steps = ["<li>initial h = 0</li>"]
        for character, previous, value in trace:
            escaped_character = html.escape(character)
            steps.append(
                f"<li>{escaped_character}: h = (31 × {previous} + "
                f"{ord(character)}) % {table.capacity} = {value}</li>"
            )
        return (
            "<details><summary>Hash calculation</summary><ol>"
            f'{"".join(steps)}</ol>'
            f"<p>Starting slot: {starting_slot}</p></details>"
        )

    def _send_html(self, status: int, content: str) -> None:
        body = (
            '<!doctype html><html lang="en"><meta charset="utf-8"><body>'
            f"{content}</body></html>"
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ShortenerHTTPServer(HTTPServer):
    def __init__(
        self, server_address: tuple[str, int], table_type: str = "chaining"
    ) -> None:
        if table_type == "chaining":
            table = HashTable(capacity=13)
        elif table_type == "linear":
            table = LinearProbingHashTable(capacity=13)
        else:
            raise ValueError(f"unknown table type: {table_type}")
        self.table_type = table_type
        self.shortener = Shortener(table)
        super().__init__(server_address, ShortenerRequestHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--table", choices=("chaining", "linear"), default="chaining"
    )
    arguments = parser.parse_args()
    with ShortenerHTTPServer(
        ("0.0.0.0", arguments.port), table_type=arguments.table
    ) as server:
        print(f"Serving on http://0.0.0.0:{arguments.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
