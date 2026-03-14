import os
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import yaml

with open("config.yml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

MAPS_DIR = CONFIG["paths"]["maps_dir"]
MAX_SIZE = CONFIG["maps"]["max_size_mb"]
ALLOWED = tuple(CONFIG["maps"]["allowed_extensions"])


def sha1_file(path):

    h = hashlib.sha1()

    with open(path, "rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            h.update(data)

    return h.hexdigest()


def progress_bar(percent):

    filled = int(percent / 5)
    empty = 20 - filled

    return "█" * filled + "░" * empty


def download_epicwar(url, progress_callback=None):

    os.makedirs(MAPS_DIR, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0"}

    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")

    download_href = None
    filename = None

    for a in soup.find_all("a", href=True):

        text = a.get_text(strip=True)

        if text.startswith("Download"):

            name = text.replace("Download", "").strip()

            if name.lower().endswith(ALLOWED):

                filename = name
                download_href = a["href"]
                break

    if not filename:
        raise Exception("No se encontró el mapa")

    file_url = urljoin(url, download_href)

    r = requests.get(file_url, stream=True)

    total = int(r.headers.get("content-length", 0))

    path = os.path.join(MAPS_DIR, filename)

    downloaded = 0
    start = time.time()
    last_update = 0

    with open(path, "wb") as f:

        for chunk in r.iter_content(65536):

            if chunk:

                f.write(chunk)
                downloaded += len(chunk)

                if downloaded > MAX_SIZE * 1024 * 1024:
                    f.close()
                    os.remove(path)
                    raise Exception("Mapa excede tamaño permitido")

                now = time.time()

                if progress_callback and now - last_update > 4:

                    elapsed = now - start
                    speed = downloaded / elapsed if elapsed > 0 else 0

                    percent = int(downloaded / total * 100) if total else 0

                    remaining = total - downloaded
                    eta = remaining / speed if speed > 0 else 0

                    progress_callback(
                        percent,
                        downloaded,
                        total,
                        speed,
                        eta
                    )

                    last_update = now

    file_hash = sha1_file(path)

    return filename, downloaded, file_hash