from urllib.parse import urlparse

from pagegraph.types import Url


LOCAL_FRAME_URLS = (
     "about:blank",
     "about:srcdoc",
)


def is_url_local(url: Url, context_url: Url) -> bool:
    if url in LOCAL_FRAME_URLS:
        return True
    url_parts = urlparse(url)
    context_url_parts = urlparse(context_url)
    if url_parts.netloc == "" or url_parts.netloc == context_url_parts.netloc:
        return True
    return False


def brief_version(value: str, max_length: int = 250) -> str:
    summary = value.replace("\n", "\\n")
    if len(summary) > max_length:
        summary = summary[:50] + "…"
    return summary
