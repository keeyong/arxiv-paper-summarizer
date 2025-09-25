#!/usr/bin/env python3
"""
arXiv Paper Summarizer
======================
arXiv URL을 입력받아 PDF를 다운로드하고, 섹션별로 요약하여 Markdown 형태로 출력하는 스크립트
"""

import re
import os
import sys
import requests
from urllib.parse import urlparse
from PyPDF2 import PdfReader
from transformers import pipeline
import nltk
from typing import Dict, List, Optional

# NLTK 데이터 다운로드
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class ArxivPaperSummarizer:
    def __init__(self):
        """초기화 - 요약 모델 로드"""
        print("요약 모델을 로딩중입니다...")
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1  # CPU 사용
        )
        print("모델 로딩 완료!")
    
    def download_pdf(self, arxiv_url: str) -> str:
        """arXiv URL에서 PDF 다운로드"""
        print(f"PDF 다운로드 중: {arxiv_url}")
        
        # URL 검증 및 PDF URL 변환
        if "arxiv.org/abs/" in arxiv_url:
            arxiv_url = arxiv_url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
        
        if not arxiv_url.endswith(".pdf"):
            arxiv_url += ".pdf"
        
        # PDF 파일명 생성
        paper_id = arxiv_url.split("/")[-1].replace(".pdf", "")
        pdf_filename = f"{paper_id}.pdf"
        
        # PDF 다운로드
        try:
            response = requests.get(arxiv_url, timeout=30)
            response.raise_for_status()
            
            with open(pdf_filename, 'wb') as f:
                f.write(response.content)
            
            print(f"PDF 다운로드 완료: {pdf_filename}")
            return pdf_filename
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"PDF 다운로드 실패: {e}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출"""
        print("PDF에서 텍스트 추출 중...")
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += page_text + "\n"
                    except Exception as e:
                        print(f"페이지 {page_num + 1} 추출 실패: {e}")
                        continue
                
                print(f"총 {len(pdf_reader.pages)}페이지에서 텍스트 추출 완료")
                return text
                
        except Exception as e:
            raise Exception(f"PDF 텍스트 추출 실패: {e}")
    
    def parse_sections(self, text: str) -> Dict[str, str]:
        """텍스트를 섹션별로 분리"""
        print("섹션별 텍스트 분리 중...")
        
        sections = {
            'abstract': '',
            'introduction': '',
            'method': '',
            'results': '',
            'conclusion': ''
        }
        
        # 텍스트 전처리 - 줄바꿈 정리
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Abstract 추출
        abstract_patterns = [
            r'Abstract\s*(.+?)(?=1\s+Introduction|Introduction|1\.|\n\n)',
            r'ABSTRACT\s*(.+?)(?=1\s+INTRODUCTION|INTRODUCTION|1\.|\n\n)',
            r'Abstract[\s\n]*(.+?)(?=Keywords|Introduction|1\s)',
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections['abstract'] = match.group(1).strip()
                break
        
        # Introduction 추출
        intro_patterns = [
            r'(?:1\s+)?Introduction\s*(.+?)(?=2\s+|Method|Related Work|Background)',
            r'(?:1\s+)?INTRODUCTION\s*(.+?)(?=2\s+|METHOD|RELATED WORK|BACKGROUND)',
        ]
        
        for pattern in intro_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections['introduction'] = match.group(1).strip()[:2000]  # 길이 제한
                break
        
        # Method 추출
        method_patterns = [
            r'(?:\d+\s+)?(?:Method|Methodology|Approach|Model)\s*(.+?)(?=\d+\s+|Result|Experiment|Evaluation|Discussion)',
            r'(?:\d+\s+)?(?:METHOD|METHODOLOGY|APPROACH|MODEL)\s*(.+?)(?=\d+\s+|RESULT|EXPERIMENT|EVALUATION|DISCUSSION)',
        ]
        
        for pattern in method_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections['method'] = match.group(1).strip()[:2000]  # 길이 제한
                break
        
        # Results/Discussion 추출
        results_patterns = [
            r'(?:\d+\s+)?(?:Result|Experiment|Evaluation|Discussion)\s*(.+?)(?=\d+\s+|Conclusion|Reference|Acknowledge)',
            r'(?:\d+\s+)?(?:RESULT|EXPERIMENT|EVALUATION|DISCUSSION)\s*(.+?)(?=\d+\s+|CONCLUSION|REFERENCE|ACKNOWLEDGE)',
        ]
        
        for pattern in results_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections['results'] = match.group(1).strip()[:2000]  # 길이 제한
                break
        
        # Conclusion 추출
        conclusion_patterns = [
            r'(?:\d+\s+)?Conclusion\s*(.+?)(?=Reference|Acknowledge|Appendix|\Z)',
            r'(?:\d+\s+)?CONCLUSION\s*(.+?)(?=REFERENCE|ACKNOWLEDGE|APPENDIX|\Z)',
        ]
        
        for pattern in conclusion_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections['conclusion'] = match.group(1).strip()[:1500]  # 길이 제한
                break
        
        # 추출된 섹션 정보 출력
        for section, content in sections.items():
            if content:
                print(f"{section.capitalize()}: {len(content)} 글자 추출됨")
            else:
                print(f"{section.capitalize()}: 추출되지 않음")
        
        return sections
    
    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 50) -> str:
        """텍스트 요약"""
        if not text or len(text) < 100:
            return text
        
        try:
            # 텍스트를 청크로 나누기 (모델 입력 길이 제한)
            max_chunk_length = 1000
            chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
            
            summaries = []
            for chunk in chunks:
                if len(chunk.strip()) < 50:  # 너무 짧은 청크는 건너뛰기
                    continue
                    
                summary = self.summarizer(
                    chunk,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False
                )
                summaries.append(summary[0]['summary_text'])
            
            return " ".join(summaries)
            
        except Exception as e:
            print(f"요약 중 오류 발생: {e}")
            # 요약 실패시 원본 텍스트의 앞부분 반환
            sentences = nltk.sent_tokenize(text)
            return " ".join(sentences[:3]) if sentences else text[:500]
    
    def generate_markdown_summary(self, sections: Dict[str, str], arxiv_url: str) -> str:
        """섹션별 요약을 바탕으로 Markdown 요약 생성"""
        print("Markdown 요약 생성 중...")
        
        # 논문 제목 추출 (간단한 방식)
        title = "arXiv Paper Summary"
        
        markdown = f"""# {title}

**Source**: {arxiv_url}

---

"""
        
        # Abstract 요약
        if sections['abstract']:
            print("Abstract 요약 중...")
            abstract_summary = self.summarize_text(sections['abstract'], max_length=200, min_length=80)
            markdown += f"""## 📝 Abstract

{abstract_summary}

"""
        
        # Introduction 요약
        if sections['introduction']:
            print("Introduction 요약 중...")
            intro_summary = self.summarize_text(sections['introduction'], max_length=180, min_length=70)
            markdown += f"""## 🎯 Introduction

{intro_summary}

"""
        
        # Method 요약
        if sections['method']:
            print("Method 요약 중...")
            method_summary = self.summarize_text(sections['method'], max_length=200, min_length=80)
            markdown += f"""## 🔬 Methodology

{method_summary}

"""
        
        # Results 요약
        if sections['results']:
            print("Results 요약 중...")
            results_summary = self.summarize_text(sections['results'], max_length=180, min_length=70)
            markdown += f"""## 📊 Results & Discussion

{results_summary}

"""
        
        # Conclusion 요약
        if sections['conclusion']:
            print("Conclusion 요약 중...")
            conclusion_summary = self.summarize_text(sections['conclusion'], max_length=150, min_length=60)
            markdown += f"""## 🎯 Conclusion

{conclusion_summary}

"""
        
        markdown += f"""---

*Generated by arXiv Paper Summarizer*
"""
        
        return markdown
    
    def process_paper(self, arxiv_url: str) -> str:
        """전체 프로세스 실행"""
        try:
            # 1. PDF 다운로드
            pdf_path = self.download_pdf(arxiv_url)
            
            # 2. 텍스트 추출
            text = self.extract_text_from_pdf(pdf_path)
            
            # 3. 섹션별 분리
            sections = self.parse_sections(text)
            
            # 4. Markdown 요약 생성
            markdown_summary = self.generate_markdown_summary(sections, arxiv_url)
            
            # 5. 결과 저장
            output_filename = f"{os.path.splitext(pdf_path)[0]}_summary.md"
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(markdown_summary)
            
            print(f"\n✅ 요약 완료! 결과 파일: {output_filename}")
            
            # 임시 PDF 파일 삭제
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                print(f"임시 PDF 파일 삭제: {pdf_path}")
            
            return markdown_summary
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            return ""


def main():
    """메인 함수"""
    if len(sys.argv) != 2:
        print("사용법: python paper_summarizer.py <arxiv_url>")
        print("예시: python paper_summarizer.py https://arxiv.org/pdf/1706.03762")
        sys.exit(1)
    
    arxiv_url = sys.argv[1]
    
    print("🚀 arXiv Paper Summarizer 시작")
    print(f"처리할 논문: {arxiv_url}")
    print("=" * 50)
    
    summarizer = ArxivPaperSummarizer()
    result = summarizer.process_paper(arxiv_url)
    
    if result:
        print("\n" + "=" * 50)
        print("📄 요약 결과:")
        print("=" * 50)
        print(result)
    else:
        print("요약 생성에 실패했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
