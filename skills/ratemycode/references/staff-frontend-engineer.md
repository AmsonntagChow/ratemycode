# Staff Frontend engineer review

Review the shipped client experience as a Staff Frontend engineer: correct, inclusive, resilient, measurable, and safe across the product's supported browsers and devices. Judge observable contracts and user consequences, not framework fashion or personal taste.

## Questions the artifact must answer

- Do critical journeys survive clean load, hard refresh, deep links, back/forward navigation, session expiry, resource failure, and offline/online transitions?
- Are URL, local, cached, and server state reconciled predictably under cancellation, retry, optimistic updates, duplicate actions, multi-tab use, and out-of-order responses?
- Can critical tasks be completed with keyboard, screen reader, zoom/reflow, touch, and reduced motion, with correct semantics, focus, announcements, contrast, and error association?
- Is loading, responsiveness, and visual stability acceptable on representative devices and networks, based on a reproducible trace or product metric rather than intuition?
- Do supported browsers, viewport sizes, orientation changes, pointer types, virtual keyboards, safe areas, long content, and localized text preserve every critical control?
- Does text hold together as set at every supported width: no last line stranded with a single word or character, no punctuation pushed to a line start, a readable measure and leading, and line-breaking correct for every script the product ships?
- Do components, tokens, variants, states, and interaction conventions form one coherent system, with justified exceptions rather than parallel one-offs?
- Are forms, pending states, validation, duplicate submission, partial failure, destructive actions, and retry or undo paths safe and recoverable?
- Is interaction feedback immediate and predictable? Is motion purposeful for its frequency, interruptible, performant, input-aware, and respectful of reduced motion?
- Are authorization and sensitive-data boundaries enforced beyond the client? Can untrusted content reach unsafe rendering, navigation, storage, messaging, upload, or telemetry paths?
- Can production failures, degraded performance, and regressions be detected, reproduced, attributed to a release, tested deterministically, and rolled back safely?

## Frontend review matrix

Rate only dimensions that apply to the product and target. For numeric scoring, use these weights and the anchors in `references/numeric-scoring.md`:

| Dimension | Weight |
|---|---:|
| Browser and runtime correctness | 13 |
| State and data flow | 11 |
| Accessibility and inclusive input | 12 |
| Performance and perceived responsiveness | 10 |
| Responsive and cross-browser behavior | 5 |
| Design-system consistency | 4 |
| Typography and text setting | 5 |
| Forms, errors, and recovery | 9 |
| Interaction and motion craft | 4 |
| Client security and privacy boundaries | 9 |
| Testability | 7 |
| Observability | 5 |
| Change safety | 6 |

For every scored finding, name the exact journey, environment, browser or device when relevant, state and data preconditions, expected versus actual behavior, user consequence, evidence locator, confidence, and a falsifiable acceptance check. Prefer a real-browser reproduction, accessibility tree, network capture, runtime trace, or product metric. Static code may explain an observed failure but is not automatically runtime proof.

Use representative targets from the product's declared support contract. If that contract is absent, record the matrix as an unknown and test a minimal risk-based sample without pretending it is complete. Automated accessibility scans, one desktop browser, a fast developer laptop, or a synthetic performance score never prove the whole dimension.

Typography is judged as set text, not as taste. The defect is script-independent: a paragraph whose last line
carries a single word, or a heading broken into a long line and a stub. Latin and CJK differ only in what counts as
stranded — one word in Latin, one or two characters in CJK, where a single character is a complete morpheme — and in
the extra rules each script brings, such as the CJK convention that punctuation must not open a line.

Check whether the page uses the remedies that are now standard practice rather than hand-tuned line breaks:
`text-wrap: balance` on headings and other short blocks, `text-wrap: pretty` on body copy, a non-breaking space
binding the final two words where the algorithm cannot reach, and a measure held near 45–75 characters. Their absence
is not itself a finding; a stranded line at a supported width is.

Measure in a real browser at real widths, and beware two traps that produce false results. A paragraph that sets
correctly at one viewport can strand a word at another, so a single width proves nothing. And an inline element with
a different font size — `code`, `sub`, a smaller badge — produces a line box whose top differs from the surrounding
text on the same visual line; grouping rendered rectangles by exact position will report a phantom last line
containing only that element. Cluster line positions with a tolerance near the line height before judging.

Do not file font preference, exact leading values, a hyphenated compound breaking at its hyphen, or a house style the
product never declared.

To measure it rather than eyeball it, walk the text nodes of each block, take a rectangle per character, group those
rectangles into lines with a tolerance, and read the last group:

```js
// last-line content of one block, tolerant of smaller inline elements
const lh = parseFloat(getComputedStyle(el).lineHeight) || 24;
const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
const chars = [];
for (let n; (n = walker.nextNode()); )
  for (let i = 0; i < n.length; i++) {
    const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1);
    const b = r.getBoundingClientRect();
    if (b.width > 0) chars.push({ c: n.data[i], y: Math.round(b.bottom) });
  }
const rows = [...new Set(chars.map(c => c.y))].sort((a, b) => a - b)
  .reduce((g, y) => (g.length && y - g.at(-1).at(-1) <= lh * 0.6 ? g.at(-1).push(y) : g.push([y]), g), []);
const last = new Set(rows.at(-1));
const text = chars.filter(c => last.has(c.y)).map(c => c.c).join('').trim();
```

Score `text` by units, not by width: words for Latin, characters for CJK. A last line whose ratio to the block width
looks small is not automatically stranded — fifteen characters of code on a wide measure is fine. Repeat across the
product's supported widths; the same block can set correctly at one and strand at another.

## Judgment boundaries

Use the finding, severity, decision, and target-scoped veto protocol in `references/review-contract.md`. A core journey that is unusable for a required input mode or supported browser may be a release blocker by consequence, but only when verified and in scope. A missing preferred library, code style, component taste, or alternate architecture is not a finding.

Treat visual and motion craft as product quality only when it changes comprehension, responsiveness, accessibility, consistency, trust, or maintainability. Do not require animation merely because a surface is static. For frequent actions, responsiveness beats spectacle. Test gestures on a real touch device when they matter, gate hover behavior to hover-capable pointers, respect reduced-motion preferences, avoid broad transitions that hide unintended property changes, and prefer interruptible motion that does not delay repeated input.

Do not claim Core Web Vitals, accessibility, cross-browser support, or mobile readiness without direct evidence. Do not prescribe React, Vue, a state library, a design system, or an animation library unless the artifact's own contract makes it relevant.

## Expected deliverable

In addition to the shared verdict, include:

- strongest frontend engineering decision and why it is appropriate
- most expensive user-facing defect or hidden browser-state assumption
- one component, token, state, or interaction convention to preserve
- one change that most improves future frontend iteration speed

Keep unscored polish suggestions separate from release findings.
