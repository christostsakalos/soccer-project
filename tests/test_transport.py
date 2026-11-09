from types import SimpleNamespace
import pytest
from football_similarity.transport import reader_class


class FakeFBref:
    no_store = False


def test_plain_transport_stops_challenge_without_caching(tmp_path, monkeypatch):
    monkeypatch.setattr("football_similarity.transport.time.sleep", lambda _: None)
    calls = []
    def get(*args, **kwargs):
        calls.append(args)
        return SimpleNamespace(text="Verify you are human", raise_for_status=lambda: None)
    monkeypatch.setattr("football_similarity.transport.requests.get", get)
    reader = reader_class(SimpleNamespace(FBref=FakeFBref))()
    path = tmp_path / "page.html"
    with pytest.raises(PermissionError, match="blocked"):
        reader._download_and_save("https://example.test", path)
    assert not path.exists()
    assert len(calls) == 1


def test_plain_transport_preserves_response(tmp_path, monkeypatch):
    monkeypatch.setattr("football_similarity.transport.time.sleep", lambda _: None)
    response = SimpleNamespace(text="<html>data</html>", content=b"<html>data</html>", raise_for_status=lambda: None)
    monkeypatch.setattr("football_similarity.transport.requests.get", lambda *a, **kw: response)
    reader = reader_class(SimpleNamespace(FBref=FakeFBref))()
    path = tmp_path / "page.html"
    assert reader._download_and_save("https://example.test", path).read() == path.read_bytes()
