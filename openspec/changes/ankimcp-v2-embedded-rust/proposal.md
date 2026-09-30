# Proposal: AnkiMCP v2 Embedded Rust Core

## Status and authority

This change is the repository-delivery artifact for COD-509. It transcribes the PM-authored COD-513 v6 architecture handoff into OpenSpec; it does not implement the migration.

The fixed owner rulings below are binding. They were recorded by Shiv on 2026-09-16 and must not be redesigned by this change. The Hydra/AnkiMCP transport seam was accepted at COD-513 negotiation round 3/3. Hydra COD-510 delivered the transport specification, and Hydra COD-525 delivered the reusable runtime at `303ba7af54b2c54752c59c1e3a60828290f79e75`; COD-545 remains the Hydra-owned residual acceptance follow-up. Drafting this P0 architecture is allowed under COD-509's existing owner allowance. Runtime phases remain separately gated.

No release, immutable Hydra dependency selection, consumer repin, deployment, permission-policy decision, supported-platform claim, or live Anki validation is granted by this document.

## Problem

The current AnkiMCP repository is a Python `src/`-layout Anki addon. It starts an in-process HTTP/SSE service from Anki profile hooks and exposes fifteen tools through a legacy JSON-RPC surface. The current implementation has product and safety gaps that are difficult to repair incrementally without an explicit architecture boundary:

- `search_notes` slices results to 50 without a total or continuation cursor.
- There are no bounded batch create/update operations.
- Canonical responses are Python `str`/repr-like values, requiring clients to use `ast.literal_eval`-style fallbacks.
- There is no supported sync operation with an honest accepted/running/completed/unknown lifecycle.
- An owner-observed `create_note_type` template-persistence failure needs a real Anki persistence/reopen reproduction; the architecture must not claim a root cause from mocks alone.
- The addon must retain existing localhost clients while gaining a modern generated contract and an embedded implementation that cannot access Anki/Qt objects from arbitrary Rust worker threads.

The solution must be shippable in vertical tracer bullets, not a single rewrite that leaves a long-lived compatibility gap.

## Fixed owner rulings

1. **One-step distribution:** users install one AnkiWeb addon code and restart Anki. There are no user-facing Rust toolchain steps, install-time builds, runtime downloads, marketplaces, or auto-updaters.
2. **Embedded Rust core:** the production implementation is a PyO3 `abi3` `cdylib` bundled inside the addon with a minimal Python shim. A spawned sidecar is not the distribution mechanism. A sidecar/dev binary is allowed only as a developer convenience for the same crate.
3. **Build-time Hydra projection:** `api/operations.yaml` is the single operation source of truth. Hydra generates CLI, HTTP, and MCP artifacts at build time. Hydra is never a user-facing runtime dependency.
4. **MCP over HTTP:** the canonical new MCP surface is the reusable stateless Streamable HTTP runtime, not stdio. The server is embedded in Anki and cannot be client-spawned. Generic transport gaps belong in Hydra.
5. **Separate CLI:** the CLI is a thin HTTP client of the running addon at `127.0.0.1:4473`, distributed separately through cargo-install/release binaries and never bundled in the `.ankiaddon`.
6. **Additive wire compatibility:** existing JSON-RPC clients on localhost:4473 continue to work. New tools, parameters, and routes are additive; legacy defaults, envelopes, IDs, repr-compatible text, resources, and error behavior are not silently replaced.
7. **Manifest hygiene:** the addon manifest author is exactly `Shiv` or `shivros`; the rejected historical deadname is not copied into new artifacts.

## Proposal

Replace the current transport/domain implementation incrementally with an embedded Rust core while Anki remains the only collection owner. The addon archive contains the Python bootstrap and prebuilt native modules for every explicitly approved target. A minimal Python layer owns addon configuration, Anki profile hooks, Qt/main-thread scheduling, native loading, and legacy formatting. Rust owns validated operation inputs, deterministic domain results, structured errors, and one dispatcher. Hydra projects the same declared operations into HTTP, MCP, and the separately distributed CLI.

Each migration phase ends in a usable addon. Legacy routes stay available until parity evidence and explicit owner authorization support their removal. The architecture deliberately separates generic Hydra transport from Anki-specific lifecycle and permission policy.

## Scope

This change defines:

- the repository boundaries and Rust/Python module responsibilities;
- the legacy and canonical public-surface relationship;
- the PyO3, Anki/Qt, profile-generation, shutdown, and failure contracts;
- the Hydra build-time projection boundary and current runtime integration seam;
- vertical migration phases, prerequisites, acceptance evidence, and owner-only gates;
- normative requirements for the seven rulings and five observed product defects.

This change creates only four OpenSpec documents. It does not add Rust, Python, generated artifacts, dependencies, CI workflows, native binaries, Anki package outputs, releases, or deployment configuration.

## Out of scope

- migration to the unrelated `ankimcp.ai` fork;
- a user-facing spawned sidecar, runtime package download, marketplace, or updater;
- a new handwritten canonical HTTP/MCP operation registry;
- direct SQLite/protobuf collection writes;
- changing current legacy protocol behavior before compatibility fixtures and owner disposition exist;
- permission broadening, sync credentials/login, or a destructive full-sync policy;
- selecting or pinning a Hydra release, publishing AnkiMCP, deploying an addon, or repinning a consumer;
- claiming native platform support, live Anki/Qt evidence, or COD-545 acceptance from this spec.

## Dependency and authority boundary

The dependency order is:

1. COD-510's reviewed Hydra transport specification — landed;
2. COD-525's reusable Hydra runtime and Notes public-boundary evidence — merged, with residual negative-matrix evidence tracked by COD-545;
3. an owner-authorized immutable Hydra dependency selection containing the required runtime;
4. AnkiMCP implementation slices, each with their own ticket, review, packaging, real-Anki evidence, and gates.

COD-509 may draft and land this P0 OpenSpec while the later runtime gates are unresolved. No P2+ implementation ticket is implicitly promoted by this proposal, and the existing Hydra-owned COD-545 follow-up must not be duplicated in AnkiMCP.

## P0 acceptance

The proposal is complete when:

- `proposal.md`, `design.md`, `tasks.md`, and `specs/ankimcp-v2/spec.md` exist at the named paths;
- the documents contain traceability for all seven rulings, all five motivating defects, the dependency sequence, and the owner-only gates;
- the current Python addon, Hydra runtime interface, legacy obligations, and known evidence limits are distinguished from future design;
- the diff contains no runtime, generated, dependency, packaging, release, deployment, or consumer-repin change;
- structural validation, `git diff --check`, and the repository's existing locked Python quality gates are run and reported.
