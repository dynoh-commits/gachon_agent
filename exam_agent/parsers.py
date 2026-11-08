from __future__ import annotations

import io
import re
from collections import OrderedDict

import pandas as pd


ANSWER_MAP = {"①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5}


def _pdf_text(content: bytes) -> str:
    try:
        import fitz

        document = fitz.open(stream=content, filetype="pdf")
        return "\n".join(page.get_text("text") for page in document)
    except ImportError as exc:
        try:
            import pdfplumber

            with pdfplumber.open(io.BytesIO(content)) as document:
                return "\n".join(page.extract_text() or "" for page in document.pages)
        except ImportError:
            raise RuntimeError("PDF 읽기 라이브러리가 없습니다. requirements.txt에 있는 패키지를 설치해 주세요.") from exc
    except Exception as exc:
        raise ValueError(f"PDF에서 텍스트를 읽지 못했습니다: {exc}") from exc


def parse_answer_key(content: bytes) -> dict[int, dict[str, int]]:
    """Extract question number, circled/Arabic choice, and point value from the key PDF."""
    text = _pdf_text(content)
    rows: dict[int, dict[str, int]] = OrderedDict()
    # The uploaded answer sheet is arranged in four repeated columns. Each row
    # yields number, answer, points triples; the parser also accepts ASCII choices.
    triples = re.findall(r"(?<!\d)(\d{1,2})\s*([①②③④⑤1-5])\s*([23])(?=\s|$)", text)
    for number, answer, points in triples:
        qnum = int(number)
        if 1 <= qnum <= 60:
            normalized_answer = ANSWER_MAP[answer] if answer in ANSWER_MAP else int(answer)
            rows[qnum] = {"answer": normalized_answer, "points": int(points)}
    if len(rows) < 10:
        raise ValueError("정답표에서 문항 번호·정답·배점을 충분히 찾지 못했습니다. 텍스트가 선택 가능한 PDF인지 확인해 주세요.")
    return dict(sorted(rows.items()))


def read_responses(content: bytes, filename: str) -> pd.DataFrame:
    stream = io.BytesIO(content)
    try:
        frame = pd.read_csv(stream) if filename.lower().endswith(".csv") else pd.read_excel(stream)
    except Exception as exc:
        raise ValueError(f"응답 파일을 읽지 못했습니다: {exc}") from exc
    if frame.empty or len(frame.columns) < 2:
        raise ValueError("학생 이름과 문항 응답이 포함된 표를 찾지 못했습니다.")
    name_col = next((col for col in frame.columns if str(col).strip() in {"학생명", "이름", "학생", "name", "Name"}), frame.columns[0])
    frame = frame.rename(columns={name_col: "학생명"})
    qcols = {}
    for col in frame.columns:
        match = re.fullmatch(r"\s*Q?0*(\d{1,2})\s*", str(col), flags=re.IGNORECASE)
        if match:
            qcols[int(match.group(1))] = col
    if not qcols:
        raise ValueError("문항 열 이름을 Q01, Q02 또는 1, 2 형식으로 찾지 못했습니다.")
    frame = frame[["학생명", *[qcols[n] for n in sorted(qcols)]]].copy()
    frame = frame.rename(columns={col: n for n, col in qcols.items()})
    frame["학생명"] = frame["학생명"].astype(str).str.strip()
    for col in sorted(qcols):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def parse_exam_questions(content: bytes) -> dict[int, str]:
    try:
        import pdfplumber

        extracted: dict[int, str] = {}
        with pdfplumber.open(io.BytesIO(content)) as document:
            for page in document.pages:
                words = page.extract_words()
                starts = []
                for word in words:
                    match = re.fullmatch(r"(\d{1,2})\.", word["text"].strip())
                    if match and 1 <= int(match.group(1)) <= 60:
                        starts.append((int(match.group(1)), word["top"], word["x0"] < page.width / 2))
                for number, top, left_column in starts:
                    next_top = min((y for _, y, is_left in starts if is_left == left_column and y > top + 2), default=page.height)
                    column_words = [w for w in words if (w["x0"] < page.width / 2) == left_column and top - 1 <= w["top"] < next_top]
                    lines: list[list[dict]] = []
                    for word in sorted(column_words, key=lambda item: (item["top"], item["x0"])):
                        if not lines or abs(lines[-1][0]["top"] - word["top"]) > 3:
                            lines.append([word])
                        else:
                            lines[-1].append(word)
                    stem = " ".join(" ".join(w["text"] for w in line) for line in lines)
                    stem = re.sub(r"\s+", " ", stem).strip()
                    if len(stem) > 30:
                        extracted[number] = stem[:5000]
        if extracted:
            return extracted
    except ImportError:
        pass

    text = _pdf_text(content)
    # Keep each numbered stem, including its answer choices, until the next item.
    matches = list(re.finditer(r"(?<!\d)(\d{1,2})\.\s+(?=[가-힣A-Z“\"‘])", text))
    questions: dict[int, str] = {}
    for index, match in enumerate(matches):
        number = int(match.group(1))
        if not 1 <= number <= 60:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        stem = re.sub(r"\s+", " ", text[match.start():end]).strip()
        if len(stem) > 30:
            questions[number] = stem[:5000]
    return questions
