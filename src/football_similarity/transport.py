"""Plain HTTP adapter: no browser stealth, CAPTCHA solving or proxy rotation.

Uses soccerdata's parser/cache API, verified against soccerdata 2026.43.0.
"""
import io
import time
import requests

_last_request = 0.0
SUPPORTED_CATEGORIES = {"standard", "shooting", "playing_time", "keeper", "misc"}


def reader_class(sd):
    class PlainHTTPFBref(sd.FBref):
        @classmethod
        def _all_leagues(cls):
            return sd.FBref._all_leagues()

        def _init_webdriver(self):
            return None

        def _download_and_save(self, url, filepath=None, var=None):
            global _last_request
            if var is not None:
                raise NotImplementedError("JavaScript retrieval is disabled")
            time.sleep(max(0, 7 - (time.monotonic() - _last_request)))
            _last_request = time.monotonic()
            response = requests.get(url, timeout=30, headers={"User-Agent": "football-player-similarity/0.1 (university research)"})
            response.raise_for_status()
            if any(marker in response.text.lower() for marker in ("verify you are human", "cf-challenge", "captcha", "checking your browser", "just a moment...")):
                raise PermissionError("Access blocked by source challenge; collection stopped")
            if not self.no_store and filepath is not None:
                filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_bytes(response.content)
            return io.BytesIO(response.content)

    return PlainHTTPFBref
