---
name: isic-m-kotoba-slice
description: Porting isic actor .cljk to .kotoba, gating with amu check.
metadata: {"hermes": {"version": "0.1.0", "author": "cloud-itonami", "source": "https://github.com/cloud-itonami/app-itonami-cloud-itonami-isic-7310/tree/5b0c39170d4f2ee91c67ecb35a673766a17d624d", "compatibility": {"hermes": "*", "desktop": "*"}}}
---

# ISIC-M .kotoba slice workflow (measured 2026-09-20, actor 7310 phase.cljk)

## Gate command (the only acceptance authority)

    orgs/kotoba-lang/amu/bin/amu check <slices>/<code>/advertising/SLICE.kotoba \
      --source-path <slices>/<code> \
      --source-path orgs/kotoba-lang/kotoba-lang/lang/compat

  Cross-module `(:require [advertising.phase :as phase])` is resolved as the
  PATH `advertising/phase.kotoba` under each --source-path root (measured
  2026-09-23, operation.kotoba): a flat `<slices>/<code>/*.kotoba` layout
  fails with `:kotoba/project-link-failed` "required module <ns> is missing
  from the explicit source paths" (EXIT 65) even though the file parses.
  Keep slice files in `<slices>/<code>/<ns-first-segment>/` and point
  --source-path at the code root.

- A single-file `amu check FILE` refuses any `(:require ...)`: `:kotoba.error/namespace-require-needs-project`. Always use the project route (source-path list). (The current Amu selfhost `bin/amu` has NO `--jvm-free` flag — that belonged to the retired hosted entry (`docs/retired/legacy-public-entry-20261023` in kotoba-lang/amu). JVM-freeness is a build property of the selfhost artifact now; the receipts are process trace + compiler generation + artifact hash, not a flag.)
- `kotoba.lang.coll` / `kotoba.lang.text` resolve from `kotoba-lang/kotoba-lang/lang/compat` (guest twins, cross-root rule picks the .kotoba).
- Run with stdout+stderr redirected to files and read the files: the cron terminal often swallows stdout, and amu writes the CLI-error EDN to stderr. exit 0 = `:kotoba.check/v1` green; nonzero = read the `:message`/`:span` — amu reports ONE error per run, fix and re-run.

## Profile-6 grammar rules (each one was a measured refusal)

1. Params are name/type PAIRS, result type after the params vector: `(defn f [x :i64] :bool ...)`. Unannotated params default to i64 — annotate every keyword/set param or the type errors surface somewhere unrelated.
2. Keyword equality AND keyword case-scrutinee are refused ("expected i64, got keyword"). Pass booleans/ints instead; keep keyword `=` on the caller side.
3. `contains?` does not reach typed sets — use `(typed-set-contains [:set :keyword] s x)` (core, unqualified; `set/typed-set-contains` is refused as a non-exported import).
4. A conditional may NOT return a keyword-keyed map literal: every map literal is its own singleton type, so `cond`-of-maps fails "if branches must have the same value type" even when all branches are literals. Split the function into one :i64/:bool function per field and annotate the result type (`:i64` annotation makes literal/var branches unify).
5. Map literal values must be i64 (nil refused: "write (option-none) or leave the key out"); keyword values refused too ("expected i64, got keyword").
6. Top-level defs must be constants: a def whose value calls a function (even one of the same module) is refused; write literal sets/maps, and keep the computed form as an exported defn (e.g. `auto-set`).
7. `(:export [...])` names must be declared FUNCTIONS of the module — a def constant export is refused (":export-names-constant"); make zero-parameter defns returning the set.
8. `case` is fine over i64 scrutinees with mixed literal/expr branches of one type; `case` over keywords is refused (rule 2).
9. kotoba.lang.coll's twin exports ONLY set-union/set-intersection/set-difference/subset?/superset?, two-argument, template param elem=:keyword.

## Slice-shape guidance

- One component per slice (q9-migration v3: `:decision-only-slices-allowed false`) — port ALL top-level names, private ones included (rename `defn-` to public defn).
- Where the .cljk computed a top-level from functions, write the literal value AND keep the computing function exported; document that the invariant now lives in the function.
- Keep a RUN-NOTE.txt in workspace/slices/<code>/ with the gate cmd, result, and each refusal->fix pair; it is the next run's evidence.

## Misleading-gate refusal (measured 2026-09-21, buy.kotoba)

- Unescaped double quotes INSIDE an ns docstring close the string early; the ns form then parses malformed and amu reports `:error :project-link` / `:code :kotoba/project-link-failed` with the message "only one :export, one :capabilities, one :schemas, one :params and alias-only :require clauses are admitted" — NOT the obvious string error. Exit 65. Fix: no inner `"` in docstrings (backticks are fine, phase.kotoba style); on this message, re-read the ns form as the reader would before suspecting duplicate clauses.
- `amu check --source-path DIR` project-links EVERY .kotoba file under DIR: stray probe files are parsed too (harmless if they are well-formed, but they bloat the run). Delete probes once their refusal is recorded in RUN-NOTE.

## Cross-module gate calls (measured 2026-09-23, operation.kotoba)

- `subset-reject "expected bool, got i64"` at the call line (not the callee) means one ARGUMENT of a cross-module call crossed a type boundary: the phase gate's `governor-disposition` slot is :i64 and its `governor-hold?` slot is :bool; the cljk's `(case disposition ...)` base must not be passed into the i64 slot as a bool, nor an i64 literal into the bool slot. Pass the base disposition computed by an `if` (i64) and the raw bool flag, respectively; when the caller's cond already answered the hard? case, pass literal `false` to the reason call.
- A minimal zero-arg or literal-arg probe file in the same `advertising/` dir confirms whether the refusal is the call or the namespace link; delete the probe once its refusal is recorded.

## Cron environment gotchas

- write_file/patch hit a freshness guard: read the FULL file (all pages) right before overwriting; patch fails otherwise and write_file refuses (stale_write_blocked). When patch keeps failing, prefer a fresh full read + write_file, or sed with `|` delimiters (macOS: `sed -i '' -e ...`).
- execute_code and `node -e`/`-c` flags are blocked in cron; plain `node bin/amu ...` and sed are fine. `$?` in echo triggers the security scan — redirect to files instead.
