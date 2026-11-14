"""Implement fixed-size and structure-aware chunking."""
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    """Chia text thành các cửa sổ chồng lấp kích thước cố định (ký tự).
    Dùng cho cấu hình A. Bỏ qua trang rỗng text.
    """
    text = page.text
    if not text.strip():
        return []
    if overlap >= size:
        raise ValueError("overlap phải nhỏ hơn size")

    step = size - overlap
    n = len(text)
    chunks: list[Chunk] = []
    start = 0
    idx = 0

    while start < n:
        end = min(start + size, n)
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                Chunk(
                    chunk_id=f"{page.document_id}_p{page.page}_f{idx}",
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=chunk_text,
                    metadata=dict(page.metadata),
                )
            )
            idx += 1
        if end == n:
            break
        start += step

    return chunks


MIN_CHARS = 60

def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Gom các đoạn (ngăn cách bởi dòng trống) thành chunk tối đa max_size ký tự.
    Dùng cho cấu hình B/C. Đoạn dài hơn max_size bị cắt thành các phần
    bằng max_size (không overlap). Nhiều dòng liền nhau trong cùng một
    đoạn được nối lại bằng khoảng trắng. Mảnh ngắn hơn MIN_CHARS được
    gộp vào mảnh kề. Bỏ qua trang rỗng text.
    """
    text = page.text
    if not text.strip():
        return []

    paragraphs: list[str] = []
    for block in text.split("\n\n"):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if lines:
            paragraphs.append(" ".join(lines))

    pieces: list[str] = []
    current = ""

    for para in paragraphs:
        if len(para) > max_size:
            if current:
                pieces.append(current)
                current = ""
            for start in range(0, len(para), max_size):
                pieces.append(para[start : start + max_size])
            continue

        candidate = f"{current} {para}".strip() if current else para
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                pieces.append(current)
            current = para

    if current:
        pieces.append(current)

    # --- Gộp mảnh quá ngắn vào mảnh kề ---
    merged: list[str] = []
    for piece in pieces:
        if merged and len(piece) < MIN_CHARS:
            merged[-1] = f"{merged[-1]} {piece}"
        else:
            merged.append(piece)
    if len(merged) > 1 and len(merged[0]) < MIN_CHARS:
        merged[1] = f"{merged[0]} {merged[1]}"
        merged.pop(0)
    pieces = merged
    # ---------------------------------------------------------------

    return [
        Chunk(
            chunk_id=f"{page.document_id}_p{page.page}_b{idx}",
            document_id=page.document_id,
            source=page.source,
            page=page.page,
            text=piece,
            metadata=dict(page.metadata),
        )
        for idx, piece in enumerate(pieces)
    ]