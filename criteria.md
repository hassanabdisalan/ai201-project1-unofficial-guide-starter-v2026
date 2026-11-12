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


---

# Capstone criteria

Written before any capstone results exist. Criteria 1–4 are about the
extension (the structured log and run path in `serve.py`); criterion 5 is about
the original system, to catch a regression. Drafted by Claude following the
Criteria Self-Check procedure at my request; I reviewed and own the targets.

**Test conditions for every criterion.** Server started as documented in
`RUNNING.md` for Windows: `AI201_CACHE=0`, `python serve.py`, fresh log file
per trial (`AI201_LOG_PATH`), index built. "Warm" means after one discarded
request. "The in-corpus set" is the 5 `QUESTIONS` in `questions.py`; "the
out-of-scope set" is the 5 `OUT_OF_SCOPE` questions. One trial = one full pass
of the criterion's procedure; three trials each.

## 1. Every request leaves a complete log record

In a single trial, send 20 requests: 10 in-corpus (the set twice), 5
out-of-scope, 3 empty-question, 2 whose model call fails (server started with
an invalid API key for those two). The log file gains **exactly 20 lines, all
valid JSON, and every line contains the keys `ts`, `request_id`, `question`,
`answer`, `status`, `latency_ms`, `error`.** Target: 20 of 20 lines, in each
of 3 trials.

**Why this target:** a request that fails is exactly the one I'll want to
diagnose later, and a missing line looks the same as "never happened". So the
target is all of them, not a rate; 19 of 20 would mean some class of request is
invisible. The mix covers every code path in `serve.py::ask` that returns.

## 2. A failed model call returns a readable error and is logged

With the server started with an invalid `GEMINI_API_KEY`, send each of the 5
in-corpus questions. For each, the HTTP response is **status 500 with a JSON
body whose `error` field is non-empty, returned in under 30 seconds**, and the
log gains a line with `status` 500 and a non-empty `error`. Target: 5 of 5, in
each of 3 trials.

**Why this target:** the Milestone 3 spot check passed once (11 s), but there
is no timeout in `serve.py` and `generate.py` only retries on 429, so I don't
know the worst case. 30 s is the point where a user has given up and a proxy in
front of it would be cutting the connection. All 5, because a failure path that
works 4 times in 5 is one a user will eventually hit.

## 3. Answered requests come back within 10 seconds

Send the in-corpus set twice, one request at a time, after one discarded warm-up
request (10 timed requests per trial). Latency is the client-measured time from
sending the request to receiving the full response, and the same request's
logged `latency_ms` must not be more than 250 ms below it. Target: **at least 9
of 10 under 10 000 ms**, in each of 3 trials.

**Why this target:** my Milestone 3 sample ranged 1.4 s–12.3 s (median 4.1 s,
mean 5.5 s), with the model call dominating. 10 s is about as long as a student
will wait on a chat-style answer; allowing 1 in 10 over reflects that the
hosted model's time varies on near-identical prompts, which I can't fix. A
stricter 5 s target would miss on roughly half of requests and tell me about
Gemini, not about my service. Cold-start (first request) is excluded on
purpose; it measured 13–20 s and is documented in `RUNNING.md`.

## 4. Token and model-call counts are attributed to the right request, even under concurrency

Send 15 requests (the in-corpus set three times) plus the out-of-scope set
(5), 20 in all, from 3 concurrent clients. In the log: **every answered
request has `model_calls` equal to 1 and both `prompt_tokens` and
`output_tokens` greater than 0, and every refused request has `model_calls`
0, `prompt_tokens` 0 and `output_tokens` 0.** Target: 20 of 20 lines
correct, in each of 3 trials.

**Why this target:** the cost number in the README is built from these fields,
so a wrong attribution makes the cost number wrong without anything looking
broken. The counts are computed in `serve.py` as differences of process-wide
counters in `generate.py`, which is only correct when requests don't overlap;
`python serve.py` is multithreaded, so I expect this one to be at risk and I'd
be disappointed to ship a cost number that's silently wrong under a second
simultaneous user. All 20 because one misattributed line already corrupts the
sum.

## 5. The extension didn't break the relevance gate

Send the out-of-scope set (5 questions) once per trial. **Every response has
`refused: true`, and its log line has `model_calls` 0.** Target: 5 of 5, in each
of 3 trials.

**Why this target:** the gate was calibrated in Week 1 and re-checked after the
hybrid-search and gate-decoupling changes (all 5 refused, best distances
0.787–0.923 against a 0.6 threshold). It is the one safeguard against an
invented answer to a question the corpus can't support, so a single leak is a
failure, not noise. It's the deliberately safe criterion: the point is to
catch the extension regressing the original system, not to find new problems.
