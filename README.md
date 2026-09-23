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

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
