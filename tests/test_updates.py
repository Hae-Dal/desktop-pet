"""업데이트 내역 표시와 새 버전 확인."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from PyQt5.QtCore import QEventLoop, QTimer

from pet import __version__
from pet.ui import changelog, prefs, updater


def test_changelog_shows_only_released_versions():
    text = "# 업데이트 내역\n<!-- 주석 -->\n## 미반영\n- 비밀\n## 1.2.0 - 날짜\n- 공개\n## 1.1.0 - 날짜\n- 예전\n"
    notes = changelog.released_notes(text)
    assert "비밀" not in notes and "주석" not in notes
    assert notes.startswith("## 1.2.0") and "예전" in notes


def test_first_run_of_a_version_is_detected_once(qapp):
    assert changelog.is_new_version() is True
    assert changelog.is_new_version() is False


@pytest.mark.parametrize("text, expected", [("v0.10.0", (0, 10, 0)), ("1.2.3", (1, 2, 3)), ("v1.2", None), ("x", None)])
def test_parse_version(text, expected):
    assert updater.parse_version(text) == expected


def test_version_numbers_compare_as_numbers():
    assert updater.parse_version("0.10.0") > updater.parse_version("0.9.1")


class FakeGitHub:
    """GitHub 최신 릴리스 API 흉내. tag를 바꾸면 다음 응답부터 반영."""

    def __init__(self):
        self.tag, self.hits = "v99.0.0", 0
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                fake.hits += 1
                body = json.dumps({"tag_name": fake.tag, "html_url": "http://x/" + fake.tag}).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/latest"


@pytest.fixture
def github(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(updater, "LATEST_URL", fake.url)
    yield fake
    fake.server.shutdown()


def wait(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec_()


def test_checker_reports_newer_version_only(qapp, github):
    found = []
    checker = updater.UpdateChecker()
    checker.update_available.connect(lambda v, u: found.append(v))
    checker.check()
    wait(500)
    github.tag = "v" + __version__
    checker.check()
    wait(500)
    assert found == ["99.0.0"]


def test_running_pet_checks_again_and_does_not_repeat(qapp, github, monkeypatch):
    from pet.config import PetConfig
    from pet.ui import pet_widget
    from pet.ui.sprites import SpriteSet
    from pet.ui.world import World
    monkeypatch.setattr(updater, "START_DELAY_MS", 50)
    monkeypatch.setattr(updater, "INTERVAL_MS", 300)
    pet = pet_widget.PetWidget(PetConfig(), SpriteSet({}), World())
    notices = []
    say = pet.ctx.say
    monkeypatch.setattr(pet.ctx, "say", lambda t, n=90: (notices.append(t) if "새 버전" in t else None, say(t, n)))

    wait(800)                                   # 시작 확인 + 다시 확인 2번 정도
    assert github.hits >= 2 and len(notices) == 1 and pet.updates.version == "99.0.0"
    github.tag = "v99.1.0"
    wait(400)
    assert len(notices) == 2 and pet.updates.version == "99.1.0"
    prefs.set_check_updates(False)
    hits = github.hits
    wait(400)
    assert github.hits == hits                  # 끄면 확인 안 함
    pet.close()
    pet.bubble.close()
