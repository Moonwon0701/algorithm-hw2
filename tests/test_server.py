import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import ShortenerHTTPServer


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = ShortenerHTTPServer(("127.0.0.1", 0))
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=2
        )

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, body=None, headers=None):
        self.connection.request(method, path, body=body, headers=headers or {})
        response = self.connection.getresponse()
        response_body = response.read().decode("utf-8")
        return response.status, response.headers, response_body

    def post_url(self, url, headers=None):
        request_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            **(headers or {}),
        }
        return self.request(
            "POST",
            "/shorten",
            body=urlencode([("url", url)]),
            headers=request_headers,
        )

    def test_home_displays_url_form(self):
        status, _, body = self.request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn('<form method="post" action="/shorten">', body)
        self.assertIn('name="url"', body)

    def test_post_shortens_and_serves_redirect(self):
        url = "https://example.com/path"
        status, _, body = self.post_url(url)

        self.assertEqual(status, 200)
        self.assertIn(url, body)
        self.assertIn(f"http://127.0.0.1:{self.server.server_port}/s/0", body)

        status, headers, _ = self.request("GET", "/s/0")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], url)

    def test_invalid_url_returns_bad_request(self):
        status, _, body = self.post_url("ftp://example.com")

        self.assertEqual(status, 400)
        self.assertIn("HTTP(S)", body)

    def test_unknown_and_malformed_codes_return_not_found(self):
        for path in ("/s/9999", "/s/!"):
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertEqual(status, 404)

    def test_forwarded_host_and_protocol_form_short_link(self):
        status, _, body = self.post_url(
            "https://example.com/path",
            headers={
                "X-Forwarded-Host": "short.example:8443",
                "X-Forwarded-Proto": "https",
            },
        )

        self.assertEqual(status, 200)
        self.assertIn("https://short.example:8443/s/0", body)

    def test_table_displays_chains_and_hash_trace(self):
        status, _, _ = self.post_url("https://example.com/path")

        self.assertEqual(status, 200)
        status, _, body = self.request("GET", "/table")

        self.assertEqual(status, 200)
        self.assertIn("https://example.com/path", body)
        self.assertIn("/s/0", body)
        self.assertIn("→ NULL", body)
        self.assertIn("<details>", body)
        self.assertIn("initial h = 0", body)
        self.assertIn("h: h = (31 × 0 + 104) % 13 = 0", body)

    def test_html_escapes_urls_in_result_and_table(self):
        url = "https://example.com/<script>alert(1)</script>"
        status, _, body = self.post_url(url)

        self.assertEqual(status, 200)
        self.assertIn("&lt;script&gt;", body)
        self.assertNotIn("<script>", body)

        status, _, body = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("&lt;script&gt;", body)
        self.assertNotIn("<script>", body)


if __name__ == "__main__":
    unittest.main()
