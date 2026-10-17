import os
import re
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from app.config import settings

class PDFProcessor:
    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Hierarchy of natural split boundaries:
        # 1. Paragraphs (\n\n)
        # 2. Lines / List items (\n)
        # 3. Sentences (. , ? , ! )
        # 4. Clauses (; , , )
        # 5. Words (" ")
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]

    def _clean_extracted_text(self, text: str) -> str:
        """
        Cleans extracted text from PDF artifacts:
        - Reconnects hyphenated words broken across line wraps (e.g., 'electro-\nchemical' -> 'electrochemical')
        - Replaces special unicode bullet points or replacement chars with clean standard bullet points
        - Normalizes horizontal spaces while preserving paragraph breaks
        """
        if not text:
            return ""

        # Reconnect hyphenated word breaks
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # Normalize unicode replacement characters like  into standard bullets
        text = text.replace('\ufffd', '• ')

        # Normalize whitespace (preserve double newlines for paragraphs)
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
        cleaned_text = '\n'.join(lines)
        # Collapse 3+ newlines into 2
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        return cleaned_text.strip()

    def extract_text_by_pages(self, file_path: str) -> List[Tuple[int, str]]:
        """
        Extract text from PDF file, returning a list of tuples: (page_number, cleaned_text).
        page_number is 1-indexed.
        """
        pages_content = []
        reader = PdfReader(file_path)
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            cleaned = self._clean_extracted_text(page_text)
            pages_content.append((idx + 1, cleaned))
        return pages_content

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively splits text using the highest-priority separator that exists in the text.
        """
        text = text.strip()
        if len(text) <= self.chunk_size or not separators:
            return [text] if text else []

        sep = separators[0]
        remaining_seps = separators[1:]

        if sep in text:
            splits = text.split(sep)
        else:
            return self._recursive_split(text, remaining_seps)

        final_units = []
        for s in splits:
            s_clean = s.strip()
            if not s_clean:
                continue
            if len(s_clean) > self.chunk_size and remaining_seps:
                sub_splits = self._recursive_split(s_clean, remaining_seps)
                final_units.extend(sub_splits)
            else:
                final_units.append(s_clean)

        return final_units

    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Hierarchical recursive chunker:
        1. Breaks on paragraphs and sentences first.
        2. Merges units up to chunk_size.
        3. Never cuts in the middle of words or sentences.
        4. Overlaps using complete grammatical units.
        """
        if not text:
            return []

        # Get atomic units broken at paragraphs/sentences/words
        units = self._recursive_split(text, self.separators)
        if not units:
            return []

        chunks = []
        current_chunk_units = []
        current_len = 0

        for unit in units:
            unit_len = len(unit) + (2 if current_chunk_units else 0)  # account for delimiter space/newline

            if current_len + unit_len <= self.chunk_size:
                current_chunk_units.append(unit)
                current_len += unit_len
            else:
                if current_chunk_units:
                    chunk_str = " ".join(current_chunk_units).strip()
                    if chunk_str:
                        chunks.append(chunk_str)

                    # Build overlap from full units at the end of the current chunk
                    overlap_units = []
                    overlap_len = 0
                    for u in reversed(current_chunk_units):
                        if overlap_len + len(u) + 1 <= self.chunk_overlap:
                            overlap_units.insert(0, u)
                            overlap_len += len(u) + 1
                        else:
                            break

                    current_chunk_units = overlap_units + [unit]
                    current_len = sum(len(u) for u in current_chunk_units) + len(current_chunk_units) - 1
                else:
                    # Single unit exceeds chunk_size on its own; add it directly
                    chunks.append(unit)
                    current_chunk_units = []
                    current_len = 0

        if current_chunk_units:
            chunk_str = " ".join(current_chunk_units).strip()
            if chunk_str:
                chunks.append(chunk_str)

        return chunks

    def process_pdf(self, file_path: str, document_id: int, document_title: str) -> List[Dict[str, Any]]:
        """
        Extracts text from all pages and generates clean chunks with page metadata.
        """
        pages = self.extract_text_by_pages(file_path)
        all_chunks = []
        chunk_global_idx = 0

        for page_num, page_text in pages:
            if not page_text:
                continue

            page_chunks = self._split_into_chunks(page_text)
            for chunk_text in page_chunks:
                chunk_id = f"doc_{document_id}_p{page_num}_c{chunk_global_idx}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "document_id": document_id,
                        "document_title": document_title,
                        "page_number": page_num,
                        "chunk_index": chunk_global_idx
                    }
                })
                chunk_global_idx += 1

        page_count = len(pages)
        del pages
        import gc
        gc.collect()
        return all_chunks, page_count

pdf_processor = PDFProcessor()
