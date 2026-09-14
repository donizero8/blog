"""Download a user-provided public HTTPS image without following redirects or DNS rebinding."""

import hashlib
import http.client
import ipaddress
import socket
from io import BytesIO
from urllib.parse import urlsplit

from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

from .forms import optimize_uploaded_image

MAX_COVER_BYTES = 5 * 1024 * 1024
MAX_COVER_PIXELS = 25_000_000


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address, **kwargs):
        super().__init__(host, **kwargs)
        self.address = address

    def connect(self):
        self.sock = socket.create_connection(
            (self.address, self.port), self.timeout, self.source_address
        )
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


def validate_cover_url(value):
    try:
        parsed = urlsplit(value.strip())
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
            or len(value) > 2048
        ):
            raise ValueError
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        ips = {item[4][0] for item in addresses}
        if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
            raise ValueError
    except (ValueError, OSError) as exc:
        raise ValueError("Gunakan URL HTTPS gambar di server publik, bukan alamat lokal.") from exc
    return parsed, sorted(ips)[0]


def download_cover_url(value):
    parsed, address = validate_cover_url(value)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    connection = PinnedHTTPSConnection(parsed.hostname, address, port=443, timeout=8)
    try:
        connection.request("GET", path, headers={"User-Agent": "DonyNotebook/1.0", "Accept": "image/*"})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError("URL gambar tidak dapat diunduh (redirect tidak diikuti).")
        if not response.getheader("Content-Type", "").lower().startswith("image/"):
            raise ValueError("URL tidak mengembalikan file gambar.")
        content_length = response.getheader("Content-Length")
        if content_length and int(content_length) > MAX_COVER_BYTES:
            raise ValueError("Ukuran gambar maksimal 5 MB.")
        payload = response.read(MAX_COVER_BYTES + 1)
        if len(payload) > MAX_COVER_BYTES:
            raise ValueError("Ukuran gambar maksimal 5 MB.")
    except (OSError, TimeoutError) as exc:
        raise ValueError("Gambar tidak dapat diunduh. Periksa URL dan coba lagi.") from exc
    finally:
        connection.close()

    try:
        with Image.open(BytesIO(payload)) as image:
            if image.width * image.height > MAX_COVER_PIXELS:
                raise ValueError("Resolusi gambar terlalu besar.")
            image.verify()
        filename = hashlib.sha256(value.encode()).hexdigest()[:16]
        return optimize_uploaded_image(
            ContentFile(payload, name=f"cover-{filename}.img"), (300, 424), "cover"
        )
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError("URL tidak berisi gambar yang valid.") from exc
