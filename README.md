# Self-Healing Technical Documentation

A GitHub Action that watches a codebase, detects when code changes make the
documentation inaccurate, pinpoints the specific stale sections, and either opens
a PR with corrected docs (high-confidence, simple changes) or flags the
discrepancies for human review (complex or low-confidence ones).

## Why this exists

This lives inside CI/CD, not a Streamlit demo. It solves a pain every engineer
has personally felt — perpetually stale docs — and exercises the full AI stack:
parsing, linking, retrieval, LLM verification, LLM repair, and production
deployment as an installable Action.

## Architecture

```
src/mapping/code_parser.py    AST parse -> semantic code chunks (functions/classes)
                               with stable identifiers and signatures
src/mapping/doc_parser.py     markdown -> sections with nested heading paths + the
                               code symbols each section references
src/mapping/link_graph.py     links doc sections to code chunks by symbol match
src/detection/diff_parser.py  parse git diff + filter for MEANINGFUL changes
                               (signatures/endpoints/config, not comments/whitespace)
src/detection/staleness.py    LLM verification: given old+new code and a doc section,
                               is the doc now inaccurate? (filters false positives)
src/repair/repair_engine.py   targeted correction + second-pass validation +
                               confidence-based mode (auto-fix vs. draft-for-review)
src/pipeline.py               wires mapping+detection: diff -> suspect doc sections
action/action.yml             Docker-based GitHub Action definition
.github/workflows/doc-check.yml  runs the Action on PRs that touch *.py
```

## Design decisions

- **Two-stage staleness detection: cheap filter, then LLM.** The diff parser first
  discards comment-only/whitespace/non-behavioral changes and finds which doc
  sections even *reference* the changed code (via the link graph). Only those
  suspects go to the (expensive) LLM staleness check — so the Action doesn't burn
  tokens verifying docs that couldn't possibly be affected.
- **The link graph is symbol-based first.** A doc section that mentions
  `connect_db` links to the `connect_db` code chunk by name — deterministic, cheap,
  and debuggable, with embeddings as an optional enhancement rather than the
  foundation.
- **Confidence + change-complexity decides the mode.** Simple, high-confidence
  changes (renamed parameter, changed default) auto-fix and open a PR; complex or
  low-confidence changes become drafts with TODO markers for human review. A
  correction that fails the second-pass validation is *never* auto-applied,
  regardless of confidence.
- **Corrections are targeted.** The repair prompt rewrites only the stale parts and
  is explicitly told to preserve the rest — the tool shouldn't reflow a whole doc
  because one default value changed.
- **Everything except the LLM calls is pure and tested.** AST parsing, markdown
  sectioning, link-graph construction, diff parsing, and the meaningful-change
  filter are all deterministic and covered offline — no API key needed for the suite.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env      # OPENAI_API_KEY
```

## As a GitHub Action

`.github/workflows/doc-check.yml` runs on any PR touching `*.py`: it parses the
diff, finds doc sections referencing the changed code, LLM-verifies staleness,
and posts a summary comment (`3 verified accurate, 1 auto-fixed, 2 flagged`).

## Tests

```bash
pytest tests/ -v
```

14 tests covering AST extraction (functions/classes, signatures, stable IDs,
syntax-error handling), markdown parsing (nested headings, code-reference
extraction, backticks), link-graph construction, diff parsing + the meaningful-
change filter (signature change is meaningful, comment change isn't), and the
end-to-end suspect-section pipeline — all offline, no API key required.

## Status

Phases 1-3 complete (code+doc mapping, change detection with meaningful-change
filtering, repair engine with validation + confidence-based modes) plus the
Action packaging. Phase 4's live PR-creation via PyGithub and Phase 5's real-repo
accuracy measurement are scaffolded (action.yml + workflow) but the PR-open call
against a live GitHub API is not exercised in the offline suite.
