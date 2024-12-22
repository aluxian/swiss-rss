import base64
from io import BytesIO

import pytest
import requests
import requests_mock
from PIL import Image

from .favicon_parser import (
    decode_base64_image,
    download_favicon,
    convert_to_png,
    resize_favicon,
)


@pytest.fixture
def mock_favicon_data():
    # Create a small red square image
    img = Image.new("RGB", (16, 16), color="red")
    img_io = BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)
    return img_io.getvalue()


@pytest.fixture
def mock_html_with_favicon():
    return """
    <html>
    <head>
        <link rel="icon" href="/favicon.ico" type="image/x-icon">
    </head>
    <body></body>
    </html>
    """


def test_download_favicon_with_path(mock_favicon_data, mock_html_with_favicon):
    with requests_mock.Mocker() as m:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml;q=0.8,application/atom+xml;q=0.7,*/*;q=0.6",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Charset": "utf-8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        url = "http://blog.example.com/post/123"

        # Mock all domain variations
        m.get(url, text=mock_html_with_favicon, request_headers=headers)
        m.get(
            "http://blog.example.com",
            text=mock_html_with_favicon,
            request_headers=headers,
        )
        m.get(
            "http://example.com", text=mock_html_with_favicon, request_headers=headers
        )

        # Mock favicon URL
        m.get(
            "http://blog.example.com/favicon.ico",
            content=mock_favicon_data,
            request_headers=headers,
        )

        result = download_favicon("http://blog.example.com/post/123")
        assert result != b""
        img = Image.open(BytesIO(result))
        assert img.format == "PNG"
        assert img.size == (32, 32)


def test_download_favicon_fallback_to_root(mock_favicon_data, mock_html_with_favicon):
    with requests_mock.Mocker() as m:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml;q=0.8,application/atom+xml;q=0.7,*/*;q=0.6",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Charset": "utf-8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        # First attempt fails
        m.get("http://blog.example.com/post/123", status_code=404)
        # Root domain succeeds
        m.get(
            "http://blog.example.com",
            text=mock_html_with_favicon,
            request_headers=headers,
        )
        m.get(
            "http://blog.example.com/",
            text=mock_html_with_favicon,
            request_headers=headers,
        )
        m.get(
            "http://blog.example.com/favicon.ico",
            content=mock_favicon_data,
            request_headers=headers,
        )

        result = download_favicon("http://blog.example.com/post/123")
        assert result != b""
        img = Image.open(BytesIO(result))
        assert img.format == "PNG"
        assert img.size == (32, 32)


def test_download_favicon_fallback_to_main_domain(
    mock_favicon_data, mock_html_with_favicon
):
    with requests_mock.Mocker() as m:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml;q=0.8,application/atom+xml;q=0.7,*/*;q=0.6",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Charset": "utf-8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        # First attempts fail
        m.get("http://blog.example.com/post/123", status_code=404)
        m.get("http://blog.example.com", status_code=404)
        m.get("http://blog.example.com/", status_code=404)
        # Main domain succeeds
        m.get(
            "http://example.com", text=mock_html_with_favicon, request_headers=headers
        )
        m.get(
            "http://example.com/", text=mock_html_with_favicon, request_headers=headers
        )
        m.get(
            "http://example.com/favicon.ico",
            content=mock_favicon_data,
            request_headers=headers,
        )

        result = download_favicon("http://blog.example.com/post/123")
        assert result != b""
        img = Image.open(BytesIO(result))
        assert img.format == "PNG"
        assert img.size == (32, 32)


def test_download_favicon_no_favicon_link(mock_favicon_data):
    html_without_favicon = "<html><head></head><body></body></html>"
    with requests_mock.Mocker() as m:
        m.get("http://example.com", text=html_without_favicon)
        m.get("http://example.com/favicon.ico", content=mock_favicon_data)
        result = download_favicon("http://example.com")
        assert result != b""
        # Verify that the result is a valid PNG
        img = Image.open(BytesIO(result))
        assert img.format == "PNG"
        assert img.size == (32, 32)  # Check if it's resized to 32x32


def test_download_favicon_network_error():
    with requests_mock.Mocker() as m:
        m.get("http://example.com", exc=requests.exceptions.RequestException)
        with pytest.raises(requests.exceptions.RequestException):
            download_favicon("http://example.com")


def test_convert_to_png(mock_favicon_data):
    png_data = convert_to_png(mock_favicon_data)
    assert png_data != b""
    # Verify that the converted data is a valid PNG
    img = Image.open(BytesIO(png_data))
    assert img.format == "PNG"


def test_convert_to_png_error():
    invalid_data = b"This is not a valid image"
    result = convert_to_png(invalid_data)
    assert result == b""


def test_resize_favicon(mock_favicon_data):
    resized_data = resize_favicon(mock_favicon_data)
    assert resized_data != b""
    # Verify that the resized data is a valid PNG
    img = Image.open(BytesIO(resized_data))
    assert img.format == "PNG"
    assert img.size == (32, 32)  # Check if it's resized to 32x32


def test_resize_favicon_error():
    invalid_data = b"This is not a valid image"
    result = resize_favicon(invalid_data)
    assert result == b""


def test_decode_base64_image_valid():
    # Create a simple 1x1 transparent PNG in base64
    png_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    data_url = f"data:image/png;base64,{png_data}"

    result = decode_base64_image(data_url)
    assert result == base64.b64decode(png_data)


def test_decode_base64_image_no_comma():
    result = decode_base64_image("data:image/png;base64foobar")
    assert result == b""


def test_decode_base64_image_invalid_base64():
    result = decode_base64_image("data:image/png;base64,not-valid-base64!")
    assert result == b""


def test_decode_base64_image_empty():
    result = decode_base64_image("")
    assert result == b""


def test_decode_svg_data_url():
    svg_data = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' stroke='black' stroke-width='3' fill='red'/></svg>"
    result = decode_base64_image(svg_data)
    assert result != b""
    # Verify the result is a valid PNG
    img = Image.open(BytesIO(result))
    assert img.format == "PNG"
    assert img.mode == "RGBA"  # Should be converted to RGBA
