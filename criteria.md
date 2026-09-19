# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in week 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next week costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:** `campus_life` posts are short (average 317 characters)
and each one is built around a single fact, so a chunk either is the answer
or clearly isn't — there's little of the "answer split across two chunks"
problem a longer, sectioned corpus would have. I still leave room for one
miss: two of my five questions (the shuttle timing and the CS 210 curve
question) retrieve a near-duplicate document as the #2 or #3 result — the
`_followup` and `_exams` sibling files repeat similar phrasing about
schedules and grading — so I want a target I can miss without it meaning the
pipeline is broken.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:** This is 5 of 5, not 4 of 5, because source-naming isn't
a retrieval outcome that can come back thin — it's a formatting step in
`generate.py` that runs on every answer the gate lets through, using
whichever chunks were retrieved regardless of how good they are. The only
way this fails is a code bug (the template drops the source line), not a
question being hard, so I hold it to a target the other two criteria don't
get.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:** I checked the raw distances before writing this target.
My five in-corpus questions land between 0.22 and 0.43 best-distance; the
five `OUT_OF_SCOPE` questions land between 0.82 and 0.93. That's a wide,
clean gap with nothing sitting near either edge, so the default 0.6 cutoff
should catch all five out-of-scope questions reliably. I still write 4 of 5
rather than 5 of 5 because I haven't run the eval itself yet — a
single-pass, deterministic check can still surprise me, and I'd rather leave
one slot of room than claim a perfect score before I've seen the run log.

---

## 4. Chunks read as complete thoughts, not fragments

For at least 4 of 5 chunks I sample by eye after chunking, the chunk starts
and ends on a full sentence — nothing is cut off mid-word or mid-clause at
either boundary.

**Why this target:** Reading `campus_life` in Milestone 1, I noticed several
posts (e.g. `course_biol_160.txt`) pack 3-4 separate facts — format,
assessment style, workload, one piece of advice — into a handful of short
paragraphs under 600 characters, well under the default 800-character
chunk size. That means the fixed-size fallback splitter mostly leaves these
posts whole by accident, not because it understands sentence boundaries. If
I move to a smaller or paragraph-aware split in Milestone 3, the real test
is whether the cut points land on paragraph breaks instead of arithmetic
ones. I set 4 of 5 rather than 5 of 5 because a `\n\n` in these posts isn't
guaranteed to mark a clean thought boundary — some replies run paragraphs
together — so I expect an occasional miss even from a strategy that's
working.

---

## 5. The cited source is the one that actually contains the fact

For at least 4 of my 5 test questions, the source named in the answer is the
document whose text contains the specific fact asked about — not a sibling
document about the same general topic that doesn't actually contain it.

**Why this target:** `campus_life` splits many topics across near-duplicate
sibling files — `course_cs_210.txt` / `course_cs_210_exams.txt` /
`course_cs_210_workload.txt`, or `housing_aldridge_hall.txt` /
`_laundry` / `_noise`. Criterion 2 only checks that *some* source gets named;
it would pass even if the system cited `course_cs_210.txt` for a question
about the exam curve, because that file is about the same course but
doesn't contain the answer. That's a more specific and more useful bar than
criterion 2, and one I expect this corpus to actually stress, since I saw
the CS 210 exams document and workload document rank close together in
Milestone 1's retrieval check. I kept it at 4 of 5 rather than 5 of 5 for
the same reason — sibling-document confusion is exactly the failure mode I
expect to hit at least once.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     WEEK 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in week 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
