# Design: AnkiMCP v2 Embedded Rust Core

## Responsibility and composition

AnkiMCP owns the safe in-process bridge between Anki/Qt and an agent-facing addon service. It owns addon lifecycle, profile boundaries, permission policy, legacy compatibility, and collection operations. It does not own a generic MCP transport or a second operation registry. Hydra owns the generic projection and MCP-over-HTTP transport; AnkiMCP supplies the declared operation contract and one consumer-owned dispatcher.

Composition is intentionally explicit:

- **Input:** generated operation calls, legacy JSON-RPC requests, addon configuration, Anki profile lifecycle events, and Anki-supported collection APIs.
- **Output:** structured canonical results/errors, legacy-compatible responses, health/lifecycle status, and a separate thin HTTP CLI client path.
- **Side effects:** only the Anki main-thread bridge may touch the collection; packaging assembles prebuilt native modules; the host owns listener binding and shutdown.
- **Durable state:** Anki's collection remains authoritative. The addon may retain bounded in-memory request/job/profile-generation state but must not create a competing collection database or durable mutation log.
- **Upstream contract:** Hydra's reviewed stateless MCP Streamable HTTP runtime, current `ServerConfig::new(...)`/`router(config, dispatch)` seam, and generated explicit parameter-location metadata.
- **Downstream consumers:** existing JSON-RPC/SSE clients, a modern MCP-over-HTTP client, and the separately distributed HTTP CLI.

## Current baseline and evidence boundary

The current source is `shivros/ankimcp` main `d2554b2b8188cd1f46fdde92d2ec392876d04ec4`:

- `src/ankimcp/__init__.py` registers profile hooks, constructs `AnkiInterface(mw.col, config)`, starts an in-process `SimpleHTTPServer`, and stops it on profile close. Its old separate-process wording is stale and is not an architecture requirement.
- `simple_http_server.py` owns the legacy `GET /health`, `GET /sse`, `POST /messages`, and `POST /mcp` routes plus initialize/ping/tools/resources/logging behavior. It currently returns JSON-RPC errors through HTTP 200 on the direct route and exposes SSE session state.
- `tools.py` declares the current fifteen tools and serializes successful values through Python string formatting. This is a compatibility obligation, not a contract to preserve as the canonical v2 representation.
- `anki_interface.py` calls Anki APIs directly, limits `find_notes` to 50 by default, and constructs/saves note templates through the Anki model API. The observed template-loss incident still needs a real Anki persistence/reopen reproduction; this design does not assert a specific root cause.
- `permissions.py` and `config.json` define layered global/deck/tag/note-type policy, but enforcement is not uniform across all current read and model paths. The migration must characterize the existing behavior before moving policy and must not claim broader protection without an owner-reviewed security requirement.
- `package_for_ankiweb.py` archives source/native files but does not yet build a platform matrix. `pyproject.toml` is the current Python package configuration, not evidence that the future native build is complete.

These observations define the starting point. They are not claims that v2 behavior already exists.

## Module boundaries

### `ankimcp-core`

A Rust crate with no Anki, Qt, Python GIL, transport, or collection-file I/O dependency. It owns:

- typed operation inputs and JSON-valued results;
- structured domain errors and value-free public diagnostics;
- permission evaluation primitives only after the policy contract is approved;
- batch outcome types (`applied`, `rejected`, `not_attempted`, and dispatched-but-unknown);
- pagination/cursor validation for the additive search operation;
- sync job state values that distinguish accepted from completed and unknown.

The core must not guess parameter locations, own a socket, open an Anki collection, or encode legacy protocol framing.

### `ankimcp-addon`

The PyO3 `abi3` `cdylib` and embedded runtime. It owns the native loader boundary, listener composition, canonical Hydra runtime embedding, operation dispatch, and the bounded bridge to Anki. It may use Tokio/axum internally, but it never dereferences `mw.col` or borrowed Python/Qt objects from a Rust worker thread.

The host-facing dispatcher is one explicit path. It maps a generated operation to a bridge command, schedules that command on Anki's supported main-thread/collection mechanism, and converts the result into a structured value or safe error. It does not implement a second HTTP/MCP tool table.

### Python shim

`src/ankimcp/{__init__,native_loader,qt_bridge,compat_format}.py` is the minimal addon layer for configuration, profile hooks, main-thread scheduling, native loading, and legacy result formatting. Existing `tools.py`, `anki_interface.py`, and `simple_http_server.py` may remain during named migration phases only. They are retired one adapter at a time after the replacement passes the complete parity matrix.

### `ankimcp-codegen` and `api/operations.yaml`

`api/operations.yaml` is the only operation declaration. A build/developer-only wrapper invokes an owner-authorized immutable Hydra version's `write`/`check` commands. It never ships in the addon and is never invoked at runtime. All emitted artifacts from the selected generator version are committed when the implementation phase calls for them.

At the currently inspected Hydra source, the artifact inventory includes:

- `generated/cli.rs`;
- `generated/http.rs`;
- `generated/mcp.json`;
- `generated/ts-client/index.ts`.

The full selected-version inventory must be re-audited at the P2 dependency gate; a stale three-file list must not cause an artifact to be deleted or ignored. No TypeScript product, npm package, Node runtime, or extra public surface is implied by recording this inventory.

### `ankimcp-cli`

A separately distributed thin HTTP client. It uses generated explicit path/query/body metadata, connects to the running addon at `127.0.0.1:4473`, returns structured JSON, and reports meaningful exit status. It never opens a collection, starts Anki, spawns the addon, or falls back to local collection access.

## Request and lifecycle flow

1. Anki opens a profile and invokes the Python hook.
2. The shim loads a bundled compatible native module and creates a fresh profile-generation token.
3. The host composes the legacy routes and the canonical generated surfaces on one explicitly configured listener. It may mount the modern Hydra runtime at a distinct path such as `/mcp/v2`; Hydra does not choose the path or bind the listener.
4. A canonical operation enters the one Rust dispatcher. A legacy request enters the compatibility adapter, which translates only its known framing/format into the same operation dispatcher.
5. If collection access is needed, the dispatcher enqueues an explicit command for the Anki main-thread bridge. Workers do not hold Python/Qt references while awaiting the bridge.
6. The bridge checks the profile-generation token before execution. Results are converted to canonical JSON or the legacy compatibility formatter; diagnostics are value-free and do not expose secrets or collection content unnecessarily.
7. On profile close, the host marks the generation unavailable before queued work can run, stops accepting new work, shuts down the listener, cancels queued commands, and drops profile references without waiting on the UI thread for a worker that needs the same thread. An already-dispatched mutation reports an honest completed/unknown outcome; it is never falsely reported as rolled back.
8. A reopened profile receives a new generation. Old requests, cursors, and job identifiers cannot access the new profile.

Required lifecycle evidence includes repeated open/close, close during a mutation, listener bind conflict, timeout, stale generation rejection, queued cancellation, and no UI deadlock.

## Hydra seam and MCP transport

COD-510's reviewed transport specification is Hydra-owned. COD-525's delivered runtime exposes a reusable router with the following current interface:

- `ServerConfig::new(server_name, server_version, generated_tools, explicit_origin_policy)`;
- `hydra_mcp_http::router(config, async_dispatch) -> Result<Router, ConfigurationError>`;
- one host-owned async dispatcher with `Send + Sync + 'static` lifetime and `Result<Value, String>` output;
- explicit generated tool objects and explicit parameter locations;
- stateless POST-only MCP `2026-07-28` discover/list/call behavior, with no session affinity, legacy initialize handshake, GET stream, implicit CORS/PNA, or authentication policy.

The Anki host owns listener bind, mount path, shutdown, profile generation, permission policy, and main-thread scheduling. The runtime's current transport read cap is 8 MiB; the Anki v2 design proposes a 2 MiB new-API cap. These are different layers. The 2 MiB value remains a proposal until the owner/security gate records how it composes with the fixed Hydra behavior. It must never be silently applied to legacy routes.

`tools/list` must expose the exact generated tool objects in deterministic order. `tools/call` must route through the generated location table, not parameter-name or path-shape inference. If Hydra cannot express a needed generic capability, the request goes to hydra-PM; AnkiMCP does not fork or hand-write a generic transport.

COD-545 currently tracks missing negative transport/header/media/loopback evidence against COD-525. AnkiMCP may refer to the delivered API seam for architecture, but it must not call the full upstream acceptance matrix complete until that issue's disposition and evidence are recorded.

## Legacy compatibility

The listener retains the existing `POST /mcp`, `GET /sse`, `POST /messages?session_id=...`, `GET /health`, initialize/initialized, ping, resources/list/read, logging/setLevel, and current tool names/defaults. Existing clients keep their JSON-RPC IDs, missing/null distinctions, error envelopes, resource behavior, and repr-compatible success text. The canonical v2 endpoint returns JSON and uses the reviewed Hydra protocol; it is not an in-place protocol upgrade of the old route.

A compatibility adapter may translate legacy frames and format results, but it cannot hold a second operation registry, duplicate domain policy, or an independent business implementation. Removal of a legacy route requires:

1. captured fixtures for every currently supported tool and transport behavior;
2. parity replay after every vertical migration phase;
3. an explicit owner decision that supported clients no longer need the route;
4. a recorded removal condition and rollback plan.

The architecture proposes no legacy exception approval now. It records the exception boundary so a later review can decide it explicitly.

## Permission and collection safety

The current permission system is layered: global read/write/delete, protected decks, deck allow/deny lists, tag restrictions, and note-type constraints, with the most restrictive result winning. Rust v2 may centralize policy only after the existing behavior is characterized and the owner approves any security correction.

All reads and writes go through Anki's supported APIs. Direct SQLite/protobuf collection manipulation is prohibited. Permission filtering occurs before totals and pagination slicing so denied-note counts do not leak. Batch operations evaluate each item independently and return ordered receipts; a partially dispatched or disconnected mutation is `unknown`, not an automatic retry or false rollback. Sync uses Anki-managed configuration and credentials and never transports credentials through the generated API.

## Additive defect repairs

### Search pagination

Add `search_notes_page(query, limit, cursor?)` with a maximum limit of 200 and a structured `{notes,total,has_more,next_cursor,consistency:"live"}` result. The cursor binds query, profile generation, and format and is validated as untrusted input. It is live, not snapshot-consistent. The original `search_notes` operation remains unchanged.

### Batch mutations

Add ordered `create_notes_batch` and `update_notes_batch` with at most 100 items. Each item has a caller correlation ID and an outcome of applied, rejected, not-attempted, or dispatched-but-unknown. The contract is partial-success, not atomic or exactly-once; clients do not automatically retry mutations.

### Template persistence

Use the supported Anki model APIs, reproduce the owner-observed qfmt/afmt failure on a real isolated profile, reopen the collection, and distinguish dropped input, API persistence, client naming, and unsupported-version causes. A no-reproduction result is recorded honestly; no SQLite workaround is accepted.

### Sync

Add `sync` and `get_sync_status` only after the owner approves the exact supported Anki API and user-interaction authority. Status values distinguish accepted, running, succeeded, failed, and needs-user-action. A restart invalidates in-memory job state to unknown. No hidden retry, kill/restart workaround, login flow, or destructive full-sync choice is permitted.

## Distribution and rollback

The approved target matrix must be established from actual Anki embedded-Python and OS evidence before selecting an `abi3` baseline. The proposed matrix is Windows x86_64, macOS x86_64/arm64, and Linux x86_64; it is not a support claim. Free-threaded Python, libc variants, unsupported architectures, and archive size limits require explicit evidence.

CI builds native libraries per approved target, records hashes and a target manifest, places only compatible prebuilt modules under the addon source tree, and creates one AnkiWeb archive. The loader never compiles or downloads code. A missing/incompatible module leaves Anki usable and reports an actionable local error. Rollback restores a prior compatible addon archive on restart; it never downgrades the Anki collection format.

## Owner-only gates

The following five decisions remain outside this spec's authority and must be recorded before the relevant implementation/release phase:

1. supported Anki/OS/CPU/libc matrix and the `abi3` baseline;
2. permission/security policy corrections and exposure of currently under-enforced paths;
3. the exact supported Anki sync API, user-interaction authority, and credential boundary;
4. disposition and removal condition for legacy compatibility adapters/routes;
5. immutable Hydra dependency selection, AnkiMCP release/publication, and consumer-repin authority.

COD-545's Hydra acceptance evidence is an upstream prerequisite but is not one of these AnkiMCP owner decisions. No phase may silently convert any gate into an implementation assumption.

## Phase architecture

- **P0 — specification:** land these four OpenSpec files. No runtime or Cargo change.
- **P1 — compatibility baseline:** capture all fifteen tools, both legacy transports, resources, errors, manifest author, and installation docs; add only characterization/metadata corrections.
- **P2 — first tracer bullet:** after upstream acceptance and immutable dependency authorization, ship bundled-native `list_decks` through PyO3, the bridge, generated surfaces, and real packaged-addon evidence while retaining every legacy operation.
- **P3a–P3n — vertical operations:** migrate read families and mutation families one at a time; each phase owns public-boundary, real-Anki, legacy-parity, and packaging evidence.
- **P4 — paginated search:** deliver `search_notes_page` and complete 0/1/50/51/114-note traversal and permission-exclusion evidence.
- **P5 — batches:** deliver bounded partial-outcome batch mutations, disconnect/close behavior, and the 114-note workflow without exactly-once claims.
- **P6 — templates:** deliver evidence-backed template persistence/read-back across reopen or record a no-reproduction result.
- **P7 — sync:** deliver profile-scoped sync status only after the sync authority gate and controlled real-Anki evidence.
- **P8 — CLI and retirement:** ship the separate HTTP CLI, finish parity, then remove obsolete adapters only with explicit owner approval.

Every runtime phase must be separately ticketed and dependency-linked. The spec does not bulk-create or promote those tickets.
