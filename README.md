# arXiv Paper Summarizer

arXiv URL을 입력받아 PDF를 다운로드하고, 섹션별로 요약하여 Markdown 형태로 출력하는 Python 스크립트입니다.

## 기능

- ✅ arXiv URL에서 PDF 자동 다운로드
- ✅ PDF에서 텍스트 추출
- ✅ 섹션별 텍스트 분리 (Abstract, Introduction, Method, Results, Conclusion)
- ✅ AI 기반 각 섹션 요약
- ✅ 최종 Markdown 요약 생성

## 설치

필요한 패키지를 설치합니다:

```bash
pip install -r requirements.txt
```

## 사용법

```bash
python paper_summarizer.py <arxiv_url>
```

### 예시

```bash
python paper_summarizer.py https://arxiv.org/pdf/1706.03762
```

또는

```bash
python paper_summarizer.py https://arxiv.org/abs/1706.03762
```

## 출력

스크립트는 다음과 같은 파일을 생성합니다:
- `{paper_id}_summary.md`: 섹션별 요약이 포함된 Markdown 파일

## 지원하는 섹션

1. **📝 Abstract**: 논문의 요약
2. **🎯 Introduction**: 연구 배경 및 목적
3. **🔬 Methodology**: 연구 방법론
4. **📊 Results & Discussion**: 결과 및 토론
5. **🎯 Conclusion**: 결론

## 요구사항

- Python 3.7+
- 인터넷 연결 (PDF 다운로드 및 AI 모델 로딩)
- 약 2GB 여유 공간 (AI 모델 캐시)

## 테스트 결과

유명한 "Attention Is All You Need" 논문 (https://arxiv.org/pdf/1706.03762)으로 테스트 완료:
- ✅ PDF 다운로드 성공
- ✅ 15페이지 텍스트 추출 완료
- ✅ 5개 섹션 성공적으로 분리 및 요약
- ✅ Markdown 요약 생성 완료

## 주의사항

- 첫 실행 시 AI 모델 다운로드로 인해 시간이 걸릴 수 있습니다
- PDF 구조가 표준과 다른 경우 일부 섹션이 추출되지 않을 수 있습니다
- 임시 PDF 파일은 처리 완료 후 자동으로 삭제됩니다

## 라이브러리

- `requests`: PDF 다운로드
- `PyPDF2`: PDF 텍스트 추출
- `transformers`: AI 기반 텍스트 요약
- `torch`: 딥러닝 프레임워크
- `nltk`: 자연어 처리
