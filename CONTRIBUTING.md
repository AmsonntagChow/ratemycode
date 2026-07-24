# Contributing

RateMyCode is one focused skill: evidence-grounded product judgment for built software. New reviewer modes may fit; unrelated skills do not. Please fork the repository for a different job-to-be-done rather than adding another top-level skill directory.

## Evidence required for a pull request

Include all of the following:

1. At least three exact user prompts that exercise the change, including a near miss when discovery behavior changes.
2. Before-and-after transcripts or concise behavioral observations.
3. The expected assertions and which assertions fail before the change.
4. Whether `description` changed and why the trigger boundary remains safe.
5. A same-rubric comparison when scoring or verdict behavior changes.

A prose-only restatement of a prompt is not enough. Prefer a small reference, deterministic helper, or evaluation case that changes measurable behavior.

## Local checks

```bash
python3 scripts/sync_codex_plugin.py --check
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
```

Keep scripts on the Python standard library unless a dependency is essential and explicitly reviewed. Scripts must be independent of the current working directory, deterministic for the same logical input, and emit actionable errors with non-zero exit codes.

## Pull-request hygiene

- Keep safety vetoes and non-negotiable rules in the main `SKILL.md`.
- Keep reference links one level deep and valid on case-sensitive filesystems.
- Run `python3 scripts/sync_codex_plugin.py` after changing the canonical skill, then keep `.claude-plugin/plugin.json` and `plugins/ratemycode/.codex-plugin/plugin.json` on the same semantic version whenever published contents change.
- Update trigger and execution evals separately.
- Never add telemetry or undisclosed network access.
- Never weaken a verified veto merely to raise a score.
- Sign off commits with `git commit -s` to certify the Developer Certificate of Origin.

Maintainers may close proposals that expand scope, lack reproducible evidence, or create a new permission or supply-chain risk without a clear benefit.
