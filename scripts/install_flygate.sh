#!/usr/bin/env bash
# flygate CLI 를 설치합니다. 저장소 .venv 를 만들고 의존성을 넣은 뒤, ~/.local/bin/flygate 에 실행 래퍼를 연결합니다.
# 사용: ./scripts/install_flygate.sh [설치 디렉터리, 기본 ~/.local/bin]
# 키는 저장소 루트의 .env(TYPESAFE_API_KEY, NVIDIA_API_KEY)에서 읽습니다. 키가 없으면 판단이 필요한 명령은 '사람 확인'으로 돌립니다.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${1:-$HOME/.local/bin}"

# 파이썬 3.10 이상이 필요합니다(코드가 `str | None` 같은 3.10 문법을 씁니다). 없거나 낮으면 여기서 멈추고 알려 줍니다.
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 를 찾지 못했습니다. Python 3.10 이상을 설치한 뒤 다시 실행하세요." >&2
  exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "Python 3.10 이상이 필요합니다. 지금 버전: $(python3 --version 2>&1)" >&2
  exit 1
fi

if [ ! -x "$ROOT/.venv/bin/python" ]; then
  python3 -m venv "$ROOT/.venv"
fi
"$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt" duckdb keyring "prompt_toolkit>=3.0.48,<4"

mkdir -p "$BIN"
ln -sf "$ROOT/agent/bin/flygate" "$BIN/flygate"
echo "설치했습니다: $BIN/flygate -> $ROOT/agent/bin/flygate"
case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo "PATH 에 $BIN 이 없습니다. 셸 설정에 다음 줄을 더하세요: export PATH=\"$BIN:\$PATH\"" ;;
esac
"$BIN/flygate" --help | head -5
echo "다음: flygate 를 실행하고 /login 으로 NVIDIA 키를 넣으세요(또는 .env.example 을 .env 로 복사해 채웁니다)."
