"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in week 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


# Below this length, a first paragraph reads as a heading ("Laundry in
# Aldridge Hall") rather than as content in its own right. Every campus_life
# document happens to have one — checked across all 88 before picking this.
HEADING_MAX_CHARS = 80

# A chunk shorter than this couldn't stand on its own even with the heading
# attached, so it gets folded into its neighbour instead of shipped as a
# fragment. Nothing in campus_life actually triggers this (shortest observed
# chunk is 63 characters) — it's a safety net for a document that doesn't fit
# the pattern the rest of the corpus does.
MIN_CHUNK_CHARS = 40


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split each document on paragraph breaks, one chunk per paragraph, with the
    document's own heading carried into every chunk so each one still says
    what it's about.

    campus_life posts are short (88 documents, 317 characters average, none
    over 800) but most bundle two to four separable facts under one heading —
    "Laundry in Aldridge Hall" covers both machine prices and the best time to
    go, as two different paragraphs. Splitting on paragraph breaks pulls those
    apart into chunks that each answer one question instead of two, without
    cutting any sentence in half — paragraph breaks in this corpus always fall
    between complete thoughts, never inside one.

    A heading-only paragraph is folded into the next one rather than shipped
    as its own chunk, since "Laundry in Aldridge Hall" alone answers nothing.
    """
    chunks: list[Chunk] = []
    for doc in documents:
        chunks.extend(_split_one(doc))
    return chunks


def _split_one(doc: Document) -> list[Chunk]:
    paragraphs = [p.strip() for p in doc.text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    heading, body = paragraphs[0], paragraphs[1:]
    has_heading = len(heading) <= HEADING_MAX_CHARS and body
    if not has_heading:
        # No separable heading (or nothing after it) — treat every paragraph
        # as its own piece of content instead of losing the first one.
        heading, body = None, paragraphs

    pieces = [f"{heading}\n\n{para}" if heading else para for para in body]
    pieces = [piece for text in pieces for piece in _cap_length(text)]

    merged: list[str] = []
    for piece in pieces:
        if merged and len(piece) < MIN_CHUNK_CHARS:
            merged[-1] = f"{merged[-1]} {piece}"
        else:
            merged.append(piece)

    return [
        Chunk(text=text, source=doc.source, index=i, produced_by="chunker.py::split_documents")
        for i, text in enumerate(merged)
    ]


def _cap_length(text: str) -> list[str]:
    """
    Safety net, not the main strategy: if a heading+paragraph pair still runs
    past CHUNK_SIZE, fall back to fixed-size windows rather than ship one
    oversized chunk. Nothing in campus_life is long enough to reach this —
    the longest chunk produced is 397 characters against an 800 default.
    """
    if len(text) <= config.CHUNK_SIZE:
        return [text]
    step = config.CHUNK_SIZE - config.CHUNK_OVERLAP
    return [
        text[i : i + config.CHUNK_SIZE].strip()
        for i in range(0, len(text), step)
        if text[i : i + config.CHUNK_SIZE].strip()
    ]


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
