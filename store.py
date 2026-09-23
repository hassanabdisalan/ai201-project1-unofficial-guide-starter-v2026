"""
Stages 3 and 4 of the pipeline: embedding chunks and retrieving them.

Three things in here are worth knowing about, because they'd quietly break the
rest of the project if they were wrong:

1. The Chroma collection is created with cosine distance, explicitly. Chroma
   defaults to squared L2, and the 0.6 threshold the course uses is calibrated
   against cosine. Getting this wrong makes every distance number meaningless.

2. `search` returns the distance alongside each chunk. Milestone 4 has you
   compare distances, so they have to be visible.

3. The embedding model is the one Chroma bundles, not one loaded through
   `sentence-transformers`. It is the same model — `all-MiniLM-L6-v2`, 384
   dimensions — but it arrives as an ONNX build from Chroma's own CDN, so the
   install needs neither PyTorch nor a reachable Hugging Face. See `_embedder`.
"""

import os
import re
import shutil
from dataclasses import dataclass

# Must be set BEFORE chromadb is imported. Without it, some Chroma versions
# print "Failed to send telemetry event ..." on every single call — which looks
# exactly like a real error, isn't one, and cost a previous cohort a lot of
# confused help-channel messages.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb  # noqa: E402
from rank_bm25 import BM25Okapi  # noqa: E402

import config
from chunker import Chunk


@dataclass
class Result:
    """One retrieved chunk and how far it was from the question."""

    text: str
    source: str
    label: str
    distance: float   # LOWER IS BETTER. 0.3 is close, 0.9 is unrelated.
    produced_by: str
    category: str


def _category(source: str) -> str:
    """The filename prefix before the first underscore, e.g. 'housing' from
    'housing_aldridge_hall.txt'. Metadata filtering (stretch) narrows search
    to one of these via `search(..., category=...)`."""
    stem = source.rsplit(".", 1)[0]
    return stem.split("_", 1)[0]


_model = None

# The model Chroma bundles. Anything else in config.EMBEDDING_MODEL means
# "fetch that one from Hugging Face instead" — see `_embedder`.
BUNDLED_MODEL = "all-MiniLM-L6-v2"


class _OnnxEmbedder:
    """
    Chroma's built-in embedder, wrapped to look like the other two.

    Chroma's embedding functions are called directly and hand back numpy
    arrays. The rest of this file wants `.encode(texts)`, so the adapter lives
    here rather than making every caller care which embedder it got.
    """

    def __init__(self):
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        self._ef = ONNXMiniLM_L6_V2()

    def encode(self, texts, show_progress_bar: bool = False):
        return [vector.tolist() for vector in self._ef(list(texts))]


def _sentence_transformer(name: str):
    """
    The escape hatch: any model that isn't the bundled one.

    Week 2's "try a second embedding model" stretch option comes through here,
    and so does anything you set `EMBEDDING_MODEL` to. This path *does* need
    `sentence-transformers` and a reachable Hugging Face, neither of which the
    default install has — which is the whole point of the default install.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            f"config.EMBEDDING_MODEL is set to {name!r}, which isn't the model "
            f"Chroma bundles ({BUNDLED_MODEL!r}), so it has to be downloaded "
            f"from Hugging Face.\n"
            f"Install the optional dependency first:\n"
            f"    pip install 'sentence-transformers>=3.4,<3.5'\n"
            f"Or set EMBEDDING_MODEL back to {BUNDLED_MODEL!r}."
        ) from exc

    return SentenceTransformer(name)


def _embedder():
    """
    Load the embedding model once and keep it.

    First call is slow — it downloads about 80 MB. That's why setup happens
    before class.
    """
    global _model

    if _model is not None:
        return _model

    # Used only by this repo's own smoke test, which runs where no model can be
    # downloaded at all. Never set this yourself.
    if os.getenv("AI201_FAKE_EMBEDDINGS") == "1":
        from _smoke_embedder import FakeEmbedder

        _model = FakeEmbedder()
    elif config.EMBEDDING_MODEL == BUNDLED_MODEL:
        _model = _OnnxEmbedder()
    else:
        _model = _sentence_transformer(config.EMBEDDING_MODEL)

    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Turn text into vectors. Runs on your machine, costs no API quota."""
    vectors = _embedder().encode(texts, show_progress_bar=False)
    # sentence-transformers and the smoke stand-in return something with a
    # .tolist(); _OnnxEmbedder has already done that conversion itself.
    return vectors.tolist() if hasattr(vectors, "tolist") else vectors


def _client():
    return chromadb.PersistentClient(
        path=str(config.CHROMA_DIR),
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )


def build_index(
    chunks: list[Chunk],
    corpus: str | None = None,
    variant: str = "default",
) -> int:
    """
    Embed every chunk and store it.

    `variant` lets you keep more than one index of the same corpus at the same
    time. In week 2, when you compare two chunking strategies, index the second
    one as variant="v2" and you can query both instead of deleting the first
    and starting over.
    """
    name = config.collection_name(corpus, variant)
    client = _client()

    try:
        client.delete_collection(name)
    except Exception:
        pass

    collection = client.create_collection(
        name=name,
        # ⚠️ Do not remove. Chroma defaults to squared L2, and every distance
        # number in this course assumes cosine.
        metadata={"hnsw:space": "cosine"},
    )

    batch = 256
    for start in range(0, len(chunks), batch):
        window = chunks[start : start + batch]
        collection.add(
            ids=[f"{c.source}#{c.index}" for c in window],
            documents=[c.text for c in window],
            embeddings=embed([c.text for c in window]),
            metadatas=[
                {
                    "source": c.source,
                    "index": c.index,
                    "produced_by": c.produced_by,
                    "category": _category(c.source),
                }
                for c in window
            ],
        )

    return len(chunks)


def _tokenize(text: str) -> list[str]:
    """Lowercase, alphanumeric-only tokens — enough for BM25 to match exact
    words and numbers ("210", "340") that two near-duplicate chunks share
    everything else with."""
    return re.findall(r"[a-z0-9]+", text.lower())


# Standard reciprocal-rank-fusion constant. It's not sensitive: the point of
# RRF is combining two RANKINGS, not two scores on different scales (cosine
# distance and a BM25 score aren't comparable numbers), so the exact constant
# barely moves the result — it only softens how much a #1-vs-#2 gap matters
# relative to a #10-vs-#11 gap.
_RRF_K = 60


def search(
    question: str,
    top_k: int | None = None,
    corpus: str | None = None,
    variant: str = "default",
    category: str | None = None,
) -> list[Result]:
    """
    Retrieve the chunks most relevant to a question — semantic similarity
    blended with BM25 keyword matching (Milestone 4's hybrid-search
    improvement).

    Semantic-only retrieval on this corpus has one known weak spot: sibling
    documents that share almost every word ("CS 210 Data Structures —
    assessment" vs. "CS 340 Databases — assessment") land at nearly the same
    distance, and the wrong one can win on raw cosine distance alone. BM25
    doesn't care about phrasing similarity — it cares whether the exact
    tokens in the question ("210") appear in the chunk — so it pulls the
    right sibling back up. The two signals are combined by reciprocal rank
    fusion: each chunk's semantic rank and its BM25 rank both contribute,
    so a chunk has to be a genuinely poor semantic match AND have no keyword
    overlap to fall out of the results entirely.

    The corpus is small enough (183 chunks) that both signals are computed
    over the *entire* (optionally category-filtered) collection on every
    call, rather than maintaining a separate persistent BM25 index — simpler,
    and nothing to keep in sync after a re-index.

    Returns the fused top-k, nearest-first by semantic distance is no longer
    guaranteed — fused order is. Each `Result.distance` is still the true
    semantic cosine distance for that chunk, unchanged, because the
    relevance gate's 0.6 cutoff is calibrated against that number and has to
    keep meaning the same thing.

    `category` (stretch: metadata filtering) narrows the search to chunks
    from one filename prefix — e.g. "housing" — before either signal is
    computed, using Chroma's `where` clause. Chunks outside that category are
    invisible to this query, not merely ranked lower.
    """
    top_k = top_k or config.TOP_K
    name = config.collection_name(corpus, variant)

    try:
        collection = _client().get_collection(name)
    except Exception as exc:
        raise RuntimeError(
            f"No index called '{name}'. Run `python app.py index` first."
        ) from exc

    where = {"category": category} if category else None
    total = collection.count()
    if total == 0:
        return []

    # Pull the whole (filtered) collection, not just top-k by distance — BM25
    # needs to see every candidate to have a fair shot at surfacing one that
    # semantic search ranked outside the naive top-k.
    raw = collection.query(
        query_embeddings=embed([question]),
        n_results=total,
        where=where,
    )

    docs = raw["documents"][0]
    metas = raw["metadatas"][0]
    distances = raw["distances"][0]
    if not docs:
        return []

    bm25 = BM25Okapi([_tokenize(d) for d in docs])
    bm25_scores = bm25.get_scores(_tokenize(question))

    # Chroma already returns `docs` sorted nearest-first, so its index order
    # doubles as the semantic ranking.
    semantic_rank = {i: i for i in range(len(docs))}
    bm25_rank = {
        i: rank
        for rank, i in enumerate(sorted(range(len(docs)), key=lambda i: -bm25_scores[i]))
    }

    fused = sorted(
        range(len(docs)),
        key=lambda i: -(1 / (_RRF_K + semantic_rank[i]) + 1 / (_RRF_K + bm25_rank[i])),
    )

    results: list[Result] = []
    for i in fused[:top_k]:
        meta = metas[i]
        results.append(
            Result(
                text=docs[i],
                source=str(meta.get("source", "unknown")),
                label=f"{meta.get('source', 'unknown')}#{meta.get('index', 0)}",
                distance=float(distances[i]),
                produced_by=str(meta.get("produced_by", "unknown")),
                category=str(meta.get("category", "unknown")),
            )
        )
    return results


def semantic_best_distance(
    question: str,
    corpus: str | None = None,
    variant: str = "default",
    category: str | None = None,
) -> float:
    """
    The true nearest neighbour, semantic-only — no BM25 involved.

    Stretch: a second measured improvement. The relevance gate answers a
    different question than retrieval does ("is this in-corpus at all," not
    "which chunks best answer it") and its 0.6 threshold was calibrated
    against pure cosine distance in Week 1. `search`'s hybrid fusion can
    leave the single closest chunk out of the top-k entirely if it has no
    keyword overlap with the question, which quietly changes what the
    gate's reported distance means. This function exists so the gate can
    keep checking the one number it was actually calibrated against,
    independent of whatever `search` does to rank chunks for generation.
    """
    name = config.collection_name(corpus, variant)
    try:
        collection = _client().get_collection(name)
    except Exception as exc:
        raise RuntimeError(
            f"No index called '{name}'. Run `python app.py index` first."
        ) from exc

    if collection.count() == 0:
        return 1.0

    where = {"category": category} if category else None
    raw = collection.query(
        query_embeddings=embed([question]),
        n_results=1,
        where=where,
    )
    distances = raw["distances"][0]
    return float(distances[0]) if distances else 1.0


def index_exists(corpus: str | None = None, variant: str = "default") -> bool:
    """Is there an index here to search, without searching it?

    `serve.py`'s health check asks this. It deliberately does not embed
    anything: loading the embedding model takes 80 MB and a few seconds, and a
    health check that heavy is a health check nobody can afford to call.
    """
    try:
        collection = _client().get_collection(config.collection_name(corpus, variant))
        return collection.count() > 0
    except Exception:
        return False


def reset():
    """Delete every index. Occasionally the fastest way out of a mess."""
    if config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)
