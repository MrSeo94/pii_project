# kpii

한국어 쇼핑몰 상담 대화에서 PII(개인식별정보)를 탐지하고 비식별화하는 Python 패키지입니다.

`kpii`는 정규식 기반 탐지와 선택적인 LLM 기반 탐지를 결합해 대화 메시지에서 개인정보를 찾고, 유형에 따라 마스킹 또는 일반화를 적용합니다.

## 주요 기능

- 한국어 대화 텍스트에서 PII 탐지
- 정규식 기반 정형 PII 탐지
- OpenAI 기반 선택적 LLM 탐지
- 직접식별자 마스킹
- 준식별자 일반화
- 대화 단위 배치 처리와 메시지 스트리밍 처리 지원

## 탐지 및 처리 대상

직접식별자:

- 주민등록번호
- 전화번호
- 이메일
- 신용카드번호
- 계좌번호
- 여권번호
- 운전면허번호
- 이름

준식별자:

- 나이
- 주소
- 날짜

처리 방식:

- 직접식별자: `[전화번호]`, `[이메일]` 같은 유형 토큰으로 마스킹
- 준식별자: 나이, 주소, 날짜를 더 넓은 범주로 일반화

## 설치

기본 설치:

```bash
pip install -e .
```

LLM 탐지까지 사용:

```bash
pip install -e ".[llm]"
```

개발 환경:

```bash
pip install -e ".[dev]"
```

요구 사항:

- Python 3.11+

## 빠른 사용 예시

### 배치 처리

```python
from kpii import Conversation, Message, create_pipeline

pipeline = create_pipeline()

conversation = Conversation(
    conversation_id="demo-001",
    messages=[
        Message(role="user", content="전화번호는 010-1234-5678입니다"),
        Message(role="user", content="저는 만 28세이고 서울시 강남구 역삼동에 살아요"),
    ],
)

result = pipeline.process_conversation(conversation)

for message in result.messages:
    print(message.processed_content)

print(result.summary)
```

예상 결과:

```text
전화번호는 [전화번호]입니다
저는 20대이고 서울 강남구에 살아요
{'전화번호': 1, '나이': 1, '주소': 1}
```

### 단일 메시지 처리

```python
from kpii import Message, create_pipeline

pipeline = create_pipeline()
message = Message(role="user", content="이메일은 test@example.com입니다")
result = pipeline.process_message(message)

print(result.processed_content)
print(result.entities)
```

### 스트리밍 처리

```python
import asyncio

from kpii import Message, create_pipeline

pipeline = create_pipeline()


async def message_stream():
    yield Message(role="user", content="전화번호 010-1234-5678")
    yield Message(role="user", content="2024년 3월 15일에 주문했어요")


async def main():
    async for processed in pipeline.process_stream(message_stream()):
        print(processed.processed_content)


asyncio.run(main())
```

## LLM 탐지 사용

LLM 탐지는 기본적으로 비활성화되어 있습니다. OpenAI 클라이언트를 사용하려면 optional dependency와 API 키가 필요합니다.

```python
from kpii import create_pipeline

pipeline = create_pipeline(
    enable_llm=True,
    llm_api_key="your-api-key",
    llm_model="gpt-4o-mini",
)
```

환경변수 기반으로 키를 주입하는 방식도 사용할 수 있습니다.

LLM은 정규식으로 탐지하기 어려운 이름, 비정형 주소, 문맥 기반 PII 보완에 적합합니다.

## 아키텍처

처리 흐름:

1. `RegexDetector`가 정형 PII를 탐지합니다.
2. 필요 시 `LLMDetector`가 비정형 PII를 추가 탐지합니다.
3. 중복 span은 score 우선으로 정리합니다.
4. `Masker`가 직접식별자를 마스킹합니다.
5. `Generalizer`가 준식별자를 일반화합니다.

핵심 진입점:

- `create_pipeline(...)`
- `PIIPipeline.process_message(...)`
- `PIIPipeline.process_conversation(...)`
- `PIIPipeline.process_stream(...)`

## 테스트

```bash
pytest
```

## 프로젝트 구조

```text
src/kpii/
  config.py
  models.py
  pipeline.py
  detectors/
  processors/
  patterns/
  llm/
  utils/
tests/
docs/
```

## 문서

상세 방법론과 설계 배경은 [docs/pii_methodology.md](docs/pii_methodology.md)에서 확인할 수 있습니다.
