# AnkiMCP v2 Embedded Rust Specification

## ADDED Requirements

### Requirement: The addon is a one-step embedded native distribution

AnkiMCP SHALL be distributed as one AnkiWeb addon archive containing the Python bootstrap and prebuilt compatible native modules for every explicitly advertised target. A user SHALL be able to install by entering the addon code and restarting Anki, without a Rust toolchain, install-time compilation, runtime download, spawned production sidecar, marketplace, or updater. The manifest author SHALL be exactly `Shiv` or `shivros`.

#### Scenario: Offline one-step installation

- **WHEN** a user installs the assembled addon archive and restarts Anki with no Rust toolchain and no network access
- **THEN** the bundled compatible native module loads, Anki remains usable, `/health` responds, and a real client can invoke the generated `list_decks` operation
- **AND** a missing or incompatible native module produces an actionable local addon error without downloading code or spawning an unsigned executable

#### Scenario: Advertised target matrix is honest

- **WHEN** a target is listed as supported
- **THEN** the exact Anki/Python/OS/CPU/libc evidence, native artifact hash, archive-size check, and packaged-addon acceptance run for that target are recorded
- **AND** a Linux build or `abi3` label alone is not treated as evidence for other targets or free-threaded Python

#### Scenario: Manifest hygiene

- **WHEN** the addon manifest is packaged
- **THEN** its author is `Shiv` or `shivros`
- **AND** the rejected historical author value is absent from the manifest and generated reports

### Requirement: Rust collection access is embedded and profile-safe

The production Rust core SHALL be a PyO3 `abi3` `cdylib` bundled in the addon. A minimal Python shim SHALL own addon configuration, native loading, Anki profile hooks, and Qt/main-thread scheduling. Rust worker threads SHALL NOT dereference `mw.col`, borrowed Python objects, or Qt objects. All collection access SHALL use supported Anki APIs through one bounded main-thread bridge.

#### Scenario: Profile generation prevents cross-profile access

- **WHEN** a request is queued for profile generation A and the profile closes before the request executes
- **THEN** the request is rejected or reported as an honest unknown/finished mutation outcome before it touches the collection
- **AND** reopening profile B creates a new generation that cannot be accessed by the old request, cursor, or job identifier

#### Scenario: Shutdown does not deadlock the UI

- **WHEN** a profile closes while requests are queued or a collection operation is in flight
- **THEN** the listener stops accepting new work, queued work is canceled before execution, profile references are dropped, and the UI thread is not blocked waiting for a worker that requires the UI thread
- **AND** an already-dispatched mutation is not falsely reported as rolled back

#### Scenario: Collection writes use supported APIs

- **WHEN** a runtime phase creates, updates, deletes, syncs, or persists a note type
- **THEN** it calls the supported Anki/Qt API through the bridge
- **AND** it never writes the collection SQLite database or protobuf files directly

### Requirement: One declared operation contract projects every canonical surface

`api/operations.yaml` SHALL be the sole source of operation names, explicit parameter locations, schemas, descriptions, and surface membership. An owner-authorized immutable Hydra version SHALL generate the CLI, HTTP, and MCP artifacts at build time. The addon SHALL not run Hydra or any generator at runtime, and it SHALL not maintain a parallel operation registry or infer locations from parameter names/path shapes.

The full emitted artifact set for the selected Hydra version SHALL be enumerated and committed when a runtime phase requires committed generation. The currently inspected generator emits `generated/cli.rs`, `generated/http.rs`, `generated/mcp.json`, and `generated/ts-client/index.ts`; this inventory must be re-audited at dependency selection rather than assumed stable.

#### Scenario: Deterministic generation

- **WHEN** the authorized generator writes the artifacts twice from the same operation declaration and immutable dependency set
- **THEN** every emitted artifact is byte-identical across both writes
- **AND** the generator check reports the committed artifacts current

#### Scenario: Explicit location routing

- **WHEN** a canonical CLI or MCP call supplies a path, query, or JSON-body argument
- **THEN** the adapter uses the generated location metadata to construct the operation input
- **AND** no parameter name, identifier, or path shape is used to guess a location

#### Scenario: Projection gap

- **WHEN** the AnkiMCP contract needs a generic projection or transport feature that Hydra cannot express
- **THEN** the gap is filed to hydra-PM with a versioned contract request
- **AND** AnkiMCP does not add a bespoke generic generator or handwritten canonical transport

### Requirement: MCP-over-HTTP is additive to the legacy addon protocol

The new canonical MCP surface SHALL use Hydra's reusable stateless Streamable HTTP runtime and the reviewed `2026-07-28` contract. The host SHALL own the listener, explicit mount path, shutdown, profile generation, and permission policy. The runtime SHALL not be replaced by stdio, a client-spawned process, a session-affinity protocol, a GET stream, implicit CORS/PNA behavior, or an authentication policy invented by this spec.

The existing `POST /mcp`, `GET /sse`, `POST /messages?session_id=...`, `GET /health`, initialize/initialized, ping, resources, logging, and legacy tool behavior SHALL remain available until the compatibility exit criteria and explicit owner disposition are complete. A proposed canonical mount such as `/mcp/v2` is distinct from the legacy routes.

#### Scenario: Canonical MCP client uses the embedded host

- **WHEN** an independent MCP client sends a valid discover, list, or call request to the explicit canonical mount on the running addon
- **THEN** the request reaches the generated tool manifest and one consumer-owned dispatcher through Hydra's stateless HTTP runtime
- **AND** the addon does not spawn a child server, open an Anki collection in the CLI, or create a session-affinity requirement

#### Scenario: Legacy client remains compatible

- **WHEN** an existing client replays captured requests against the legacy JSON-RPC or SSE-session routes
- **THEN** tool names, defaults, IDs, missing/null distinctions, error envelopes, resources, and repr-compatible result text remain compatible
- **AND** adding canonical JSON results does not replace the legacy default representation

#### Scenario: Legacy route removal requires evidence

- **WHEN** a future change proposes removing or changing a legacy route
- **THEN** the change includes complete fixture parity, a documented removal condition, rollback behavior, and explicit owner authorization
- **AND** this architecture spec alone is not treated as that authorization

#### Scenario: Upstream runtime acceptance is not overstated

- **WHEN** AnkiMCP records its dependency on Hydra's MCP-over-HTTP runtime
- **THEN** it distinguishes COD-510's landed specification, COD-525's merged runtime, and COD-545's residual rejection/loopback evidence
- **AND** it does not call the complete upstream acceptance matrix closed until COD-545's disposition is recorded

### Requirement: Permission policy and diagnostics remain least-authority and secret-safe

The addon SHALL preserve the layered permission model: global read/write/delete, protected decks, deck allow/deny lists, tag restrictions, and note-type constraints, with the most restrictive decision winning. Permission filtering SHALL precede totals and page slicing. Canonical errors SHALL be structured and value-free; legacy text compatibility SHALL not expose secrets or raw collection/configuration contents. Any correction to currently under-enforced paths requires an owner-reviewed security contract and regression evidence.

#### Scenario: Permission filtering does not leak denied totals

- **WHEN** a paginated search includes notes excluded by the active permission policy
- **THEN** denied notes are removed before total calculation and page slicing
- **AND** the response does not reveal the count or identifiers of denied notes

#### Scenario: Permission failures are consistent across surfaces

- **WHEN** a read, write, delete, or note-type operation is denied
- **THEN** the canonical HTTP/MCP/CLI surfaces expose the same structured denial semantics
- **AND** the legacy adapter preserves its established error representation without bypassing the policy

#### Scenario: Diagnostics are safe

- **WHEN** a malformed request, configuration error, provider/Anki error, or sync failure is returned
- **THEN** the public diagnostic is bounded, code-authored, and secret-safe
- **AND** raw tokens, credentials, full collection contents, or unredacted configuration source are not copied into response text or logs

### Requirement: Additive search pagination is bounded and honest

AnkiMCP SHALL add a generated `search_notes_page(query, limit, cursor?)` operation without changing legacy `search_notes`. The new operation SHALL return `{notes,total,has_more,next_cursor,consistency:"live"}`, enforce a maximum limit of 200, order permitted matches deterministically, and bind the opaque cursor to its format, query, and profile generation. It SHALL not claim snapshot consistency.

#### Scenario: Quiescent 114-note traversal

- **WHEN** an isolated permitted profile contains 114 matching notes and a client follows `next_cursor` until `has_more` is false
- **THEN** every permitted note is returned exactly once in deterministic order
- **AND** the response reports the live consistency model and does not silently truncate at 50

#### Scenario: Search cursor is rejected safely

- **WHEN** a cursor is malformed, oversized, stale, cross-profile, or bound to a different query
- **THEN** the operation returns a structured restart-required error before returning future-only results
- **AND** no denied-note count is disclosed

#### Scenario: Legacy search remains unchanged

- **WHEN** an existing client calls `search_notes` with its current arguments
- **THEN** its established route, defaults, output shape, and compatibility representation remain unchanged

### Requirement: Batch mutations report partial and unknown outcomes

AnkiMCP SHALL add ordered `create_notes_batch` and `update_notes_batch` operations with a maximum of 100 items per request. Each item SHALL carry a caller correlation ID and return `applied`, `rejected`, `not_attempted`, or dispatched-but-`unknown` outcome as appropriate. The contract SHALL be partial-success, not atomic or exactly-once, and transports SHALL not automatically retry an unknown mutation.

#### Scenario: Ordered partial batch

- **WHEN** a bounded batch contains an invalid or denied item between valid items
- **THEN** each item reports its own outcome and the result preserves caller order
- **AND** a later valid item is not reported as applied if it was never dispatched

#### Scenario: Disconnect during mutation

- **WHEN** the client disconnects after a mutation was dispatched but before its result is known
- **THEN** the item is reported as unknown through the applicable reconciliation path
- **AND** the client is not told that the mutation was rolled back or safe to retry automatically

#### Scenario: 114-note migration uses bounded calls

- **WHEN** a client migrates 114 notes through the batch API
- **THEN** it uses bounded requests with ordered receipts and round-trips fields/tags through supported Anki APIs
- **AND** the contract makes no atomicity or exactly-once claim

### Requirement: Template persistence is proven against real Anki

The implementation SHALL use supported Anki model APIs for note-type/template creation. Before claiming a fix, it SHALL reproduce the owner-observed case against a real isolated Anki profile, including HTML, escaping, cloze, and multiple-template cases, save the model, reopen the collection, and compare exact qfmt/afmt and generated-card behavior. If the failure cannot be reproduced, the result SHALL say so rather than invent a database workaround.

#### Scenario: Template values survive reopen

- **WHEN** a canonical create-note-type call supplies explicit qfmt and afmt values and the profile is closed and reopened
- **THEN** the supported Anki read-back contains the exact values and generated cards use the expected templates
- **AND** no SQLite/protobuf file was modified directly

#### Scenario: Root cause is unknown

- **WHEN** the observed production failure cannot be reproduced on the authorized Anki/version/profile matrix
- **THEN** the acceptance record names the missing evidence or unsupported version
- **AND** no speculative template rewrite is shipped as a fix

### Requirement: Sync is an explicit profile-scoped lifecycle, not a hidden restart workaround

AnkiMCP SHALL not add `sync` or `get_sync_status` until the owner/security gate records the supported Anki API, credential boundary, user-interaction authority, and destructive-sync policy. Once authorized, sync SHALL expose accepted, running, succeeded, failed, and needs-user-action states with a profile-scoped job ID. A restart SHALL invalidate in-memory job state to unknown rather than report false success.

#### Scenario: Accepted is distinct from completed

- **WHEN** a client requests sync and Anki accepts the job
- **THEN** the response reports accepted/running with a job identifier
- **AND** it does not claim that synchronization has completed

#### Scenario: Restart invalidates job state

- **WHEN** Anki or the addon restarts before a sync result is durable in the supported Anki system
- **THEN** the old job is reported as unknown or requires user reconciliation
- **AND** the addon does not automatically log in, choose a destructive full-sync mode, kill/restart Anki, or retry silently

### Requirement: Every vertical phase is shippable and machine-verifiable

Each implementation phase SHALL be a separately scoped ticket with a generated-surface contract, real public-boundary evidence, real Anki/packaging evidence where applicable, legacy compatibility evidence, deterministic regeneration checks, and rollback notes. The phase SHALL stop at its named owner/dependency gates. The P0 specification phase SHALL change only the four OpenSpec documents.

#### Scenario: P0 docs-only scope

- **WHEN** the P0 OpenSpec change is reviewed
- **THEN** it contains the proposal, design, tasks, and normative spec with traceability for seven rulings and five defects
- **AND** the diff contains no Rust/Python runtime, Cargo/dependency, generated artifact, packaging, release, deployment, or Hydra source change

#### Scenario: Runtime gate is not inferred from green documentation checks

- **WHEN** structural OpenSpec checks and repository Python checks pass for P0
- **THEN** the completion record reports only docs/specification evidence
- **AND** it does not claim native support, real Anki/Qt behavior, Hydra release selection, deployment, consumer repin, or live production behavior

#### Scenario: Generated and packaged behavior is verified at the real boundary

- **WHEN** a later phase changes generated operations or native packaging
- **THEN** the phase runs two-write byte identity and generator freshness, uses the installed addon archive, exercises an independent canonical client and legacy fixtures, and records exact target/tool versions
- **AND** mocks alone are not accepted as completion evidence
