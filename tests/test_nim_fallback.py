"""NIM 모델 사슬의 대체 동작: 앞 모델이 404 이거나 응답 없이 시간을 넘겨도 뒤 모델까지 차례가 와야 합니다."""
import asyncio
import json
import time

import httpx
import pytest

from api._fv import clients, config


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setattr(config, "NVIDIA_API_KEY", "nvapi-test")


def run(handle, models, **kw):
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as c:
            return await clients.nim_chat([{"role": "user", "content": "x"}], models, client=c, **kw)
    return asyncio.run(go())


def test_404_then_timeout_still_reaches_last_model():
    def handle(req):
        model = json.loads(req.content)["model"]
        if model == "gone":
            return httpx.Response(404, text="not found")
        if model == "slow":
            raise httpx.ReadTimeout("no answer", request=req)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    out = run(handle, ["gone", "slow", "fast"], deadline=time.monotonic() + 85, per_model_s=35)
    assert out["model"] == "fast" and out["content"] == "ok"
    assert out["fallbacks"] == ["gone: HTTP 404", "slow: ReadTimeout"]


def test_per_model_cap_limits_each_request_timeout():
    seen = []

    def handle(req):
        seen.append(req.extensions["timeout"]["read"])
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    run(handle, ["m"], deadline=time.monotonic() + 85, per_model_s=35)
    run(handle, ["m"], deadline=time.monotonic() + 20, per_model_s=35)
    run(handle, ["m"])
    assert seen[0] == 35                 # 남은 시간이 넉넉하면 모델당 상한이 걸립니다
    assert 15 < seen[1] <= 20            # 남은 시간이 더 짧으면 그쪽을 따릅니다
    assert seen[2] == 90                 # 상한을 주지 않으면 예전처럼 90초입니다


def test_deliberation_chain_puts_the_fast_model_before_the_slow_one():
    chain = config.MODEL_DELIBERATE
    assert chain.index("nvidia/nemotron-3.5-lightning-30b-a3b") < chain.index("nvidia/nemotron-3-ultra-550b-a55b")
    # 모델 셋이 각자 상한까지 써도 전체 예산(100초 - 여유 15초) 안에 최소 둘은 온전히 시도할 수 있어야 합니다
    assert config.DELIBERATE_PER_MODEL_S * 2 <= 85
