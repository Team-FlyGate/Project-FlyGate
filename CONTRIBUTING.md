# FlyGate에 기여하기 · Contributing

FlyGate는 Apache-2.0 라이선스의 오픈소스입니다. 버그 제보, 기능 제안, 문서 수정, 코드 기여를 모두 환영합니다.

*English summary: FlyGate is open source under Apache-2.0. Bug reports, feature ideas, docs fixes and code are all welcome. Open an issue first for anything larger than a small fix, keep pull requests focused, and make sure `pytest` and `npm run build` pass. Issues and pull requests in English are fine.*

## 먼저 알아 둘 것

- **FlyGate는 판단을 돕는 도구입니다.** 보고 여부와 인과성의 최종 판정은 사람이 합니다. 이 원칙을 바꾸는 변경(자동 제출, 사람 검토를 건너뛰는 경로 등)은 받지 않습니다.
- **수치는 만들지 않습니다.** 화면과 문서에 적는 수치는 저장소의 평가 결과나 원본 데이터에서 나와야 하고, 출처(파일 · 키)를 함께 적습니다.
- **주장에는 근거 ID가 붙습니다.** 에이전트가 쓰는 문장을 늘리는 변경은 크리틱(근거 ID · 숫자 대조 · 과잉해석 판정)을 함께 통과해야 합니다.
- **키와 환자 정보는 커밋하지 않습니다.** `.env`, 실제 환자를 식별할 수 있는 자료는 올리지 마세요.

## 제보와 제안

- 버그와 기능 제안은 [이슈](https://github.com/Team-FlyGate/Project-FlyGate/issues)로 남겨 주세요. 양식이 준비되어 있습니다.
- 보안 문제는 공개 이슈로 올리지 말고 [SECURITY.md](SECURITY.md)의 방법을 따라 주세요.
- 작은 수정(오타, 깨진 링크, 명백한 버그)은 이슈 없이 바로 PR을 보내도 됩니다. 그보다 큰 변경은 이슈에서 방향을 먼저 맞추면 헛수고를 줄일 수 있습니다.

## 개발 환경

필요한 것은 macOS · Linux · Windows WSL, Python 3.10 이상, Node.js 20 이상입니다.

```bash
git clone https://github.com/Team-FlyGate/Project-FlyGate && cd Project-FlyGate
./scripts/install_flygate.sh                 # .venv 와 flygate CLI
cp .env.example .env                         # NVIDIA_API_KEY(필수) · TYPESAFE_API_KEY(선택)
.venv/bin/pip install pytest uvicorn duckdb pandas pyarrow numpy scipy

.venv/bin/python -m pytest -q                # 테스트(키 없이 돕니다)
.venv/bin/python -m uvicorn api.index:app --port 8000
cd web && npm ci && npm run dev              # http://localhost:5173
```

NVIDIA 모델이 이 키로 응답하는지는 `.venv/bin/python scripts/check_models.py`로 확인합니다.

## 저장소 구조

| 경로 | 내용 |
|---|---|
| `agent/` | `flygate` CLI, OpenShell 정책, OpenClaw 작업 공간 |
| `api/` | 웹이 부르는 API(FastAPI)와 판단 · 숙고 · 크리틱 로직(`api/_fv/`) |
| `web/` | flygate.kr 웹(React + Vite). 문구는 `t('한국어', 'English')` 쌍으로 적습니다 |
| `pipeline/` | FAERS 웨어하우스, 참조 세트, 벤치마크 스크립트 |
| `fly_discovery/` | STEP 1 측정 결과 |
| `skills/` | Agent Skills(SKILL.md)와 평가 |
| `tests/` | pytest |

## Pull Request

1. `main`에서 브랜치를 만듭니다. 이름은 `fix/…`, `feat/…`, `docs/…`처럼 짧게 적습니다.
2. 변경 하나에 PR 하나를 권합니다. 관계없는 정리는 따로 보내 주세요.
3. 보내기 전에 확인합니다.
   - `python -m pytest -q` 통과
   - 웹을 고쳤다면 `cd web && npm run build` 통과
   - 화면 문구를 고쳤다면 한국어와 영어를 함께 고침
   - 화면을 고쳤다면 PR에 스크린샷(폰 너비 포함)
4. 커밋 메시지와 PR 설명에는 무엇을 왜 바꿨는지 적습니다. 확인하지 못한 것이 있으면 그것도 적습니다.

검토는 팀원이 시간 날 때 합니다. 답이 늦어도 양해 부탁드립니다.

## 라이선스

기여한 내용은 저장소와 같은 [Apache-2.0](LICENSE)으로 공개됩니다.
