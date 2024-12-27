from urllib.parse import urlparse
from typing import Optional

from publicsuffix2 import get_sld

from pagegraph.types import Url


LOCAL_FRAME_URLS = (
     "about:blank",
     "about:srcdoc",
)

def is_security_origin_inheriting_url(url: Url) -> bool:
    return url in LOCAL_FRAME_URLS


def are_urls_same_site(url: Url, other_url: Url) -> bool:
    hostname_first = urlparse(url).hostname
    hostname_second = urlparse(other_url).hostname

    if hostname_first == hostname_second:
        return True

    etld1_first = get_sld(hostname_first, strict=True)
    etld1_second = get_sld(hostname_second, strict=True)
    if not etld1_first or not etld1_second:
        return False
    return str(etld1_first) == str(etld1_second)


def is_url_local(url: Url, context_url: Url) -> bool:
    if is_security_origin_inheriting_url(url):
        return True
    url_parts = urlparse(url)
    context_url_parts = urlparse(context_url)
    if url_parts.netloc in ("", context_url_parts.netloc):
        return True
    return False


def security_origin_from_url(url: Url) -> Optional[Url]:
    url_parts = urlparse(url)
    if url_parts.scheme and url_parts.netloc:
        return f"{url_parts.scheme}://{url_parts.netloc}"
    return None
