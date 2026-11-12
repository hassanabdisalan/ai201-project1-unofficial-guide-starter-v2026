# The Unofficial Guide

Hassan Abdisalan — corpus: `campus_life`

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none, because the grader can't
> read it.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Week 1

## What This Does

This is a retrieval-augmented question answerer over `campus_life`, a corpus
of 88 short student-written posts about life at a university — dining halls,
dorms and their laundry rooms, course workload and exam formats, parking,
printing quotas, financial aid, and the administrative deadlines nobody
explains properly. Ask it something concrete a real student would know
("How often does the campus shuttle run on weekdays?", "Is the CS 210 final
exam curved?") and it retrieves the specific post that answers it and cites
the file it came from. Ask it something the corpus has no opinion on and it
says so instead of guessing.

## Chunking Strategy

**Chunk size:** not a fixed character count — paragraph-based, with a 500-character safety cap
**Overlap:** 80 characters, only used if the safety cap ever triggers (it doesn't, on this corpus)

The starter's fixed 800-character chunker never actually splits `campus_life`:
88 documents in, 88 chunks out, because the longest document is 549
characters. That's not a bug, but it's also not a real chunking decision —
it's the chunker doing nothing.

Reading the documents in Milestone 1, I noticed most posts aren't really one
thought. `housing_aldridge_hall_laundry.txt` covers machine prices in one
paragraph and the best time to do laundry in another; `health_center.txt`
covers walk-in hours in one paragraph and counselling wait times in another.
Checking all 88 documents confirmed the pattern holds corpus-wide: every one
has a short heading line (never over 80 characters) followed by 1 to 4
content paragraphs, and paragraph breaks always fall between complete
thoughts, never mid-sentence.

So `chunker.py::split_documents` splits each document on paragraph breaks —
one chunk per content paragraph — and prepends the document's heading to
every chunk. The heading matters: without it, a chunk like "Counselling is
separate, in the same building" doesn't say which building, or that it's
about the health center at all. With it, each chunk both answers one
specific question and still names its own topic. `CHUNK_SIZE` (500) and
`CHUNK_OVERLAP` (80) are only a safety net for a heading+paragraph pair that
runs unexpectedly long — nothing in this corpus reaches it; the longest
chunk produced is 397 characters.

Re-indexing with this strategy turned 88 documents into 183 chunks
(previously 88), averaging 167 characters (previously 317), shortest 63,
longest 397. One real tradeoff this surfaced: for "Is the CS 210 final exam
curved?", the top-ranked chunk by raw distance is actually
`course_cs_340_exams.txt` (a different course, same phrasing pattern), not
`course_cs_210_exams.txt`. The correct chunk still lands in the top 5
retrieved and still carries its own heading, so the model correctly answers
from and cites the CS 210 documents anyway — but it's a real near-miss this
corpus produces because so many posts share the same sentence shapes across
sibling topics, and it's part of why I wrote criterion 5 in `criteria.md`.

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it — the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** — source: `course_cs_340_exams.txt#1` — produced by: `chunker.py::split_documents`

```
CS 340 Databases — assessment

Start the term project in week three, not week eight; everyone learns this the hard way.
```

**Chunk 3** — source: `course_phys_130_workload.txt#0` — produced by: `chunker.py::split_documents`

```
Workload for PHYS 130 Mechanics

People keep asking so: 7 hours a week, plus 3 on lab weeks. That's real time, not optimistic time.
```

**Chunk 4** — source: `dining_verrill_street_grill_followup.txt#1` — produced by: `chunker.py::split_documents`

```
Re: Verrill Street Grill

Also worth saying: one register, so the queue is a single line no matter how busy. Nobody tells you this at orientation.
```

**Chunk 5** — source: `housing_morrow_house.txt#1` — produced by: `chunker.py::split_documents`

```
Morrow House — what it's actually like

The good: cheapest housing tier by about $900 a year, and the singles are real singles.
```

## Sample Answer

**Question:** What's the best time to do laundry in Aldridge Hall?

**Answer:**

```
The best time to do laundry in Aldridge Hall is Tuesday or Wednesday morning.

Source: housing_aldridge_hall_laundry.txt
```

**My relevance cutoff:** 0.6 (the starter's default — measured, not just kept)

I ran my five test questions from `questions.py` and the five in
`OUT_OF_SCOPE`, and recorded the single best distance for each with
`python app.py retrieve "..." --top-k 1`, against the paragraph-based index
from Milestone 3 (183 chunks). The five in-corpus questions land between
0.123 and 0.441. The five out-of-scope questions land between 0.787 and
0.923. That's a wide, clean gap — 0.346 wide, with nothing near either edge
— so I kept the default 0.6, which sits almost exactly in the middle
(0.614 would be the literal midpoint) rather than hugging either group.
`TOP_K` also stays at the default of 5: on the one question where two
courses' documents ranked close together (CS 210 vs. its CS 340 lookalike,
below), the correct chunk still placed inside the top 3, so 5 gives margin
above that without burying it in loosely related chunks — these chunks
average only 167 characters each, so even 5 of them is compact context.

| Question | In corpus? | Best distance |
|---|---|---|
| How much printing quota does each student get per semester? | yes | 0.308 |
| How often does the campus shuttle run on weekdays? | yes | 0.183 |
| When can I change my meal plan tier? | yes | 0.216 |
| Is the CS 210 final exam curved? | yes | 0.441 |
| What's the best time to do laundry in Aldridge Hall? | yes | 0.123 |
| What is the capital of Mongolia? | no | 0.787 |
| How do I change the oil in a diesel engine? | no | 0.923 |
| Who won the 1994 World Cup? | no | 0.847 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.849 |
| How do I write a for loop in Rust? | no | 0.860 |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

A note on how these were used: in both cases below, I asked Claude Code
(running as an agent inside my editor, with direct access to my repo and
terminal) to do the actual design and implementation, then reviewed what it
produced rather than writing or rewriting the logic myself. That's a
heavier reliance than "ask, catch a mistake, fix it" — I want to say that
plainly rather than write a correction anecdote that didn't happen.

**1. Chunking strategy (Milestone 3).** I asked it to replace the starter's
fixed 800-character chunker with something that actually fit
`campus_life`. Before writing any code, it read a sample of documents,
then checked paragraph-count and heading-length across all 88 files to
confirm every document followed a "short heading, then 1-4 content
paragraphs" pattern with no document over 80 characters in its heading.
Based on that, it wrote `chunker.py::split_documents` to split on paragraph
breaks and prepend each document's heading to every resulting chunk, with
a fixed-size fallback as a safety net for anything unexpectedly long. It
re-indexed, printed the resulting chunk-count and length stats, and
sampled five chunks for me to read. I checked those five against "could
someone answer a question using only this" myself and accepted the design
as presented — I didn't change the splitting logic, the heading threshold,
or the safety-cap numbers.

**2. Relevance cutoff (Milestone 4).** I asked it to determine whether the
shipped `THRESHOLD = 0.6` was actually right for this corpus rather than
just leaving it unexamined. It ran all five of my `questions.py` test
questions and all five `OUT_OF_SCOPE` questions through `app.py retrieve`
against the re-chunked index, recorded the best distance for each, and
reported that the in-corpus group (0.123-0.441) and the out-of-scope group
(0.787-0.923) left a wide, clean gap with 0.6 sitting near its middle. Its
conclusion was to keep 0.6 rather than move it. I accepted that conclusion
without independently re-deriving the numbers — the one place I made an
independent call in this project was unrelated to modeling choices: when a
push to my fork failed over GitHub's email-privacy protection, it offered
three ways to fix it and I picked which one.

**3. Testing, diagnosis, and the improvement (Week 2, Milestones 1-4).** I
asked it to run the full evaluation, build the criterion-level run log from
`run_eval.py`'s raw output, and judge each verdict, since `scorer.py` was
never built. The part worth flagging specifically: for criterion 1, it
didn't stop at "the right document's filename is in the sources list." On
its own initiative, it re-ran `app.py retrieve` directly on the CS 210
question — the one case `criteria.md` predicted might be close — to check
which specific *chunk* (not just which document) actually made the top-5,
since `course_cs_210.txt` splits into three separate chunks and only one
contains the curve fact. That's how the diagnosis ended up naming a real
mechanism (a sibling document winning on phrasing similarity, differing
from the real answer mainly in one exact token) instead of a vaguer
"retrieval is a little off for this one."

When I asked for one improvement connected to that diagnosis, it picked
hybrid search (BM25 + semantic, combined by reciprocal rank fusion) and
was explicit about preserving the gate's calibration — keeping
`Result.distance` as the true semantic distance rather than some fused
score the 0.6 cutoff was never calibrated against. After running the
before/after comparison, it noticed on its own that my five original
criteria didn't move at all (5/5 both times) and, rather than either
overstating that as "no effect" or quietly calling it a wash, went back to
raw chunk rankings to check whether the specific mechanism it targeted had
actually moved — which it had, at rank 1 specifically. That self-check, and
then reporting the two things hybrid search cost (generic-word noise in
ranks 2-5, and a less-pure "best distance" number for the gate) instead of
only reporting the win, is closer to it catching its own potential overclaim
than me catching a mistake it made. I reviewed and accepted all of it rather
than re-deriving the retrieval rankings myself.

## Stretch Feature: Metadata Filtering

**Declared before building (see commit history for the timestamp on this
line vs. the implementation commit).** `campus_life` filenames already carry
a natural category in their prefix — `admin` (16 docs), `advising` (1),
`course` (27), `dining` (14), `health` (1), `housing` (21), `money` (2),
`orientation` (1), `study` (2), `transit` (2), `winter` (1). I'm going to
store that prefix as a `category` metadata field on
every chunk at index time, and let `app.py retrieve` / `app.py ask` take a
`--category NAME` flag that narrows Chroma's search with a `where` clause
before distances are computed.

**Built:** `store.py::build_index` now tags every chunk's metadata with
`category` (the source filename's prefix before its first underscore).
`store.py::search` takes an optional `category` argument and, when given,
passes `where={"category": category}` to `collection.query` — the excluded
chunks are invisible to that query, not merely ranked lower. `--category`
is wired into both `app.py retrieve` and `app.py ask`.

**What changed, same query, with and without the filter:** "What are the
hours?" is genuinely ambiguous in this corpus — dining halls, the shuttle,
and the health center all describe their own "hours" in similar phrasing.

Unfiltered, `python app.py ask "What are the hours?"` retrieves chunks from
four different categories (dining, transit, health, and an unrelated STAT
150 workload chunk that happened to share vocabulary) and the model
answers with a bulleted list spanning all of them:

```
Because the question asks broadly "What are the hours?" for multiple locations, the hours from the provided documents are:

* The Atrium: 8:00am to 6:00pm weekdays (dining_the_atrium.txt).
* Kestrel Commons: 7:00am to 9:00pm weekdays, 9:00am to 8:00pm weekends (dining_kestrel_commons.txt).
* The campus shuttle: Runs from 7am to 11pm on weekdays (transit_shuttle.txt).
* The health centre: Walk-in hours are 8am to 11am (health_center.txt).
```

With `python app.py ask "What are the hours?" --category health`, only the
two `health_center.txt` chunks are visible to retrieval, and the answer
narrows to exactly the thing meant:

```
Based on health_center.txt, walk-in hours at the health centre are from 8am to 11am. Everything after that is by appointment.
```

Same question, same index, same threshold — the filter is the only thing
that changed, and it's the difference between a sprawling four-topic
answer and a one-topic one.

## Stretch Feature: Conversational Memory

**Declared before building.** The interactive loop (`python app.py ask`
with no question argument) already runs multiple turns in one process, so
it's the natural place for this: I'm going to keep the last few
question/answer pairs in that loop, use the previous question plus the new
one together as the retrieval query (so a vague follow-up like "what about
Sundays?" still retrieves the right chunk instead of nothing), and pass the
actual prior Q&A into the model's prompt as conversation history so it can
resolve pronouns and references the new question doesn't spell out.
**Built:** `app.py`'s interactive loop keeps a capped list of the last 3
`{question, answer}` turns. `ask_pipeline` uses `f"{previous question} {new
question}"` as the retrieval query when history exists (see `app.py`), so a
vague follow-up still carries the topic into the embedding. Separately,
`generate.py::build_prompt` puts the real prior Q&A into the prompt as
"Previous conversation (for context only, not a source)" — kept apart from
the retrieved documents so the model resolves references from it without
treating a past answer as a fact to cite.

**Two-turn exchange, second answer depending on the first:**

```
> What's the best time to do laundry in Aldridge Hall?
  (best distance 0.123, cutoff 0.6)

The best time to do laundry in Aldridge Hall is Tuesday or Wednesday morning.

Source: housing_aldridge_hall_laundry.txt

> What about on Sundays?
  (best distance 0.143, cutoff 0.6)

Based on the provided documents, if you do laundry on Sunday after 6pm, you will have to wait.

Sources: housing_aldridge_hall_laundry.txt (and other laundry documents retrieved alongside it)
```

**Proof it's the history doing the work, not shared vocabulary:** asking
the exact same follow-up with no prior turn —
`python app.py ask "What about on Sundays?"` — retrieves nothing about
laundry at all. It comes back with Halden Hall's Sunday dining closure,
the weekend shuttle schedule, and winter path-clearing, at a best distance
of 0.574 (barely under the 0.6 cutoff — one differently-worded question
away from being refused entirely). With the previous turn in history, the
same words retrieve the correct Aldridge Hall laundry chunk at 0.143. The
question's own words never mention laundry or Aldridge Hall; only the
history does.

## Stretch Feature: A Second Embedding Model

**Declared before building.** I'm going to install
`sentence-transformers>=3.4,<3.5`, add a second `--variant` index of
`campus_life` embedded with a different model instead of the bundled
`all-MiniLM-L6-v2`, and run the same test questions against both to see
what actually moves — which results change rank, and whether my measured
0.6 threshold (calibrated against MiniLM's distances in Milestone 4) still
sits in a clean gap once distances come from a different model.

**Built:** installed `sentence-transformers`, added
`AI201_EMBEDDING_MODEL` as an env-driven override in `config.py` (the same
pattern the starter already uses for `MODEL`), and indexed a second
`--variant mpnet` of `campus_life` with `all-mpnet-base-v2` — a larger,
768-dimension general-purpose model, versus MiniLM's 384. Ran the same ten
questions from the Milestone 4 table against both.

| Question | In corpus? | MiniLM | mpnet |
|---|---|---|---|
| How much printing quota does each student get per semester? | yes | 0.308 | 0.209 |
| How often does the campus shuttle run on weekdays? | yes | 0.183 | 0.155 |
| When can I change my meal plan tier? | yes | 0.216 | 0.243 |
| Is the CS 210 final exam curved? | yes | 0.441 | 0.426 |
| What's the best time to do laundry in Aldridge Hall? | yes | 0.123 | 0.136 |
| What is the capital of Mongolia? | no | 0.787 | 0.790 |
| How do I change the oil in a diesel engine? | no | 0.923 | 0.848 |
| Who won the 1994 World Cup? | no | 0.847 | 0.895 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.849 | 0.854 |
| How do I write a for loop in Rust? | no | 0.860 | 0.799 |

**What moved at the aggregate level:** less than I expected. The in-corpus
group's worst distance goes from 0.441 (MiniLM) to 0.426 (mpnet); the
out-of-scope group's best distance goes from 0.787 to 0.790. The gap
between the two groups is actually about as wide under mpnet (0.426-0.790)
as under MiniLM (0.441-0.787), and 0.6 still sits inside it comfortably.
On this test set, at least, my measured threshold didn't need to move —
which is itself worth writing down, since the general expectation (and the
one I declared above) was that it would.

**What moved underneath that, on the one question this corpus actually
stresses:** the aggregate numbers hide a real regression. For "Is the CS
210 final exam curved?", MiniLM's top-5 already had a sibling-document
mixup (`course_cs_340_exams.txt` ranked #1), but the chunk that actually
answers the question — "Two midterms and a final... the final is not
[curved]" — still placed 3rd, at 0.466, safely inside top-5 and under the
gate. Under mpnet, the *same chunk* drops to 14th place at 0.636 — outside
both top-5 and the 0.6 cutoff — while mpnet's actual top-5 is dominated by
other courses' exam-assessment paragraphs (`course_engl_205.txt`,
`course_phys_130.txt` twice, `course_stat_150.txt`) that share sentence
structure with the question but not its subject. Run end to end,
`python app.py --variant mpnet ask "Is the CS 210 final exam curved?"`
(with `AI201_EMBEDDING_MODEL=all-mpnet-base-v2` set) doesn't hallucinate —
it correctly says it doesn't have enough information — but that's a
question the MiniLM index answers correctly and cites right. A "better,"
larger general-purpose model made this corpus's one hard case worse, not
better: mpnet's larger vocabulary seems to weight the shared
"course — assessment" phrasing across departments more heavily than
MiniLM does, which is exactly the wrong signal for a corpus where the
department name is the fact that matters.

**Direction, overall:** of the 5 out-of-scope questions, 2 moved closer to
the 0.6 cutoff under mpnet (diesel engine: 0.923 → 0.848; Rust for loop:
0.860 → 0.799) — still safely above it here, but with less margin. Nothing
in this comparison suggests mpnet is a clear upgrade for this corpus; if
anything it's a lateral move with a worse worst-case.

---

# Week 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     week 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

- Produced by: `run_eval.py::main` (criteria 1, 2), `run_eval.py::check_out_of_scope`
  (criterion 3), and a manual sample via `app.py chunks -n 20` (criterion 4) —
  all four checked against the actual corpus text on disk for criterion 5.
- Primary evidence file: `results/run_2026-09-22_1302_before.md` — the exact
  `python run_eval.py --label before` invocation. Two additional, unlabeled
  re-runs the same week (`results/run_2026-09-24_0131.md`,
  `results/run_2026-09-24_0146.md`) are also committed; they land on the same
  sources and distances every time and are consistent with the primary file,
  which is what you'd expect since retrieval is deterministic and only the
  generated wording moves between runs.
- Corpus: `campus_life` · top-k 5 · relevance cutoff 0.6 · 3 runs per question,
  caching off.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks read as complete thoughts, not fragments | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. The cited source is the one that actually contains the fact | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

Criteria 3 and 4 don't vary run to run — the gate is a deterministic distance
comparison and chunking doesn't depend on the model, so the same number is
correct in all three columns rather than three independent measurements.

### Criterion 1 — evidence, the corpus's hardest case

From `results/run_2026-09-22_1302_before.md`, retrieval by `store.py::search`
over chunks from `chunker.py::split_documents`. `criteria.md` flagged this
question in advance as the one most likely to retrieve a sibling document
instead of the real answer:

```
### Is the CS 210 final exam curved? — run 1

- Best distance: 0.4409 (passed the gate)
- Sources retrieved: course_cs_210.txt, course_cs_210_exams.txt, course_cs_340.txt, course_cs_340_exams.txt
```

Even with `course_cs_340.txt` / `course_cs_340_exams.txt` (a different course,
same sentence shape) also pulled into the top-5, both `course_cs_210.txt` and
`course_cs_210_exams.txt` were retrieved, and both contain the answer
verbatim: *"Midterms are curved, the final is not."* Checked against every
other question's retrieved-sources list in the same file, the answering
document is present in all 5 cases across all 3 runs.

### Criterion 2 — evidence

From the same file, produced by `generate.py::answer_from_chunks`:

```
### How much printing quota does each student get per semester? — run 2

Each student gets $30 of printing per semester. (Source: admin_printing_quota.txt)
```

Every one of the 15 answers across the 3 runs (5 questions × 3 runs) names at
least one source, in every case the correct one — worded differently each
time (parenthetical, "Source:" line, occasionally both a primary and a
secondary source), but never absent.

### Criterion 3 — evidence

Produced by `run_eval.py::check_out_of_scope`, `gate.py::check`, cutoff 0.6:

```
| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.787 | refused |
| How do I change the oil in a diesel engine? | 0.923 | refused |
| Who won the 1994 World Cup? | 0.847 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.849 | refused |
| How do I write a for loop in Rust? | 0.860 | refused |
```

All five out-of-scope distances (0.787–0.923) clear the 0.6 cutoff with room
to spare — none within 0.18 of the line.

### Criterion 4 — evidence

Produced by `chunker.py::split_documents`, sampled with `python app.py chunks
-n 20` (chunking is deterministic, so a fresh sample today matches what
Milestone 3 indexed):

```
Chunk  |  source: admin_add_drop_deadline.txt#0
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.

Chunk  |  source: course_biol_160.txt#0
BIOL 160 Cell Biology

I lived here my sophomore year. Format is lecture three times a week with a weekly lab. Assessment: four unit tests and a cumulative final. Not curved.

Chunk  |  source: dining_halden_hall.txt#0
Halden Hall

I lived here my sophomore year. Wait times: rarely more than 8 minutes, even at noon. The thing worth going for is soup rotation, and the bread is baked on site. The thing to know is that closes at 7:00pm, which catches people out.

Chunk  |  source: housing_aldridge_hall_noise.txt#0
Noise levels in Aldridge Hall

Asked about this a lot so writing it down. Quiet floors on 3 and 4 are genuinely enforced.

Chunk  |  source: housing_tamsin_court.txt#3
Tamsin Court — what it's actually like

Laundry costs in-unit washer-dryer. On noise: quiet, structurally — concrete floors between units.
```

The first four are unambiguous passes. The fifth is the honest borderline
case: nothing is cut mid-word or mid-clause, so it passes the criterion as
written, but it reads as two facts (laundry, noise) glued together rather
than one clean thought. Checking the source file explains why — the
document itself packs both into a single paragraph with no `\n\n` between
them, so `split_documents` is faithfully reproducing one already-mixed
paragraph, not merging two clean ones. It's a real soft spot in the corpus
that the chunker can't fix on its own, not a chunking bug.

### Criterion 5 — evidence

Checked each cited source against the actual corpus file on disk:

```
admin_printing_quota.txt: "Every student gets $30 of printing per semester..."
→ cited answer: "Each student gets $30 of printing per semester (admin_printing_quota.txt)."

housing_aldridge_hall_laundry.txt: "Best time to do laundry here is Tuesday or Wednesday morning."
→ cited answer: "The best time to do laundry in Aldridge Hall is Tuesday or Wednesday morning. Source: housing_aldridge_hall_laundry.txt"

course_cs_210_exams.txt: "Midterms are curved, the final is not."
→ cited answer: "No, the CS 210 final exam is not curved. Source: course_cs_210_exams.txt (and course_cs_210.txt)"
```

All 5 questions, across all 3 runs, cite a document that actually contains
the fact asked about — never a sibling document that's merely on-topic. The
CS 210 case is the one criterion 5 was written to stress (`criteria.md` calls
out this exact sibling pair), and it holds: both files named actually contain
the curve fact, unlike the `course_cs_340*` siblings that were retrieved but
never cited.

## Verdicts

No criteria were revised — all five were measurable exactly as written in
`criteria.md`, and the run log's numbers are what decided each verdict below,
not a judgment call about whether the target was fair.

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunks contain the answer | MET | 5/5 in all three runs, against a 4/5 target — but I didn't stop at "the right document's name showed up in the sources list." Chunking splits multi-paragraph documents, so I re-ran `app.py retrieve` directly on the one question `criteria.md` flagged as the corpus's hardest case (CS 210 vs. its CS 340 lookalike) and confirmed the specific chunk containing "Midterms are curved, the final is not" ranked #2 and #3 of 5 — not just some other paragraph from the same file riding along on the document's name. Did the same spot-check for the shuttle and laundry questions: in both, the answer-bearing chunk is literally the #1 result. |
| 2 | Every answer names a source | MET | Exact match to the 5/5 target, not just a majority: all 15 answers (5 questions × 3 runs) name at least one source, and in every case it's the correct one. The wording varies (parenthetical, a "Source:" line, sometimes a primary plus a secondary source), but the source line itself never goes missing. |
| 3 | Gate stops out-of-corpus questions | MET | 5/5 refused against a 4/5 target, and not a near thing — the closest out-of-scope distance (0.787, "capital of Mongolia") still sits 0.19 above the 0.6 cutoff, well clear of the boundary. |
| 4 | Chunks read as complete thoughts, not fragments | MET | 5/5 of a fresh 5-chunk sample start and end on complete sentences, against a 4/5 target. One sample (`housing_tamsin_court.txt#3`) reads as two facts — laundry, then noise — glued into one chunk, but nothing is cut mid-word or mid-clause, so it satisfies the criterion as I wrote it. I checked the source file: that document itself packs both facts into a single paragraph with no `\n\n` break, so the chunker is faithfully reproducing one already-mixed paragraph, not failing to split a clean one. I'm calling this MET rather than treating it as a miss, but I don't think it's a coincidence-free 5/5 either — see "What I'd Do Differently" below. |
| 5 | The cited source is the one that actually contains the fact | MET | Checked all 15 citations against the actual corpus text on disk (not just against the retrieved-sources list) — every one names a document I confirmed contains the specific fact asked about, including the CS 210 pair this criterion was written to stress, where the system never once cited the CS 340 sibling that also got retrieved. |

## Diagnoses

I missed nothing — all five criteria held on every run, including the two
near-miss cases I stress-tested past the aggregate numbers in Verdicts
(criterion 1's CS 210 sibling pair, criterion 4's Tamsin Court chunk). Neither
came close to failing: the CS 210 answer chunk ranked 2nd and 3rd of 5, not
5th, and the Tamsin Court chunk had no boundary damage at all, just a
topic-mixing problem the criterion wasn't built to catch. Clearing every
criterion on a 5-question test set against a corpus this well-behaved isn't
evidence the system is excellent — it's evidence the targets had room in
them. Here's where, specifically, and what I'd tighten:

**1. Criterion 4 (chunks read as complete thoughts) — the clearest case.**
The literal bar — "nothing cut mid-word or mid-clause" — only checks for
boundary damage at the **chunking** stage. It has nothing to say about
whether a chunk is topically coherent, so it let a real problem straight
through: `housing_tamsin_court.txt#3` reads as two unrelated facts (laundry
machines, then noise levels) glued into one chunk. The mechanism isn't a
chunker bug — `chunker.py::split_documents` faithfully reproduced one
paragraph of the source document, and that paragraph itself mixes two facts
with no `\n\n` between them (confirmed by reading
`corpora/campus_life/documents/housing_tamsin_court.txt` directly). A
chunker that produced this exact chunk from garbled input would still pass
my criterion, which means the criterion isn't actually testing what
`split_documents`'s docstring claims the strategy achieves ("splitting on
paragraph breaks pulls [separable facts] apart into chunks that each answer
one question"). Tighter version: *"For at least 4 of 5 sampled chunks, the
chunk covers exactly one fact or sub-topic — I can state what it's about in
one clause, with no second, unrelated clause mixed in."* That's a test of
topical cohesion, not just string integrity, and it's the one my current
sample would have actually failed on (4/5, not 5/5 — still clearing the
target, but for the first time by the intended margin instead of trivially).

**2. Criterion 1 (retrieved chunk contains the answer) — margin, not
presence.** `criteria.md` predicted the CS 210 question as the place
sibling-document confusion at the **retrieval** stage might push the real
answer out of the results, because `course_cs_340_exams.txt` (a different
course, same sentence shape) out-scores it on raw distance. It does — that
sibling chunk ranks #1 — but the answer-bearing chunk still lands at #2 and
#3 out of the 5 retrieved, well inside `TOP_K`. The current criterion asks
only "is it anywhere in the top 5," which this corpus's one hard case
clears with two spots to spare — the criterion never gets close enough to
the failure mode it was written to catch. Tighter version: *"the retrieved
top **three** chunks include one that contains the answer, for at least 4
of 5 questions"* — same question set and count, but a narrower net that
would have actually put the CS 210 case's margin on the line instead of
letting `TOP_K=5` absorb it.

**The pattern underneath both.** Both near-misses I found — sibling
*documents* competing on phrasing (CS 210 vs. CS 340) and sibling *facts*
crammed into one paragraph (Tamsin Court's laundry-and-noise chunk) — trace
back to the same property of `campus_life`: near-duplicate content, either
across files or within one file's own paragraphs. That's exactly what I
flagged as the risk in `criteria.md` before I had any results, for criteria
1, 4, and 5 alike. The system handled every instance of it I could find in
this test round, but the fact that my two tightened criteria above are both
instances of it, and not something unrelated, tells me it's the one place
worth watching if I add more test questions later — not three separate
problems, but one property of the corpus showing up in two different
stages.

**Why I'm not tightening criteria 2, 3, or 5.** Criterion 2 held at an exact
5/5 across all 15 answers with no near-misses to stress-test. Criterion 3
held with a 0.19 margin on its closest out-of-scope question — not a number
that was narrowly avoided. Criterion 5 held cleanly on the one
sibling-document pair (CS 210/CS 340) it was explicitly designed to stress,
and the wrong document was never cited once across 15 answers. Nothing in
this round gives me a specific reason to believe those three are hiding a
failure mode the way 1 and 4 are.

## The Improvement

**What I changed:** `store.py::search` now blends BM25 keyword scoring with
the existing semantic (cosine-distance) search, combined by reciprocal rank
fusion (RRF), instead of ranking purely on embedding distance. Because the
corpus is small (183 chunks), both signals are computed over the entire
(optionally category-filtered) collection on every query — no separate
persistent BM25 index to keep in sync after a re-index. Each `Result`'s
`distance` field is still the unmodified semantic cosine distance, so the
relevance gate's 0.6 cutoff keeps meaning exactly what it meant before;
only which chunks make the top-k, and in what order, changed.

**Why I picked it:** Milestone 3's diagnosis named a specific mechanism, not
just a symptom: for "Is the CS 210 final exam curved?", `course_cs_340_exams.txt`
(a different course, near-identical sentence shape) outranks the real answer
document on raw semantic distance, because the two documents' assessment
paragraphs are almost the same prose and differ mainly in one exact
token — the course number. That's the textbook case for hybrid search: a
semantic embedding is rewarded for phrasing similarity and can't tell "210"
from "340" apart on meaning, but BM25 rewards the literal token match on
whichever number the question actually asked about.

### Run Log — After

Produced the same way as Before: `python run_eval.py --label after`, 3 runs
per question, caching off, same corpus/top-k/threshold. Full transcript:
`results/run_2026-09-24_0233_after.md`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks read as complete thoughts, not fragments | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. The cited source is the one that actually contains the fact | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

Real output, `store.py::search` (retrieval) → `generate.py::answer_from_chunks`
(generation), from `results/run_2026-09-24_0233_after.md`:

```
### Is the CS 210 final exam curved? — run 1

- Best distance: 0.4409 (passed the gate)
- Sources retrieved: course_cs_210.txt, course_cs_210_exams.txt, course_cs_340.txt, course_cs_340_exams.txt

No, the CS 210 final exam is not curved (source: `course_cs_210_exams.txt` and `course_cs_210.txt`).
```

```
### What is the capital of Mongolia? (out-of-scope)

Best distance: 0.826 — refused
```

**Did it help?**

Yes, on the exact mechanism the diagnosis named — but my own five criteria are
too loose to show it, which is precisely the slack Milestone 3 flagged.

Side by side, the Before and After criterion tables are identical: 5/5 on
every criterion, every run, both times. Taken at face value, that reads as
"no effect." It isn't — it's that none of my original targets were tight
enough to see this specific fix, the same gap I named in Milestone 3 when I
proposed tightening criterion 1 from "top 5" to "top 3." I checked that
tightened version too: it *still* wouldn't have shown a difference, because
even before the fix, `course_cs_210.txt` (which also contains "Midterms are
curved, the final is not") already ranked #2 of 5. Top 3 wasn't tight enough
either. The version that actually isolates the mechanism is stricter still —
**is the #1-ranked chunk one that contains the answer** — and checking that
directly with `app.py retrieve` shows the real change:

| Question | #1 chunk, before | #1 chunk, after |
|---|---|---|
| Printing quota | `admin_printing_quota.txt` (correct) | `admin_printing_quota.txt` (correct) |
| Shuttle schedule | `transit_shuttle.txt` (correct) | `transit_shuttle.txt` (correct) |
| Meal plan change window | `admin_meal_plan_changes.txt` (correct) | `admin_meal_plan_changes.txt` (correct) |
| CS 210 exam curve | `course_cs_340_exams.txt` (**wrong course**) | `course_cs_210_exams.txt` (correct) |
| Aldridge laundry time | `housing_aldridge_hall_laundry.txt` (correct) | `housing_aldridge_hall_laundry.txt` (correct) |

Before the change, the #1 slot for the CS 210 question was the wrong
document — the model still answered correctly because the real answer was
lower in its context window, not because retrieval got it right. After the
change, the correct document leads, and `course_cs_340_exams.txt` drops to
#3. Nothing else in that table moved: hybrid search didn't touch the four
questions that were already unambiguous, and it didn't break anything that
was working.

**A real cost, not just a win.** Checking the full retrieved sets (not just
#1), hybrid search also pulled less-relevant documents into ranks 2–5 for
some easy questions purely on generic word overlap — e.g. the printing
quota question now retrieves `admin_wifi_and_accounts.txt` and
`study_group_rooms.txt` in place of documents that were at least on-topic
before. It didn't cost anything measurable here (the model still answered
correctly and cited the right source every time), but it's a real trade,
not a free win: BM25 rewards *any* shared token, including generic ones like
"student" or "per," not just the meaningful ones like "210."

**No regression on the gate.** All 5 out-of-scope questions are still
refused, though three of their reported best-distances shifted (e.g.
"capital of Mongolia" moved from 0.787 to 0.826) — an honest side effect of
the gate now checking the minimum distance within the *fused* top-5 rather
than the single closest chunk in the whole collection. In every case the
shift left them further from the 0.6 cutoff, not closer, so no refusal
flipped, but it's worth naming: hybrid search makes the reported "best
distance" a slightly less pure measurement of "how semantically close is
the nearest thing in the corpus" than it was before.

## What's Still Broken

No criterion is currently MISSED, before or after the fix, so this section
isn't a list of failures — it's the honest list of things I found and chose
not to touch this unit, either because the one-change rule meant I'd already
spent my fix, or because nothing actually failed on them yet.

**1. The Tamsin Court chunk still mixes two facts (criterion 4's blind
spot).** `housing_tamsin_court.txt#3` — laundry and noise glued into one
chunk — is unchanged. I didn't fix it because it's a single-document
symptom of a corpus-authoring issue (that document's own paragraph mixes
two topics with no `\n\n` between them), not a chunker bug, and I already
used this unit's one allowed change on hybrid search, which addressed the
near-miss I'd actually verified was closer to failing (CS 210). If I keep
working on this: either hand-split that one paragraph in the source
document, or add a chunker heuristic that looks for a topic-shift sentence
(e.g. a sentence starting "On noise:" after a laundry sentence) and splits
on it even without a `\n\n`. I'd want to see at least one more example of
this pattern elsewhere in the corpus before writing that heuristic, though —
one instance isn't enough to justify a general rule, and I haven't gone
looking for a second one yet.

**2. Hybrid search's own cost: generic-word noise in ranks 2–5.** Milestone
4 found that BM25 pulls documents into the middle of the results purely on
shared common words ("student," "per") rather than meaningful ones. It
never changed a final answer or a citation in this test round, so no
criterion caught it, but it's a real, unaddressed cost of the fix I shipped.
The standard remedy is IDF-weighted down-weighting of common terms or a
stopword list before tokenizing for BM25 — `_tokenize` in `store.py` doesn't
do either right now. I didn't add it because it would have been a second
change to the same commit, which is exactly what Milestone 4 says not to do.

**3. ~~The gate's "best distance" is a slightly less pure number now.~~ Fixed
below, as the second stretch improvement.** This originally read: since the
gate checks the minimum distance within the *fused* top-k rather than the
single closest chunk in the whole collection, an out-of-scope question's
reported distance can shift (0.787 → 0.826 for "capital of Mongolia") even
though nothing about how unrelated it is changed. It never flipped a
refusal, so criterion 3 never saw it, but it was exactly the kind of thing
worth fixing on its own: "is this in-corpus at all" and "which chunks answer
it best" are two different questions that were sharing one number by
coincidence of implementation, not by design. See "Stretch Feature: A
Second Measured Improvement" below for the fix and its own before/after
comparison.

**4. Five test questions is a small net.** Every verdict in this README
rests on 5 in-corpus and 5 out-of-scope questions. That was the right size
to *write* criteria against in Week 1, but it means a MET verdict here is a
claim about this specific, small sample, not a guarantee that a sixth
question wouldn't surface something new. I stopped at 5 because that's what
the assignment specifies, not because I think 5 is enough to be confident
in — it's the honest boundary of what this test round can tell me.

## What I'd Do Differently

**Criterion 1 (retrieved chunk contains the answer) — I'd write it around
rank, not presence.** "In the top 5" turned out to have so much slack that
even the corpus's one deliberately-engineered hard case (CS 210 vs. CS 340)
passed it before *and* after the fix, with nothing to distinguish them. The
version that actually moved between before and after — "the #1-ranked
chunk contains the answer" — is what I'd write next time. It's a harder bar
(4/5 might be the realistic target, not 5/5, since the printing-quota and
meal-plan questions have less obviously-dominant #1 candidates than the
laundry question does), but a criterion that can't distinguish a fixed
pipeline from a broken one isn't earning its place.

**Criterion 4 (chunks read as complete thoughts) — I'd test cohesion, not
just boundaries.** "Nothing cut mid-word or mid-clause" is a real thing to
check, but it turned out to be almost impossible to fail on this corpus —
`split_documents` never mangles a string, it just sometimes reproduces a
source paragraph that was already mixing two topics. What I actually cared
about when I wrote this criterion in Week 1 was "does one chunk answer one
question," and boundary integrity isn't a proxy for that. Next time:
"for at least 4 of 5 sampled chunks, I can state what the chunk is about in
one clause, with no second, unrelated clause mixed in" — same sampling
method, a bar that actually tests the thing I meant.

**Criteria 2, 3, and 5 I'd leave as written.** None of them had slack I
could find evidence for this round — 2 held at an exact 5/5 with no
wording variance, 3 held with real margin (0.19+) on its closest
out-of-scope question, and 5 held cleanly on the one sibling pair it was
built to stress. Tightening a criterion just because the other two needed
it would be inventing a problem rather than reporting one.

## Stretch Feature: A Second Measured Improvement — Decoupling the Gate from Hybrid Fusion

**Declared before building** (see commit history for the timestamp on this
line vs. the implementation commit). "What's Still Broken" above names a
real, unaddressed side effect of Milestone 4's hybrid-search fix: the
relevance gate now reports the minimum distance within the *fused* top-k,
not the true closest chunk in the whole collection, because a BM25-favored
chunk can push the single nearest semantic match out of the top-k entirely.
Three of the five `OUT_OF_SCOPE` questions' reported best-distances already
shifted because of this (e.g. "capital of Mongolia": 0.787 → 0.826) even
though nothing about how unrelated they are changed.

I'm going to give the gate its own cheap, semantic-only lookup —
`store.py::semantic_best_distance` — a single top-1 Chroma query with no
BM25 involved, so "is this question in-corpus at all" (the gate's job,
calibrated in Week 1 against pure cosine distance) is answered independently
of "which chunks best answer it" (hybrid retrieval's job, Milestone 4). Right
now those two questions are sharing one number by accident of implementation,
not by design. I expect this to restore the three shifted out-of-scope
distances to their original pre-hybrid values and to leave everything
Milestone 4 fixed (the CS 210 rank-1 result) untouched, since generation
still gets its chunks from the same fused `search()` as before — only the
gate's own number changes.

**Built:** added `store.py::semantic_best_distance(question, corpus, variant,
category)` — a single `collection.query(..., n_results=1)` call with no BM25
mixed in, returning just the nearest neighbour's raw cosine distance.
`gate.py::check` now takes an optional `best_distance` override parameter;
when given, it's used directly instead of being recomputed from the
retrieved `results` list. `app.py::ask_pipeline`, `app.py::cmd_retrieve`,
`run_eval.py::run_once`, and `run_eval.py::check_out_of_scope` all now call
`semantic_best_distance` with the same query text they pass to `search()`,
and hand the result to `gate.check` as `best_distance`. `search()` itself —
and therefore what generation sees — is untouched.

### Run Log — Second Improvement

Produced the same way as Before/After: `python run_eval.py --label
after-gate-fix`, 3 runs per question, caching off, same corpus/top-k/
threshold. Full transcript:
`results/run_2026-09-24_0240_after-gate-fix.md`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks read as complete thoughts, not fragments | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. The cited source is the one that actually contains the fact | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

Produced by `run_eval.py::check_out_of_scope` calling the new
`store.py::semantic_best_distance`, cutoff 0.6:

```
| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.787 | refused |
| How do I change the oil in a diesel engine? | 0.923 | refused |
| Who won the 1994 World Cup? | 0.847 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.849 | refused |
| How do I write a for loop in Rust? | 0.860 | refused |
```

**Did it help?** Yes, exactly as predicted, and this time the numbers show
it directly instead of needing a side lookup. Same criterion table as
Before and After — still 5/5 across the board — because nothing here was
broken at the criterion level either. But the specific number the
declaration predicted moved back:

| Out-of-scope question | Before hybrid | After hybrid (Milestone 4) | After gate fix |
|---|---|---|---|
| Capital of Mongolia | 0.787 | 0.826 | **0.787** |
| Diesel engine oil change | 0.923 | 0.934 | **0.923** |
| 1994 World Cup | 0.847 | 0.847 | 0.847 |
| Ibuprofen dosage | 0.849 | 0.849 | 0.849 |
| Rust for loop | 0.860 | 0.877 | **0.860** |

All three distances that hybrid search had shifted are back to their exact
pre-hybrid values — the gate is once again reporting the true nearest
semantic neighbour, not the minimum within a fused top-k. The two that
hadn't moved stayed put, which is what should happen if this change touches
only the gate's own number and nothing else. I also re-checked the CS 210
case specifically to confirm the fix didn't undo Milestone 4's win:
`app.py retrieve "Is the CS 210 final exam curved?"` still ranks
`course_cs_210_exams.txt` at #1, because that check runs through `search()`
(hybrid, unchanged) and this improvement only touches what `gate.check`
sees, not what generation sees.

No criterion moved, because no criterion was built to notice a change in
number purity rather than a change in pass/fail — the same shape of result
as Milestone 4, and for the same reason. What this improvement bought is
narrower than Milestone 4's: not a different retrieval outcome, but a
gate whose calibration (Week 1's 0.6, measured against pure cosine
distance) means what it originally meant again, independent of whatever
`search()` does internally.


---

## Capstone

**The System**

The Unofficial Guide over the `campus_life` corpus — the same retrieval pipeline
as Weeks 1–2 (paragraph chunks, hybrid BM25 + semantic search, the relevance
gate decoupled from fusion, Gemini for the grounded answer), unchanged. This
unit extends it; it does not touch how it answers.

**The Shape**

Shape **A — deploy and instrument**, on **Path B (local with logs)**. The
pipeline already has an HTTP wrapper (`serve.py`: `POST /ask`, `GET /health`)
that was shipped deliberately bare — no logging, no timing, no metrics. What I'm
adding is the operational layer around it: one structured log record per
request (timestamp, question in, answer out, whether the gate refused, number of
chunks retrieved, end-to-end latency, and the token counts the model call
reports), a single documented command that starts the service under gunicorn,
and a cost-per-request number worked out from those logged token counts rather
than from the pricing page. I'm on Path B because the system carries a local
embedding model (ONNX MiniLM, ~80 MB, plus an optional sentence-transformers
variant), and the point of this path is that someone who isn't me can reproduce
the run from a clean checkout with one command and a committed log.

When I'm finished I'll claim: *every request to the service leaves a record I
can query after the fact, and I can say from that record how long a request
takes and what it costs.*

**Out of Scope**

- **No changes to retrieval, chunking, the gate, or the prompt.** I'm not adding
  a third retrieval strategy or re-tuning the threshold. If a criterion exposes a
  retrieval problem, I'll diagnose and fix it as the one improvement — but I'm
  not going looking for one.
- **No hosting signup.** No Path A: no platform account, no URL, no card. A
  deployed version is a stretch item at most, not part of the plan.
- **No new interface and no new endpoints** beyond what `serve.py` has. I may
  add a log-reading helper script, but the service's API doesn't change.
- **No per-stage latency breakdown, load testing, or metrics dashboard.** One
  end-to-end latency field is the plan; a stage breakdown and a 10× load run are
  declared stretch items, to be written down before I start them.

**Size check.** The build is one piece of work with three small parts that all
serve it: a logging wrapper in `serve.py`, capturing token usage from the
Gemini response, and a `RUNNING.md` section with the start command and
environment. Estimated well under ninety minutes.


**Instrumentation**

First 10 of 20 entries from `logs/requests.jsonl` (full file committed). (An earlier test run, not committed, showed a 20 s first request on a cold server; this run was already warm.)

```json
{"ts": "2026-11-12T16:56:11.567+00:00", "request_id": "f38bc47b", "question": "How much printing quota does each student get per semester?", "answer": "Each student gets $30 of printing per semester, which is about 600 black-and-white pages (admin_printing_quota.txt).", "refused": false, "best_distance": 0.3077, "n_sources": 5, "status": 200, "latency_ms": 1691, "error": null, "model_calls": 1, "prompt_tokens": 427, "output_tokens": 33}
{"ts": "2026-11-12T16:56:15.015+00:00", "request_id": "c2c3b1f9", "question": "How often does the campus shuttle run on weekdays?", "answer": "The campus shuttle runs every 20 minutes on weekdays (transit_shuttle.txt).", "refused": false, "best_distance": 0.1825, "n_sources": 5, "status": 200, "latency_ms": 1397, "error": null, "model_calls": 1, "prompt_tokens": 414, "output_tokens": 19}
{"ts": "2026-11-12T16:56:24.308+00:00", "request_id": "13f1c32c", "question": "When can I change my meal plan tier?", "answer": "You can change your meal plan tier once, during the first ten days of the semester. After that, it is locked. \n\nSource: admin_meal_plan_changes.txt", "refused": false, "best_distance": 0.2161, "n_sources": 5, "status": 200, "latency_ms": 7247, "error": null, "model_calls": 1, "prompt_tokens": 378, "output_tokens": 38}
{"ts": "2026-11-12T16:56:38.637+00:00", "request_id": "dbede4a4", "question": "Is the CS 210 final exam curved?", "answer": "No, the CS 210 final exam is not curved. \n\nSource: `course_cs_210.txt` (and also found in `course_cs_210_exams.txt`)", "refused": false, "best_distance": 0.4409, "n_sources": 4, "status": 200, "latency_ms": 12303, "error": null, "model_calls": 1, "prompt_tokens": 425, "output_tokens": 47}
{"ts": "2026-11-12T16:56:49.553+00:00", "request_id": "a91be392", "question": "What's the best time to do laundry in Aldridge Hall?", "answer": "The best time to do laundry in Aldridge Hall is Tuesday or Wednesday morning (housing_aldridge_hall_laundry.txt).", "refused": false, "best_distance": 0.1226, "n_sources": 5, "status": 200, "latency_ms": 8892, "error": null, "model_calls": 1, "prompt_tokens": 346, "output_tokens": 28}
{"ts": "2026-11-12T16:56:52.063+00:00", "request_id": "fd7fa185", "question": "What is the capital of Mongolia?", "answer": "I don't have enough information about that.", "refused": true, "best_distance": 0.7873, "n_sources": 0, "status": 200, "latency_ms": 470, "error": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
{"ts": "2026-11-12T16:56:55.120+00:00", "request_id": "c7eb6722", "question": "How do I change the oil in a diesel engine?", "answer": "I don't have enough information about that.", "refused": true, "best_distance": 0.9228, "n_sources": 0, "status": 200, "latency_ms": 900, "error": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
{"ts": "2026-11-12T16:56:57.539+00:00", "request_id": "3ea0b232", "question": "Who won the 1994 World Cup?", "answer": "I don't have enough information about that.", "refused": true, "best_distance": 0.8474, "n_sources": 0, "status": 200, "latency_ms": 382, "error": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
{"ts": "2026-11-12T16:56:59.954+00:00", "request_id": "353eccc7", "question": "What is the recommended dosage of ibuprofen for a headache?", "answer": "I don't have enough information about that.", "refused": true, "best_distance": 0.8487, "n_sources": 0, "status": 200, "latency_ms": 371, "error": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
{"ts": "2026-11-12T16:57:02.581+00:00", "request_id": "ad8a3c8f", "question": "How do I write a for loop in Rust?", "answer": "I don't have enough information about that.", "refused": true, "best_distance": 0.8598, "n_sources": 0, "status": 200, "latency_ms": 593, "error": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
```

Failed runs, from a second server started with `GEMINI_API_KEY=bad-key` (log
written to a separate file so the committed run record stays clean). The
first is a model-call failure that reaches the user as HTTP 500 and is still
logged: `model_calls` is 1 because the call was attempted, tokens are 0
because none were billed. The second is a rejected empty input (HTTP 400).

```json
{"ts": "2026-11-12T18:35:19.494+00:00", "request_id": "9459691d", "question": "Is the CS 210 final exam curved?", "answer": null, "status": 500, "latency_ms": 11315, "error": "ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}", "model_calls": 1, "prompt_tokens": 0, "output_tokens": 0}
{"ts": "2026-11-12T18:35:19.976+00:00", "request_id": "17bdd79d", "question": "", "answer": null, "status": 400, "latency_ms": 0, "error": "empty question"}
```

**Tested from a clean checkout.** I cloned the repo into a new folder, built a
fresh venv, and followed `RUNNING.md`. It ran, but the Capstone section as
first written would have failed a reader in three places: it never said to
create the venv or `.env`, never said the key goes in `.env`, and `chroma_db/`
is gitignored so `/health` would say `index_ready: false` until
`python app.py index` runs. I rewrote `RUNNING.md` to cover all three. The
clone's first request took 13.2 s (cold start).

**What It Costs**

Measured from the 10 answered requests in `logs/requests.jsonl` (5 test
questions x 2 passes, cache off so every one reached the model; token counts
are read from Gemini's `usage_metadata`, not estimated):

| | mean | median | min | max |
|---|---|---|---|---|
| prompt tokens | 398 | 414 | 346 | 427 |
| output tokens | 33 | 33 | 19 | 47 |
| latency (ms) | 5,537 | 4,114 | 1,397 | 12,303 |

- **One answered request is about 431 tokens (398 in + 33 out) and about 5.5 s.**
- **A refused request costs 0 tokens and about 0.5 s** (mean of 10: 528 ms): the
  gate refuses before any model call.
- I did **not** convert tokens to dollars: I haven't verified published pricing
  for `gemini-3.5-flash-lite`, and on the free tier actual spend is $0. Tokens
  and seconds are what I measured.
- Latency spread (1.4 s to 12.3 s for near-identical prompts) is dominated by
  the hosted model call, not retrieval: refusals, which skip it, finish in
  under 1 s.


**Capstone Run Log**

Run with `python tools/capstone_test.py <N>` (file: `tools/capstone_test.py`), three
separate trials, each starting fresh servers, a fresh log, cache off. Raw output for
every trial is in `results/capstone/trial<N>.jsonl` (the service's own log) and
`trial<N>.json` (the harness's per-criterion detail). Criteria and targets are in
`criteria.md`, committed in `328d4fa` before any results.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every request leaves a complete log record | 20 of 20 lines | 20/20 | 20/20 | 20/20 | MET |
| 2. Failed model call: readable 500, under 30 s, logged | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Answered requests under 10 s | 9 of 10 | 10/10 | 9/10 | 10/10 | MET |
| 4. Tokens / model calls attributed to the right request under 3 concurrent clients | 20 of 20 lines | 8/20 | 9/20 | 11/20 | MISSED |
| 5. Gate still refuses out-of-scope, 0 model calls | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |

**A harness bug, disclosed.** My very first trial 1 scored criterion 3 at 0/10
(criterion 4 scored 4/20 there too, and missed in the re-runs as well; its count
varies with how the threads happen to overlap). The cause was my test client, not the service:
on this Windows machine requests to `localhost` take ~2 s to resolve vs ~40 ms for
`127.0.0.1` (measured: 2344 / 2058 ms vs 38 / 37 ms on `/health`), which put every
client-measured latency ~2 s above the logged one and tripped criterion 3's
250 ms cross-check. I switched the client to `127.0.0.1`, kept the original output
as `results/capstone/trial1_localhost_harness_bug.*`, and re-ran all three trials.
Only the client address changed; no criterion or target was touched. The table
above is the re-run.

**Evidence, from trial 3 unless noted** (log lines written by `serve.py::log_request`,
called from `serve.py::ask`; answers/errors truncated with …):

*Criterion 1 — all 20 lines present, with the required keys (harness count: `lines_added: 20, complete_lines: 20`). The three request types that don't produce an ordinary answer:*

```json
{"ts": "2026-11-12T18:59:54.158+00:00", "request_id": "5ae2bfba", "question": "What is the capital of Mongolia?", "answer": "I don't have enough information about that.", "refused": true, "best_distance": 0.7873, "n_sources": 0, "status": 200, "latency_ms": 315, "error": null, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
{"ts": "2026-11-12T18:59:54.930+00:00", "request_id": "62d119a8", "question": "", "answer": null, "status": 400, "latency_ms": 0, "error": "empty question"}
{"ts": "2026-11-12T19:00:00.472+00:00", "request_id": "4093f3bb", "question": "How much printing quota does each student get per semester?", "answer": null, "status": 500, "latency_ms": 5514, "error": "ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. …", "model_calls": 1, "prompt_tokens": 0, "output_tokens": 0}
```

*Criterion 2 — client view of the five bad-key requests (harness, trial 3 `c2.detail`):*

```
{"status": 500, "ms": 637, "exc": null, "logged_status": 500}
{"status": 500, "ms": 500, "exc": null, "logged_status": 500}
{"status": 500, "ms": 344, "exc": null, "logged_status": 500}
{"status": 500, "ms": 360, "exc": null, "logged_status": 500}
{"status": 500, "ms": 597, "exc": null, "logged_status": 500}
```

*Criterion 3 — (client ms, logged ms) per request, all three trials:*

```
trial 1: [(3124, 3116), (2050, 2029), (7838, 7819), (1387, 1383), (1283, 1276), (1306, 1288), (1573, 1472), (1367, 1362), (2407, 2385), (1341, 1328)]
trial 2: [(1068, 1063), (8880, 8858), (8766, 8747), (8827, 8816), (1373, 1351), (8810, 8793), (6019, 6015), (25655, 25649), (8283, 8254), (1984, 1775)]
trial 3: [(7599, 7595), (6401, 6375), (1184, 1179), (4959, 4954), (7000, 6974), (4583, 4572), (3619, 3615), (4071, 4066), (5791, 5786), (4973, 4948)]
```

Trial 2 had one request at 25 655 ms (a slow model call, the 1 in 10 the target
allows); the logged time matches the client's, so the log is honest about it.

*Criterion 4 — log lines from the concurrent phase where the counts are wrong.
Each of these is ONE answered request, yet it logs `model_calls` of 2 or more:*

```json
{"question": "When can I change my meal plan tier?", "status": 200, "refused": false, "latency_ms": 2944, "model_calls": 3, "prompt_tokens": 378, "output_tokens": 31}
{"question": "How often does the campus shuttle run on weekdays?", "status": 200, "refused": false, "latency_ms": 3019, "model_calls": 3, "prompt_tokens": 792, "output_tokens": 52}
{"question": "How much printing quota does each student get per semester?", "status": 200, "refused": false, "latency_ms": 3438, "model_calls": 5, "prompt_tokens": 1219, "output_tokens": 88}
```

*Criterion 5 — refused questions (trial 3):*

```json
{"question": "What is the capital of Mongolia?", "answer": "I don't have enough information about that.", "refused": true, "best_distance": 0.7873, "n_sources": 0, "status": 200, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
{"question": "How do I change the oil in a diesel engine?", "answer": "I don't have enough information about that.", "refused": true, "best_distance": 0.9228, "n_sources": 0, "status": 200, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
```


**Capstone Verdicts**

Against the targets in `criteria.md` (unchanged, no criterion revised):

| # | Target | Trials | Verdict |
|---|---|---|---|
| 1 | 20/20 complete log lines | 20, 20, 20 | **MET** |
| 2 | 5/5 readable, logged 500s under 30 s | 5, 5, 5 | **MET** |
| 3 | at least 9/10 answered under 10 s | 10, 9, 10 | **MET** (trial 2 sat exactly on the line) |
| 4 | 20/20 correctly attributed lines | 8, 9, 11 | **MISSED** (all three trials) |
| 5 | 5/5 out-of-scope refused, 0 model calls | 5, 5, 5 | **MET** |

**Capstone Diagnosis**

*Criterion 4 — the one miss.* **Stage: the usage accounting in `serve.py::ask`
(`usage_since`), which reads process-wide counters in `generate.py`
(`_session_calls`, `_session_prompt_tokens`, `_session_output_tokens`).
Mechanism: concurrency.** `ask` snapshots the counters when a request starts and
subtracts when it ends, which gives that request's usage only if no other request
makes a model call in between. `python serve.py` runs each request in its own
thread, so with 3 clients a request's window overlaps others' calls and it is
charged for them. The evidence is in the logs: in the three trials 12, 11 and 9 of
20 lines were wrong, and the wrong ones are the signature of this mechanism, not
of random corruption. Single answered requests logged `model_calls` of 2, 3, 4, 7,
8, 10 and 14 when each makes exactly one call (a slow call is billed to every
request that overlapped it, hence the big numbers), and about one refused request
per trial logged non-zero counts it never earned. Same logged latency, same
retrieval, same answers; only the attribution is wrong. This did not show up in
the 20-request run record from Milestone 3 or in criteria 1, 3 or 5, because they
send one request at a time.

*Pattern.* There is one problem, not several: the only miss traces to the one
design choice that per-request numbers are derived from shared state. It also
means the "What It Costs" figures above (398 in / 33 out tokens per answered
request) are valid, because they came from sequential requests, but the log's
token fields are untrustworthy for any real concurrent use, and anyone summing them
to estimate cost under load would get an inflated number.

*Were the met targets too easy?* Honestly, partly. Criteria 1 and 5 were the
safe ones, by design, and held easily. Criterion 2 passed with a wide margin (all
failures returned in under 0.7 s against a 30 s limit), but only tests a *fast*
failure (an invalid key); there is no timeout in `serve.py`, so a model call that
*hangs* would not be caught by it. If I tightened one it would be criterion 2: add
a case where the model call never returns and require a 500 within 30 s. I expect
that would miss. Criterion 3 is the one that genuinely carries risk (trial 2 had 9,
with one request at 25.7 s).

**The Improvement (declared before building)**

One change, aimed at criterion 4's mechanism: make the usage counters
**per-thread** instead of per-process. `generate.py` gets a `threading.local()`
that `generate()` and `_record_tokens` update alongside the existing session
counters (which stay, so `usage()` and `app.py` are unchanged), plus a small
`thread_usage()` accessor; `serve.py::ask` reads that instead of subtracting
global snapshots. Each request runs in one thread end to end (including the model
call), so its counters can only contain its own calls. I expect criterion 4 to go
to 20/20 in all three trials and criteria 1, 2, 3 and 5 not to move. The risk I'm
watching is that the fix quietly breaks the single-request numbers, so I'll compare
sequential token counts before and after, too. Out of scope: switching to gunicorn
or multiple processes, and any change to retrieval or the model call.
