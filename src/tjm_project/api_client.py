# """Fetches posts from JSONPlaceholder and formats them for Notepad."""
# from __future__ import annotations

# from typing import TypedDict
# import ssl
# import requests
# from requests.adapters import HTTPAdapter

# from tjm_project import config


# class Post(TypedDict):
#     id: int
#     title: str
#     body: str


# class TLSAdapter(HTTPAdapter):
#     """
#     A custom HTTP adapter that configures the SSL context to enforce 
#     modern TLS versions, preventing intermediate firewalls or edge servers 
#     from dropping the handshake.
#     """
#     def init_poolmanager(self, *args, **kwargs):
#         ctx = ssl.create_default_context()
#         ctx.minimum_version = ssl.TLSVersion.TLSv1_2
#         ctx.set_ciphers('DEFAULT@SECLEVEL=1')
#         kwargs['ssl_context'] = ctx
#         return super().init_poolmanager(*args, **kwargs)


# def fetch_posts(limit: int = config.NUM_POSTS) -> list[Post]:
#     """GET posts from JSONPlaceholder using a hardened session and return the first `limit` of them."""
#     session = requests.Session()
#     session.mount('https://', TLSAdapter())
#     session.headers.update({
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#         "Accept": "application/json"
#     })
    
#     resp = session.get(config.POSTS_API_URL, timeout=30)
#     resp.raise_for_status()
#     data = resp.json()
#     return [
#         {"id": p["id"], "title": p["title"], "body": p["body"]}
#         for p in data[:limit]
#     ]


# def format_post(post: Post) -> str:
#     """Format a post exactly as required: 'Title: {title}\\n\\n{body}'."""
#     return f"Title: {post['title']}\n\n{post['body']}"


# def output_path_for(post: Post):
#     config.ensure_dirs()
#     return config.OUTPUT_DIR / f"post_{post['id']}.txt"


"""Fetches posts from JSONPlaceholder and formats them for Notepad."""
from __future__ import annotations

from typing import TypedDict
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from tjm_project import config


class Post(TypedDict):
    id: int
    title: str
    body: str


class TLSAdapter(HTTPAdapter):
    """
    A custom HTTP adapter configured with automatic retries and 
    hardened modern TLS versions to handle network drops gracefully.
    """
    def __init__(self, *args, **kwargs):
        # Configure retry strategy to handle intermittent ISP/firewall drops
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        super().__init__(max_retries=retries, *args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def fetch_posts(limit: int = config.NUM_POSTS) -> list[Post]:
    """GET posts from JSONPlaceholder using a retry-enabled session and return the first `limit` of them."""
    session = requests.Session()
    session.mount('https://', TLSAdapter())
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    })
    
    resp = session.get(config.POSTS_API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return [
        {"id": p["id"], "title": p["title"], "body": p["body"]}
        for p in data[:limit]
    ]


def format_post(post: Post) -> str:
    """Format a post exactly as required: 'Title: {title}\\n\\n{body}'."""
    return f"Title: {post['title']}\n\n{post['body']}"


def output_path_for(post: Post):
    config.ensure_dirs()
    return config.OUTPUT_DIR / f"post_{post['id']}.txt"