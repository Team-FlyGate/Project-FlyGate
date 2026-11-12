#!/usr/bin/env python3
"""설정에 적힌 NVIDIA 모델이 지금 이 키로 실제로 응답하는지 하나씩 불러 봅니다.

/api/health 는 키가 설정돼 있는지만 알려 줍니다. 모델이 내려갔거나(404) 키에 권한이 없거나 응답이 느린지는
직접 불러 봐야 알 수 있습니다. 모델마다 토큰 하나짜리 요청을 한 번 보내고 상태와 걸린 시간을 표로 보여 줍니다.

사용: .venv/bin/python scripts/check_models.py [--timeout 30]
키는 저장소 루트의 .env(NVIDIA_API_KEY)에서 읽습니다. 모델 하나라도 실패하면 종료 코드 1 로 끝납니다.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time

import httpx

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from api._fv import config  # noqa: E402


def chat_models() -> list[tuple[str, str]]:
    """(용도, 모델) 목록. 같은 모델이 여러 용도에 쓰이면 한 번만 부릅니다."""
    groups = [("숙고 메모", config.MODEL_DELIBERATE), ("빠른 구조화", config.MODEL_FAST),
              ("안전 가드", [config.MODEL_SAFETY, config.MODEL_SAFETY_FALLBACK])]
    seen: dict[str, str] = {}
    for purpose, models in groups:
        for m in models:
            seen.setdefault(m, purpose)
    return [(p, m) for m, p in seen.items()]


def ping(model: str, timeout: float) -> tuple[str, float]:
    t0 = time.perf_counter()
    try:
        r = httpx.post(f"{config.NIM_URL}/chat/completions",
                       headers={"Authorization": f"Bearer {config.NVIDIA_API_KEY}"},
                       json={"model": model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1,
                             "chat_template_kwargs": {"enable_thinking": False}},
                       timeout=httpx.Timeout(timeout, connect=10.0))
        status = "OK" if r.status_code == 200 else f"HTTP {r.status_code}"
    except httpx.TimeoutException:
        status = f"시간 초과(>{timeout:.0f}초)"
    except httpx.HTTPError as e:
        status = type(e).__name__
    return status, time.perf_counter() - t0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--timeout", type=float, default=30.0, help="모델 하나를 기다리는 최대 시간(초)")
    a = ap.parse_args()
    if not config.NVIDIA_API_KEY:
        print("NVIDIA_API_KEY 가 없습니다. 저장소 루트의 .env 에 적어 주세요(.env.example 참고).")
        return 2
    bad = 0
    print(f"{'용도':<10} {'모델':<46} {'상태':<18} 걸린 시간")
    for purpose, model in chat_models():
        status, sec = ping(model, a.timeout)
        bad += status != "OK"
        print(f"{purpose:<10} {model:<46} {status:<18} {sec:5.1f}초")
    if bad:
        print(f"\n응답하지 않은 모델이 {bad}개 있습니다. 숙고 사슬 순서는 api/_fv/config.py 의 MODEL_DELIBERATE 에서 바꿉니다.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
