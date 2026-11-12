# 보안 정책 · Security Policy

## 취약점 제보

보안 문제를 발견하면 **공개 이슈로 올리지 말고** GitHub의 비공개 제보 기능을 써 주세요.

1. 저장소의 [Security 탭](https://github.com/Team-FlyGate/Project-FlyGate/security)으로 갑니다.
2. **Report a vulnerability**를 눌러 내용을 적습니다.

적어 주시면 좋은 것: 영향을 받는 부분(CLI · API · 웹 · 샌드박스 정책), 재현 방법, 예상되는 영향.

제보를 받으면 팀이 확인하고 답을 드립니다. 팀이 작아 답이 며칠 걸릴 수 있습니다. 수정이 공개되기 전까지는 내용을 공개하지 말아 주세요.

*English: Please do not open a public issue for security problems. Use GitHub's private reporting instead: go to the repository's Security tab and choose "Report a vulnerability". Include the affected part (CLI, API, web, sandbox policy), steps to reproduce and the expected impact. We are a small team, so a reply can take a few days. Please keep the details private until a fix is released.*

## 범위

- `flygate` CLI와 `agent/`의 OpenShell 정책(허용 주소 밖으로 나가는 경로, 키 노출 등)
- `api/`의 공개 엔드포인트(인증 없는 호출로 키나 비용을 소모시키는 경로 등)
- `web/`(flygate.kr)

## 지원하는 버전

`main` 브랜치의 최신 상태만 지원합니다.

## 키와 민감 정보

- API 키는 `.env`나 운영체제 보안 저장소(`flygate`의 `/login`)에만 둡니다. 저장소에 커밋하지 마세요.
- 실수로 키를 커밋했다면 저장소에서 지우는 것만으로는 부족합니다. 발급처에서 그 키를 폐기하고 새로 발급받으세요.
- FlyGate는 공개된 FAERS 자료를 씁니다. 실제 환자를 식별할 수 있는 자료를 이슈나 PR에 올리지 마세요.
