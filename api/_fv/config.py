"""환경설정. 로컬 .env 의 하이픈 키 이름과 배포 환경의 밑줄 키 이름을 모두 받는다."""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = pathlib.Path(__file__).resolve().parents[1] / "_data"


def _load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_dotenv()


def _first(*names):
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return None


TYPESAFE_API_KEY = _first("TYPESAFE_API_KEY", "TYPESAFE-AI-API-KEY", "TYPESAFE_AI_API_KEY")
NVIDIA_API_KEY = _first("NVIDIA_API_KEY", "NVIDIA-NIM-API-Key", "NVIDIA_NIM_API_KEY")

JEV_URL = "https://api.typesafe.ai/v1/systemone"
JEV_MODEL = "jev-latest"
NIM_URL = "https://integrate.api.nvidia.com/v1"

# System-2 모델 사슬: 앞 모델이 실패하거나(404 · 503 등) 제한 시간 안에 답하지 않으면 다음으로 넘어간다.
# 빠른 Lightning 을 둘째에 둡니다. 예전 순서(Super → Ultra → Lightning)에서는 Ultra 가 응답 없이 남은 시간을 다 써서
# Lightning 을 불러 보지도 못하고 실패했습니다(2026-11-12 운영에서 확인: Super HTTP 404, Ultra ReadTimeout, Lightning 시간 소진).
MODEL_DELIBERATE = ["nvidia/nemotron-3-super-120b-a12b", "nvidia/nemotron-3.5-lightning-30b-a3b",
                    "nvidia/nemotron-3-ultra-550b-a55b"]
# 숙고 메모를 쓸 때 모델 하나가 쓸 수 있는 최대 대기 시간(초). 전체 예산(약 85초) 안에서 대체 모델에 시간이 남게 합니다.
DELIBERATE_PER_MODEL_S = 35.0
MODEL_FAST = ["nvidia/nemotron-3.5-lightning-30b-a3b", "nvidia/nemotron-nano-3-30b-a3b"]
MODEL_EMBED = "nvidia/nemotron-3-embed-1b"
# 문헌 후보 재정렬(교차 인코더)입니다. build.nvidia.com 에서 2026-09-28 에 응답을 확인한 공개 Nemotron 리랭커입니다
# (llama-nemotron-rerank-1b-v2 텍스트 엔드포인트는 2026-08-25 에 종료되었습니다).
MODEL_RERANK = "nvidia/llama-nemotron-rerank-vl-1b-v2"
RERANK_URL = "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-vl-1b-v2/reranking"
MODEL_SAFETY = "nvidia/llama-3.1-nemotron-safety-guard-8b-v3"
# 가드 엔드포인트가 멈추거나 DEGRADED 로 거절할 때 쓰는 대체 모델입니다(응답 형식: "User Safety: unsafe")
MODEL_SAFETY_FALLBACK = "nvidia/nemotron-3.5-content-safety"

# 가격 (USD / 1M tokens). Jev 는 공급사 공개가만 쓴다. NIM 은 확인된 단가가 없어 토큰과 지연만 기록한다
PRICE = {
    "jev": {"in": 0.042, "out": 0.0, "source": "TypeSafe AI / Vercel AI Gateway public list, 2026-09"},
}
