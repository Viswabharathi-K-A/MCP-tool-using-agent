"""Keep the automated suite independent of credentials and external services."""
import socket
import sys
from types import ModuleType
from unittest.mock import patch

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage


dotenv_patch = patch("dotenv.load_dotenv", return_value=False)
dotenv_patch.start()
original_llm = sys.modules.get("llm")
fake_llm = ModuleType("llm")
fake_llm.llm = FakeMessagesListChatModel(responses=[AIMessage(content="Offline response")])
sys.modules["llm"] = fake_llm


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    # Windows asyncio uses loopback sockets internally for its event loop.
    def guard(original):
        def blocked(sock, address):
            if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1", "localhost"):
                return original(sock, address)
            raise AssertionError("External network access is prohibited in automated tests")
        return blocked

    monkeypatch.setattr(socket.socket, "connect", guard(socket.socket.connect))
    monkeypatch.setattr(socket.socket, "connect_ex", guard(socket.socket.connect_ex))


def pytest_unconfigure(config):
    dotenv_patch.stop()
    if original_llm is None:
        sys.modules.pop("llm", None)
    else:
        sys.modules["llm"] = original_llm
