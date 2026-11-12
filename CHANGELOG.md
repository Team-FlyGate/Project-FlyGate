# 변경 기록 · Changelog

눈에 띄는 변경을 여기에 적습니다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따릅니다.
프로그램 버전은 아직 매기지 않았습니다. 저장소의 `v3.0` ~ `v4.3` 태그는 쇼릴 영상의 버전입니다.

## [Unreleased]

### 추가
- 웹: 대문(`#/`), 제품별 내비게이션(FlyDiscovery · FlyVigilance · 플랫폼), 404 화면
- 웹: 사례 분류의 '보고서 만들기'(ICSR 초기 평가 보고서 서식, 브라우저 인쇄로 PDF 저장)
- 웹: 폰 화면 정리(서랍 메뉴, 다단 배치 접기, 글자 · 누르는 영역 키우기)
- `scripts/check_models.py`: 설정된 NVIDIA 모델이 지금 키로 응답하는지 점검
- `.env.example`, `CONTRIBUTING.md`, `SECURITY.md`, 이슈 · PR 양식

### 바뀜
- 숙고(System-2) 모델 사슬 순서를 Super → Lightning → Ultra 로 바꾸고, 모델 하나가 쓸 수 있는 대기 시간을 35초로 묶었습니다
- STEP 1 단계 화면: 입력을 고르고 실행하는 카드를 맨 위로 올리고 설명을 줄였습니다
- 설치 스크립트가 Python 3.10 미만이면 멈추고 알려 줍니다

### 고침
- 숙고에서 앞 모델이 응답 없이 시간을 다 쓰면 대체 모델을 불러 보지도 못하고 실패하던 문제
