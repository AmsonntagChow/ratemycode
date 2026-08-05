#!/usr/bin/env python3
"""Generate the README diagrams as tall SVGs that survive a phone.

The originals were 1600x900. GitHub scales a README image to the column, so on a
390px screen that is 19% and the body text lands at four to eight pixels —
measured on the live page, not guessed. There is no CSS fix: GitHub strips style
attributes, and a table wrapper does not help because max-width:100% caps the
image before it can overflow anything.

So the canvas changes instead. At 560 wide the diagram renders near its natural
size in a desktop README column and at roughly 58% on a phone, which puts 24px
body text at about 14px where it is actually read. The content was always a
vertical list of numbered steps; the old landscape canvas was flattening it.
"""
import pathlib
from xml.sax.saxutils import escape

W_TALL = 460
W_WIDE = 1000
PAPER, INK, GRAPHITE, RULE, ACCENT = "#FFFFFF", "#1A1A1C", "#6B6B70", "#D8D6D1", "#C4500F"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

DIAGRAMS = {
    "audit-pipeline": {
        "eyebrow": "THE REVIEW · 01",
        "title": "Find it. Try it. Tell the truth.",
        "subtitle": "Five steps from “here is my app” to “this is safe to ship.”",
        "steps": [
            ("Find one app", ["One clear product.", "Can’t find it? Ask. Stop."]),
            ("Pick the review", ["Who should judge it?", "How strict?"]),
            ("Try real tasks", ["Use it like a customer.", "Try a failure too."]),
            ("Sort the evidence", ["What did we prove?", "What is still unknown?"]),
            ("Set the safe line", ["List every problem.", "Can it ship safely?"]),
        ],
        "band_title": "WHAT EACH STEP LEAVES BEHIND",
        "band": [
            ("TARGET", "One exact release"),
            ("SETTINGS", "Role + depth"),
            ("EDGE CASES", "Retry · race · access"),
            ("EVIDENCE", "Proven · inferred · unknown"),
            ("VERDICT", "Requested ↔ safe"),
        ],
        "closing": "Test the product first. Read the code to explain why. Untested stays unknown.",
    },
    "decision-engine": {
        "eyebrow": "THE DECISION · 02",
        "title": "The first serious problem decides.",
        "subtitle": "Ask these questions in order. The first “yes” wins.",
        "steps": [
            ("Big danger?", ["Someone could lose money,", "data, or access."], "YES → BLOCKED"),
            ("Must-pass failed?", ["An important test", "did not work."], "YES → NOT READY"),
            ("Proof missing?", ["Something important", "was not checked."], "YES → NEED PROOF"),
            ("Small gaps only?", ["The important things", "are safe."], "YES → WITH CONDITIONS"),
            ("All clear?", ["No bigger problem", "came first."], "YES → READY"),
        ],
        "band_title": "HOW TO READ THE RESULT",
        "band": [
            ("FIRST MATCH", "Stop at the first yes"),
            ("FAIL ≠ UNKNOWN", "Broken and untested differ"),
            ("SAFE LIMIT", "May sit below your request"),
            ("SCORE AFTER GATES", "Can lower; never rescue"),
        ],
        "closing": "A high score cannot erase a blocker, a failed must-pass check, or missing proof.",
    },
    "fix-retest-loop": {
        "eyebrow": "THE FIX LOOP · 03",
        "title": "Changed does not mean fixed.",
        "subtitle": "A fresh reviewer has to prove the change really works.",
        "steps": [
            ("Save the audit", ["Keep the old truth", "before any edit."]),
            ("Fix one kind", ["Find the same cause.", "Change one small batch."]),
            ("A fresh reviewer tests", ["same task · new damage · same bug", "The fixer cannot sign it off."]),
            ("Save the result", ["Write what passed", "and what did not."]),
        ],
        "band_title": "WHAT MAKES THE LOOP AUDITABLE",
        "band": [
            ("HISTORY", "Old snapshot stays"),
            ("SCOPE", "One cause · serial batch"),
            ("INDEPENDENCE", "Three checks · same release"),
            ("RESULT", "Pass · partial · blocked · risk"),
        ],
        "closing": "Still open → next batch. Independently verified → close. "
                   "Accepted risk is named, never called fixed.",
    },
}


def text(x, y, s, size, fill=INK, weight="400", family=SANS, anchor="start", spacing=None):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}>{escape(s)}</text>')


def wrap(s, per_line):
    """Character-count wrapping. Crude, but the generated SVG is measured in a
    real renderer afterwards, so a bad guess here shows up as an overflow."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > per_line:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def build(spec):
    pad, y = 32, 0
    body = []

    y += 52
    body.append(text(pad, y, spec["eyebrow"], 20, ACCENT, "600", MONO, spacing="0.12em"))
    y += 46
    for line in wrap(spec["title"], 23):
        body.append(text(pad, y, line, 34, INK, "600"))
        y += 40
    y -= 6
    for line in wrap(spec["subtitle"], 40):
        body.append(text(pad, y, line, 22, GRAPHITE))
        y += 30
    y -= 4
    body.append(f'<line x1="{pad}" y1="{y}" x2="{W_TALL-pad}" y2="{y}" stroke="{RULE}" stroke-width="1"/>')

    for n, step in enumerate(spec["steps"], 1):
        title, details = step[0], step[1]
        verdict = step[2] if len(step) > 2 else None
        y += 40
        body.append(f'<circle cx="{pad+16}" cy="{y-8}" r="17" fill="none" stroke="{ACCENT}" stroke-width="2"/>')
        body.append(text(pad + 16, y, str(n), 21, ACCENT, "600", MONO, anchor="middle"))
        body.append(text(pad + 48, y, title, 26, INK, "600"))
        for d in details:
            y += 28
            body.append(text(pad + 48, y, d, 22, GRAPHITE))
        if verdict:
            y += 30
            body.append(text(pad + 48, y, verdict, 20, ACCENT, "600", MONO, spacing="0.04em"))
        y += 22

    y += 16
    band_top = y
    body.append(text(pad, y + 34, spec["band_title"], 18, GRAPHITE, "600", MONO, spacing="0.12em"))
    y += 34
    # Label and value are stacked, not left/right: at this width a right-aligned
    # value runs straight into a long label, which the canvas-overflow check
    # cannot see because neither one leaves the canvas.
    for label, value in spec["band"]:
        y += 32
        body.append(text(pad, y, label, 18, ACCENT, "600", MONO, spacing="0.08em"))
        y += 26
        body.append(text(pad, y, value, 21, INK))
    y += 28
    band = (f'<rect x="{pad-16}" y="{band_top}" width="{W_TALL-2*pad+32}" height="{y-band_top}" '
            f'fill="#F6F4F1" stroke="{RULE}" stroke-width="1" rx="4"/>')

    y += 44
    for line in wrap(spec["closing"], 46):
        body.append(text(pad, y, line, 21, GRAPHITE))
        y += 28
    height = y + 20

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_TALL}" height="{height}" '
            f'viewBox="0 0 {W_TALL} {height}" role="img">\n'
            f'  <rect width="{W_TALL}" height="{height}" fill="{PAPER}"/>\n  '
            + band + "\n  " + "\n  ".join(body) + "\n</svg>\n")

def build_wide(spec):
    """Same content, laid out across. Generated from the identical spec so the two
    cannot drift — the reason a hand-kept second copy was not an option."""
    pad = 44
    steps = spec["steps"]
    col_w = (W_WIDE - 2 * pad) // len(steps)
    body = []

    body.append(text(pad, 62, spec["eyebrow"], 19, ACCENT, "600", MONO, spacing="0.12em"))
    body.append(text(pad, 108, spec["title"], 38, INK, "600"))
    body.append(text(pad, 142, spec["subtitle"], 21, GRAPHITE))
    body.append(f'<line x1="{pad}" y1="{170}" x2="{W_WIDE-pad}" y2="{170}" stroke="{RULE}" stroke-width="1"/>')

    for n, step in enumerate(steps):
        x = pad + n * col_w
        title, details = step[0], step[1]
        verdict = step[2] if len(step) > 2 else None
        body.append(f'<circle cx="{x+16}" cy="{212}" r="16" fill="none" stroke="{ACCENT}" stroke-width="2"/>')
        body.append(text(x + 16, 219, str(n + 1), 19, ACCENT, "600", MONO, anchor="middle"))
        yy = 262
        for line in wrap(title, 16):
            body.append(text(x, yy, line, 22, INK, "600"))
            yy += 26
        yy += 4
        for d in details:
            for line in wrap(d, 21):
                body.append(text(x, yy, line, 18, GRAPHITE))
                yy += 24
        if verdict:
            # A long verdict runs into the next column; wrap it inside its own.
            vy = yy + 12
            for line in wrap(verdict, 15):
                body.append(text(x, vy, line, 16, ACCENT, "600", MONO, spacing="0.02em"))
                vy += 20
        if n < len(steps) - 1:
            body.append(f'<line x1="{x+col_w-18}" y1="{206}" x2="{x+col_w-8}" y2="{212}" '
                        f'stroke="{RULE}" stroke-width="2"/>')

    band_top = 410
    body.append(text(pad, band_top + 34, spec["band_title"], 17, GRAPHITE, "600", MONO, spacing="0.12em"))
    bw = (W_WIDE - 2 * pad) // len(spec["band"])
    for i, (label, value) in enumerate(spec["band"]):
        x = pad + i * bw
        body.append(text(x, band_top + 72, label, 16, ACCENT, "600", MONO, spacing="0.08em"))
        yy = band_top + 98
        for line in wrap(value, 24):
            body.append(text(x, yy, line, 18, INK))
            yy += 22
    band = (f'<rect x="{pad-20}" y="{band_top}" width="{W_WIDE-2*pad+40}" height="130" '
            f'fill="#F6F4F1" stroke="{RULE}" stroke-width="1" rx="4"/>')

    yy = band_top + 176
    for line in wrap(spec["closing"], 96):
        body.append(text(pad, yy, line, 19, GRAPHITE))
        yy += 26
    H = yy + 12

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_WIDE}" height="{H}" '
            f'viewBox="0 0 {W_WIDE} {H}" role="img">\n'
            f'  <rect width="{W_WIDE}" height="{H}" fill="{PAPER}"/>\n  '
            + band + "\n  " + "\n  ".join(body) + "\n</svg>\n")


if __name__ == "__main__":
    out = pathlib.Path(__file__).resolve().parents[1] / "docs" / "diagrams"
    for name, spec in DIAGRAMS.items():
        tall = build(spec)
        (out / f"{name}-tall.svg").write_text(tall, encoding="utf-8")
        wide_svg = build_wide(spec)
        (out / f"{name}.svg").write_text(wide_svg, encoding="utf-8")
        h = tall.split('height="', 2)[1].split('"')[0]
        print(f"{name}.svg  {W_WIDE}x560 (宽)   {name}-tall.svg  {W_TALL}x{h} (窄)")
