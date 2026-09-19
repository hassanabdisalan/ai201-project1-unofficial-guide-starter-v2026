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

---

# Week 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     week 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     week — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

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
