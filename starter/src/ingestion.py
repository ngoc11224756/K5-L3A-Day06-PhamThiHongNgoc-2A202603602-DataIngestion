"""Read and normalize source data."""
import logging
import re
import unicodedata
import fitz  # PyMuPDF
from pathlib import Path

from pypdf import PdfReader

from .models import DocumentPage

logger = logging.getLogger(__name__)

_CHUONG_RE = re.compile(r"^\s*CH\s*ƯƠ\s*NG\s+(\d+)\b", re.IGNORECASE | re.MULTILINE)

def _detect_chuong(normalized_text: str) -> int | None:
    """Tìm số chương từ heading dạng 'CHƯƠNG n' trong văn bản đã chuẩn hóa."""
    match = _CHUONG_RE.search(normalized_text)
    return int(match.group(1)) if match else None


def normalize_text(text: str) -> str:
    """Chuẩn hóa Unicode (NFC) và khoảng trắng, giữ nguyên ngắt dòng/đoạn."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\xa0", " ").replace("\t", " ")

    lines = [re.sub(r" {2,}", " ", line).strip() for line in text.splitlines()]

    normalized_lines: list[str] = []
    blank_run = 0
    for line in lines:
        if line:
            normalized_lines.append(line)
            blank_run = 0
        else:
            blank_run += 1
            if blank_run == 1:
                normalized_lines.append("")

    return "\n".join(normalized_lines).strip()


def load_pdf(
    path: Path,
    document_id: str,
    source: str,
    page_range: tuple[int, int] | None = None,
    page_offset: int = 0,
) -> list[DocumentPage]:
    """Đọc PDF theo từng trang vật lý, chuẩn hóa văn bản và gán số trang in.

    page_range: (start_index, end_index) theo index 0-based của pypdf,
        bao gồm cả hai đầu. None nghĩa là đọc toàn bộ file.
    page_offset: trừ vào index vật lý để ra số trang in
        (vd corpus này: start=7, end=102, offset=6 -> trang in 1-96).
    Trang không trích được text (rỗng sau chuẩn hóa) vẫn được giữ lại,
    đánh dấu metadata["empty_text"] = True và ghi log cảnh báo.
    """
    doc = fitz.open(path)
    start, end = page_range if page_range else (0, len(doc) - 1)

    pages: list[DocumentPage] = []
    current_chuong: int | None = None

    for index in range(start, end + 1):
        raw_text = doc[index].get_text() or ""
        text = normalize_text(raw_text)

        # Bỏ số trang in nằm ở dòng đầu
        lines = text.split("\n")
        if lines and lines[0].strip() == str(index - page_offset):
            text = "\n".join(lines[1:]).lstrip()

        detected = _detect_chuong(text)
        if detected is not None:
            current_chuong = detected

        is_empty = not text
        if is_empty:
            logger.warning(
                "Trang index=%d (page=%d) không trích được text",
                index,
                index - page_offset,
            )

        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=index - page_offset,
                text=text,
                metadata={"chuong": current_chuong, "empty_text": is_empty},
            )
        )

    return pages


