import base64
from io import BytesIO
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger
from PIL import Image, UnidentifiedImageError


def get_domain_variations(url: str) -> list[str]:
    """Generate domain variations from most to least specific."""
    parsed = urlparse(url)
    parts = parsed.netloc.split(".")

    variations = []
    # Full URL first
    variations.append(url)

    # Root domain (no path)
    variations.append(f"{parsed.scheme}://{parsed.netloc}")

    # Try without subdomains if they exist
    if len(parts) > 2:
        main_domain = ".".join(parts[-2:])
        variations.append(f"{parsed.scheme}://{main_domain}")

    return variations


def decode_base64_image(data_url: str) -> bytes:
    """Decode a base64 data URL or inline SVG into bytes"""
    try:
        # Handle inline SVG data URLs
        if data_url.startswith("data:image/svg+xml;utf8,"):
            from cairosvg import svg2png

            svg_content = data_url.split(",", 1)[1]
            return svg2png(bytestring=svg_content.encode())

        # Handle base64 encoded images
        if "," not in data_url:
            return b""
        base64_data = data_url.split(",", 1)[1]
        return base64.b64decode(base64_data)
    except Exception as e:
        logger.error(f"Failed to decode image data URL: {str(e)}")
        return b""


def download_favicon(url: str) -> bytes:
    # Check if the URL is a data URL (base64 or SVG)
    if url.startswith("data:image/"):
        logger.debug("Found data URL favicon")
        return decode_base64_image(url)

    # Try with browser-like headers for maximum compatibility
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml;q=0.8,application/atom+xml;q=0.7,*/*;q=0.6",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Charset": "utf-8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    last_error = None
    for domain in get_domain_variations(url):
        try:
            logger.debug(f"Trying to fetch favicon from: {domain}")
            response = requests.get(domain, timeout=10, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            favicon_url = None
            for link in soup.find_all("link"):
                rel = link.get("rel", [])
                if isinstance(rel, str):
                    rel = [rel]
                if "icon" in rel or "shortcut icon" in rel:
                    favicon_url = link.get("href")
                    break

            if not favicon_url:
                # Try common favicon paths
                favicon_paths = [
                    "/favicon.ico",
                    "/favicon.png",
                    "/assets/favicon.png",
                    "/assets/favicon.ico",
                    "/img/favicon.png",
                    "/img/favicon.ico",
                    "/images/favicon.png",
                    "/images/favicon.ico",
                    "/static/favicon.png",
                    "/static/favicon.ico",
                ]

                for path in favicon_paths:
                    try:
                        favicon_url = urljoin(domain, path)
                        logger.debug(f"Trying favicon path: {favicon_url}")
                        favicon_response = requests.get(
                            favicon_url, timeout=10, headers=headers
                        )
                        favicon_response.raise_for_status()
                        return resize_favicon(favicon_response.content, size=32)
                    except Exception as e:
                        logger.debug(
                            f"Failed to fetch favicon from {favicon_url}: {str(e)}"
                        )
                        continue
            else:
                # Try the favicon URL from the HTML
                favicon_url = urljoin(domain, favicon_url)
                logger.debug(f"Fetching favicon from HTML link: {favicon_url}")
                favicon_response = requests.get(
                    favicon_url, timeout=10, headers=headers
                )
                favicon_response.raise_for_status()
                return resize_favicon(favicon_response.content, size=32)

        except Exception as e:
            last_error = e
            logger.warning(f"Failed to fetch favicon from {domain}: {str(e)}")
            continue

    if last_error:
        raise last_error
    return b""


def resize_favicon(favicon_data: bytes, size: int = 32) -> bytes:
    try:
        with Image.open(BytesIO(favicon_data)) as img:
            img = img.convert("RGBA")
            img = img.resize((size, size), Image.LANCZOS)
            output = BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()
    except UnidentifiedImageError:
        logger.error("Failed to resize favicon: Invalid image data")
        return b""


def convert_to_png(favicon_data: bytes) -> bytes:
    try:
        with Image.open(BytesIO(favicon_data)) as img:
            img = img.convert("RGBA")
            output = BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()
    except UnidentifiedImageError:
        logger.error("Failed to convert image to PNG: Invalid image data")
        return b""
