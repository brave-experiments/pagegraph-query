from __future__ import annotations

from tests.cases.abc.base import PageGraphBaseTestClass


def do_headers_contain_cookies(headers: list[tuple[str, str]]) -> bool:
    for name, _ in headers:
        if name == "cookie":
            return True
    return False

class RequestsCookiesTestCase(PageGraphBaseTestClass):
    NAME = "gen/requests-cookies"

    def test_img_request_cookies(self) -> None:
        # Check that there are two image requests in the graph
        img_request_edges_cookies_no = None
        img_request_edges_cookies_yes = None
        for request_edge in self.graph.request_start_edges():
            if "assets/img/blue.png?cookie=yes" in request_edge.url():
                img_request_edges_cookies_yes = request_edge
                continue
            if "assets/img/blue.png?cookie=no" in request_edge.url():
                img_request_edges_cookies_no = request_edge
                continue
        self.assertIsNotNone(img_request_edges_cookies_yes)
        self.assertIsNotNone(img_request_edges_cookies_no)
        assert img_request_edges_cookies_yes
        assert img_request_edges_cookies_no

        yes_request_headers = img_request_edges_cookies_yes.headers()
        self.assertIsNotNone(yes_request_headers)
        assert yes_request_headers
        self.assertTrue(do_headers_contain_cookies(yes_request_headers))

        no_request_headers = img_request_edges_cookies_no.headers()
        self.assertIsNotNone(no_request_headers)
        assert no_request_headers
        self.assertFalse(do_headers_contain_cookies(no_request_headers))
