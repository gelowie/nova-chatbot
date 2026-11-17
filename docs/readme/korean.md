<div align="center">

![Nova banner](../img/banner.png)

<a href="../../CHANGELOG.md"><img src="../img/badges/version.svg" alt="version: 1.0"></a> <a href="../../LICENSE"><img src="../img/badges/license.svg" alt="license: MIT"></a> <a href="../../help/installing-nova.md"><img src="../img/badges/runtime.svg" alt="runtime: Python 3.10+"></a> <a href="../nova.md"><img src="../img/badges/dependencies.svg" alt="dependencies: none"></a>

</div>

# Nova — Local JSON-Powered Chatbot

> 이 문서는 영어 [README](../../README.md)의 번역본입니다. 기준 문서는 영어판이며, 번역은 최신 내용보다 늦을 수 있습니다. 차이를 발견하면 이슈로 알려 주세요.

오타에 강한 친근한 챗봇으로, **전부 내 컴퓨터에서 실행됩니다**.
클라우드 API, API 키, 서드파티 서비스, `pip install` 모두 필요 없습니다.

<div align="center">

[English](../../README.md) | [中文](chinese.md) | [日本語](japanese.md) | [한국어](korean.md) | [Español](spanish.md)

</div>

## 목차

- [Nova란?](#nova란)
- [기능](#기능)
- [제한 사항](#제한-사항)
- [빠른 시작](#빠른-시작)
- [Nova와 대화하기](#nova와-대화하기)
- [작동 방식](#작동-방식)
- [저장소 구조](#저장소-구조)
- [Java 구현](#java-구현)
- [테스트](#테스트)
- [Nova 확장하기](#nova-확장하기)
- [문서](#문서)
- [기여하기](#기여하기)
- [라이선스](#라이선스)

## Nova란?

Nova는 친근하고 쓸모 있는 어시스턴트를 만드는 데 클라우드 서비스가 필요 없다는 것을 보여 주는 셀프 호스팅 챗봇입니다. 동작에 필요한 모든 것이 이 저장소에 있습니다.

- **성격**(답변, 농담, 조언)은 평범한 JSON입니다: [`src/json/brain.json`](../../src/json/brain.json)
- **로직**(라우팅, 계산, 날짜)은 짧은 Python입니다: [`src/py/`](../../src/py/)
- **인터페이스**는 HTML 파일 하나입니다: [`src/index.html`](../../src/index.html)
- 표준 라이브러리만 쓰는 작은 **서버**가 이들을 연결합니다: [`server.py`](../../server.py)

Nova는 학습용 프로젝트이자 나만의 로컬 어시스턴트를 위한 템플릿이며, 사적인 대화 상대입니다. 메시지는 컴퓨터 밖으로 나가지 않습니다. 할 수 있는 범위는 [제한 사항](#제한-사항)을 참고하세요.

## 기능

- **오프라인, 의존성 없음.** Python 표준 라이브러리만 사용합니다.
- **정확한 계산.** “whats 5 plus 3 times 2”, “144 divided by 12”, “15% of 200”, “2^10”, “3 squared plus 4 squared”. 제한된 구문 트리 탐색기로 계산하며 `eval()`은 절대 사용하지 않습니다.
- **시간과 날짜.** 현재 시각, 오늘 날짜와 요일, 내일/어제, 다음 달/지난달, “in 3 weeks” 같은 오프셋(컴퓨터 시계 기준).
- **JSON 두뇌**: 62개의 대화 주제(인사, 잡담, 감정, 조언, 추천, 농담 10개, 상식 7개, 명언 5개, 수수께끼 4개).
- **오타와 줄임말에 강함.** 오타 수정 127개와 구문 수정 61개, 그리고 퍼지 매칭 덕분에 “helo”, “hru”, “wat r u doin”, “helloooo thereeee”도 통합니다.
- **세련된 채팅 화면.** 입력 중 표시, 빠른 답장 버튼, 타임스탬프, 대화 지우기 버튼, 반응형 레이아웃.
- **로컬이며 비공개.** 서버는 `127.0.0.1`에서만 수신합니다.

## 제한 사항

- 규칙 기반: 언어 모델을 사용하지 않습니다. Nova는 패턴을 맞추고 작은 프로그램을 실행할 뿐입니다.
- 기억 없음: 모든 메시지를 각각 독립적으로 처리합니다.
- 인터넷에 접속하지 않으므로 날씨, 뉴스, 주가 같은 실시간 데이터가 없고 파일이나 이미지도 읽을 수 없습니다.
- 매칭은 영어만 지원합니다(다른 문자와 악센트 문자는 두뇌가 무시합니다).
- 콘텐츠가 적으며 범위를 벗어나면 대체 응답을 합니다.
- 한 명의 사용자, 한 대의 컴퓨터용입니다.
- [Java 구현](#java-구현)은 계산과 시간 스킬만 포함합니다.

## 빠른 시작

**요구 사항:** Python 3.10 이상(3.12로 개발 및 테스트)과 웹 브라우저. JDK는 선택 사항인 Java 데모에만 필요합니다.

```bash
git clone https://github.com/gelowie/nova-chatbot.git
cd nova-chatbot
python server.py        # macOS/Linux에서는 다음과 같이 해야 할 수 있습니다: python3 server.py
```

브라우저에서 <http://127.0.0.1:8000>을 엽니다. 서버는 `Ctrl+C`로 종료합니다.

실행 중인지 확인:

```bash
curl http://127.0.0.1:8000/health
# {"ok":true}
```

자세한 내용과 문제 해결: [Nova 설치](../../help/installing-nova.md).

## Nova와 대화하기

| 입력 | Nova가 사용하는 것 | 응답 예시 |
|---|---|---|
| `whats 5 plus 3 times 2` | 계산 스킬 | Solved **5 + 3 × 2** = **11** |
| `15% of 200` | 계산 스킬 | Solved **(15 ÷ 100) × 200** = **30** |
| `100 / 0` | 계산 스킬 | I can't divide by zero — that one breaks the universe. |
| `what time is it` | 시간 스킬 | It's **15:03** on your system clock. |
| `what is the date in 3 weeks` | 시간 스킬 | That lands on **Friday, 06 November 2026** (2026-11-06). |
| `helo` / `hru` / `sup` | JSON 두뇌 | 인사 또는 “잘 지내?”에 대한 답변. |
| `tell me a joke` | JSON 두뇌 | 저장된 농담 중 하나. |
| `i feel great today` | JSON 두뇌 | 날짜가 아니라 대화형 답변. |
| `asdfghjkl` | 대체 응답 | “이해하지 못했어요”라는 친절한 안내와 추천 문구. |

전체 질문 가이드와 HTTP API: [Nova 사용법](../../help/how-to-use-nova.md).

```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "whats 5 plus 3 times 2"}'
# {"text": "Solved **5 + 3 × 2** = **11**", "skill": "math", "suggestions": [...]}
```

## 작동 방식

```
Browser (src/index.html) ── POST /chat ──► server.py ──► NovaEngine.respond()   (src/py/engine.py)
                                                              │
                                      1. math_solver.solve       → "math"
                                      2. time_reader.handle      → "time"
                                      3. JSON brain (fuzzy match) → "brain"
                                      4. fallback                → "fallback"
```

1. 답을 처음 만든 계층이 채택됩니다.
2. 스킬이 먼저 실행되므로 정확히 답할 수 있는 질문은 퍼지 매칭이 아니라 계산됩니다.
3. 두뇌는 메시지를 정규화(소문자 변환, 줄임말·오타 수정)한 뒤 모든 패턴과의 단어 겹침으로 점수를 매기고(패턴이 그대로 들어 있으면 가산점) 최고 점수가 0.35 이상일 때 답합니다.
4. 모든 응답은 `{"text", "skill", "suggestions"}` 형식입니다.

더 자세한 설명: [아키텍처](../nova.md)와 [JSON 두뇌](../../help/the-json-brain.md).

## 저장소 구조

```
nova-chatbot/
├── server.py                  # HTTP 서버 및 실행 진입점
├── src/
│   ├── index.html             # 브라우저 채팅 화면
│   ├── json/brain.json        # 응답, 패턴, 오타·줄임말 수정
│   ├── py/                    # Python 엔진(지원되는 구현)
│   │   ├── engine.py          #   라우팅, 정규화, 매칭
│   │   ├── math_solver.py     #   계산 스킬
│   │   └── time_reader.py     #   날짜/시간 스킬
│   └── java/                  # Java 계산·시간 스킬과 CLI 데모
├── tests/test_nova.py         # 자동 테스트
├── docs/                      # 문서, 번역, 이미지
│   ├── _docs.md               #   문서 색인
│   ├── nova.md                #   아키텍처와 구성 요소
│   ├── compatible/            #   플랫폼별 호환성 안내
│   ├── readme/                #   README 번역본
│   └── img/                   #   배너, 아이콘, 배지
├── help/                      #   가이드(설치, 사용, 두뇌, 스킬)
├── .github/                   # 이슈 양식, PR 템플릿, CI, Dependabot
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Java 구현

[`src/java/`](../../src/java/)에는 **계산 및 시간 스킬**의 Java 버전과 명령줄 데모가 있습니다. 부분 포팅이며 HTTP 서버가 없고 `brain.json`도 읽지 않으므로 대화를 할 수 없고 Python 엔진과 바꿔 쓸 수도 없습니다. 같은 입력에 대해 두 스킬은 같은 결과를 내지만, Java는 `double`로 계산하므로 2^53보다 큰 정수 결과는 다릅니다.

```bash
javac -encoding UTF-8 -d out src/java/*.java
java -cp out nova.NovaEngine
```

JDK 17 이상을 권장합니다(OpenJDK 21에서 컴파일 및 실행 확인). 특수 문자가 `?`로 보이면 `-Dstdout.encoding=UTF-8`(Java 19+)로 실행하거나 터미널을 UTF-8로 바꾸세요.

## 테스트

```bash
python -m unittest discover -s tests -v
```

테스트는 `brain.json`의 유효성, 계산과 시간 답변, 일반 대화가 시간 질문으로 오인되지 않는지, 인텐트 라우팅, 오타 처리, 대체 응답, HTTP 서버(상태 확인, 페이지, 아이콘, 채팅, 잘못된 요청)를 확인합니다. 실행 중인 서버나 추가 패키지는 필요 없습니다. GitHub Actions도 같은 테스트를 실행하고 Java 파일을 컴파일합니다([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)).

## Nova 확장하기

- **새 답변, 인텐트, 오타 수정:** [`brain.json`](../../src/json/brain.json)을 편집하세요. [JSON 두뇌 가이드](../../help/the-json-brain.md)를 참고하세요.
- **정확한 답을 주는 새 스킬:** [나만의 스킬 만들기](../../help/_create-skill/create-your-own-skill.md)를 따라 하세요(검증된 튜토리얼).

## 문서

모든 문서의 색인은 [`docs/_docs.md`](../_docs.md)에 있습니다: [Nova란](../../help/what-is-nova.md) · [존재 이유](../../help/why-nova.md) · [Nova는 쓸 만한가](../../help/is-nova-good.md) · [설치](../../help/installing-nova.md) · [사용법](../../help/how-to-use-nova.md) · [이미지](../img/_img.md)

## 기여하기

기여를 환영합니다. [기여 가이드](../../.github/CONTRIBUTING.md)를 읽고 [버그 리포트나 기능 요청](https://github.com/gelowie/nova-chatbot/issues/new/choose)을 등록하거나 풀 리퀘스트를 보내 주세요. [변경 내역](../../CHANGELOG.md)도 참고하세요.

## 라이선스

Nova는 [MIT 라이선스](../../LICENSE)로 배포됩니다. Copyright (c) 2026 Angelo MT.
