# 기동전사 건담 외전 III 심판받는 자 한글 패치 (Mobile Suit Gundam Side Story III - Sabakareshi Mono, 세가 새턴 일본판)

- 대상: Mobile Suit Gundam Side Story III - Sabakareshi Mono (Japan) — 트랙 01에 xdelta 패치 (트랙 02~14 오디오·cue 는 그대로, 트랙 01 크기도 그대로)
- 내려받기: 릴리즈의 `GundamSideStory3_KR_v0.9.zip` — 안의 readme.txt 에 원본·패치 md5 와 적용 방법

| 트랙 | 원본 md5 | 패치 md5 |
|---|---|---|
| Track 01 | `ACB0108F768845B9EE1875A45A0C0620` | `23D897A025341C4FC5D691FE4407A495` |

## 바뀌는 것 (v0.9)
- 음성 자막 174줄 — 원래 자막이 없는 게임이라 새로 넣음(브리핑·미션 전후 컷신·결과 화면, 음성 재생 위치에 맞춰 넘어감)
- 미션 사이 막간 화면 글 4편(그림)
- 동영상 자막: 오프닝, 엔딩 5편
- 결과 화면: 교관 평가·실패 메시지 21장, 항목 이름(전술득점·피탄율·종합전적·평가), 계급(소위·중위·대위·소령)
- STAGE SELECT 화면: 제N화·시나리오 제목·전술득점·피탄율·종합전적·평가
- 시나리오 제목 5장, 타이틀 로고 부제(심판받는자)

## 알려진 점
- 인게임 HUD·포즈·STATUS 등 영문 그림은 그대로
- 자막 원문은 음성을 받아쓴 것이라 일부 대사가 실제와 다를 수 있음

## 저장소
- 1편([gundam-blue-kr-patch](https://github.com/hospi0/gundam-blue-kr-patch))과 같은 엔진 — 1편 도구를 옮기고 주소만 `tools/port.py`(`port_find.py` 로 찾음)
- `tools/build.py` 빌더 · `hook.py` 자막 훅(SH-2, SGL 명령표에 VDP1 스프라이트) · `subs.py` 자막 묶음 · `scgfx.py` 그림 · `apsp.py` 막간 화면 글 · `moviesub.py` 동영상 자막 · `iso.py` 디스크 · `make_dist.py` 배포
- `work/text/voice_ko.tsv` 음성 자막 · `work/text/apsp_ko.tsv` 막간 화면 글 · `work/movie/movie_subs.tsv` 동영상 자막
- `docs/` 조사·작업 기록
