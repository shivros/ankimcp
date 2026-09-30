# Tasks: AnkiMCP v2 Embedded Rust Core

## P0 — repository architecture specification

- [x] T0.1: Verify COD-509 authority, the COD-513 v6 reviewed handoff, the round-3/3 Hydra/AnkiMCP seam, COD-510/COD-525 dependency state, and the COD-545 residual acceptance boundary before editing the repository.
- [x] T0.2: Write `proposal.md` with the seven fixed owner rulings, scope boundary, dependency order, and no-runtime/no-release constraints.
- [x] T0.3: Write `design.md` against the current Python source and delivered Hydra runtime, including lifecycle, legacy compatibility, permission, packaging, and host/transport ownership.
- [x] T0.4: Write this `tasks.md` with shippable vertical phases and named owner gates; keep implementation phases unchecked.
- [x] T0.5: Write `specs/ankimcp-v2/spec.md` with normative requirements and deterministic scenarios for all seven rulings and five motivating defects.
- [x] T0.6: Run structural OpenSpec checks, `git diff --check`, the locked Python quality gates, and a docs-only scope audit. Record any unavailable tool honestly.

**P0 outcome:** a reviewed, actionable architecture contract. The addon source, dependencies, generated artifacts, packaging, and runtime remain unchanged.

## P1 — legacy compatibility and baseline characterization

- [ ] T1.1: Capture the current fifteen-tool inventory, direct JSON-RPC behavior, SSE session behavior, initialize/ping/resources/logging behavior, errors, repr-compatible values, and current installation/manifest behavior in deterministic fixtures.
- [ ] T1.2: Characterize permission behavior on every current read/write/delete/model path; document mismatches without silently broadening or narrowing access.
- [ ] T1.3: Correct the manifest author to `Shiv` or `shivros` and refresh stale installation guidance only in a separately scoped implementation ticket.
- [ ] T1.4: Reproduce the template qfmt/afmt observation against a real isolated Anki profile, or record a no-reproduction result with the missing evidence.
- [ ] T1.5: Do not begin P1 implementation until COD-509's spec is reviewed/merged and its child ticket has explicit ownership and acceptance scope.

## P2 — first bundled-native tracer bullet

- [ ] T2.1: Resolve COD-545's upstream acceptance disposition and obtain separate owner authorization for an immutable Hydra dependency containing the required runtime.
- [ ] T2.2: Record the supported Anki/OS/CPU/libc matrix, `abi3` baseline, native build versions, archive limits, and rollback artifact policy.
- [ ] T2.3: Add the Rust workspace, `ankimcp-core`, `ankimcp-addon`, PyO3 loader, generated operation contract, and one `list_decks` vertical slice.
- [ ] T2.4: Keep the legacy routes alive and prove old-client parity plus canonical MCP-over-HTTP discover/list/call through an installed addon archive.
- [ ] T2.5: Run native/platform packaging and real Anki lifecycle evidence on every advertised target. A Linux build alone is not sufficient.

## P3 — remaining operations, vertical slices

- [ ] T3.1: Migrate read operations in small slices; each slice owns generated CLI/HTTP/MCP artifacts, bridge behavior, permission checks, real Anki data, and legacy parity.
- [ ] T3.2: Migrate mutation operations in small slices; preserve partial/unknown outcomes and supported Anki APIs.
- [ ] T3.3: Remove an old Python adapter only after the replacement passes the complete surface and packaged-addon matrix.

## P4 — paginated search

- [ ] T4.1: Add `search_notes_page` with explicit live consistency, bounded limit, permission-first totals, deterministic ordering, and profile-bound opaque cursors.
- [ ] T4.2: Prove traversal of 0, 1, 50, 51, and 114 permitted notes without skips/duplicates, plus malformed/stale/cross-profile cursor rejection and no denied-count leak.
- [ ] T4.3: Preserve the original `search_notes` behavior for existing clients.

## P5 — bounded batch mutations

- [ ] T5.1: Add `create_notes_batch` and `update_notes_batch` with a maximum of 100 ordered items and explicit per-item outcomes.
- [ ] T5.2: Test invalid-middle, denied, not-attempted, close/disconnect, dispatched-unknown, and 114-note workflows. Do not claim atomicity or exactly-once execution.
- [ ] T5.3: Ensure CLI and canonical transports do not automatically retry unknown mutations; document reconciliation.

## P6 — template persistence

- [ ] T6.1: Reproduce the owner-observed note-type/template case on real Anki with HTML, escaping, cloze, and multiple templates.
- [ ] T6.2: Add structured template read-back if required by the reproduced contract and verify exact values after collection reopen.
- [ ] T6.3: Record no-reproduction or unsupported-version results instead of inventing a direct-database fix.

## P7 — sync lifecycle

- [ ] T7.1: Obtain owner/security approval for the supported Anki sync API, login/configuration authority, interactive states, and destructive-sync policy.
- [ ] T7.2: Add profile-scoped `sync`/`get_sync_status` with accepted/running/succeeded/failed/needs-user-action and unknown-after-restart states.
- [ ] T7.3: Test controlled real-Anki completion plus fake-client failures; never transport credentials, auto-login, kill/restart, or retry silently.

## P8 — separate CLI and retirement

- [ ] T8.1: Build the thin generated HTTP CLI as a separate artifact; it must never open collections, spawn Anki, or bundle addon/native files.
- [ ] T8.2: Exercise CLI reads and isolated-profile mutations against the packaged addon, including meaningful exit status and JSON errors.
- [ ] T8.3: Obtain explicit owner authorization and evidence before removing legacy adapters/routes. Retain rollback until the compatibility exit criteria are met.

## Cross-phase gates

- [ ] G1: COD-513/owner review has dispositioned the architecture and all owner-only gates relevant to the phase.
- [ ] G2: COD-545's Hydra residual acceptance is closed or explicitly accepted by the owner before AnkiMCP depends on the runtime.
- [ ] G3: `api/operations.yaml` remains the sole operation source; generated artifacts are written twice, byte-identical, and current.
- [ ] G4: Anki/Qt access remains on the supported main-thread bridge; no direct collection DB writes or spawned production sidecar appears.
- [ ] G5: Full repository, packaging, real-Anki, legacy-parity, and advertised-platform evidence is recorded for the selected phase.

## P0 verification commands

Run in the authorized isolated worktree, with outputs recorded in the Linear completion handoff:

```bash
# Structural checks (openspec CLI may be unavailable on the hosted runner)
python3 /opt/data/tmp/validate_ankimcp_v2_spec.py

git diff --check

git diff --name-only

# Hosted locked Python equivalents
/opt/data/tools/ankimcp-venv/bin/black --check src/ tests/
/opt/data/tools/ankimcp-venv/bin/ruff check src/ tests/
/opt/data/tools/ankimcp-venv/bin/pyright --pythonpath /opt/data/tools/ankimcp-venv/bin/python src/
/opt/data/tools/ankimcp-venv/bin/python -m pytest tests/
UV_PYTHON_INSTALL_DIR=/opt/data/tools/python UV_CACHE_DIR=/opt/data/tmp/uv-cache TMPDIR=/opt/data/tmp \
  uv build --out-dir /opt/data/tmp/ankimcp-COD-509-dist
```

The validator is a run-local helper, not a committed product file. Future runtime phases have additional Cargo/native/Anki/package gates listed above; they are not P0 acceptance evidence.
