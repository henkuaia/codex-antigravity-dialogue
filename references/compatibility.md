# Compatibility and Evidence

Skill revision: **0.1.1-dev** (unreleased `main` branch). The published GitHub Release **v0.1.0** is a historical snapshot from `2026-11-16` and does **not** include these updates. Neither revision claims universal Desktop compatibility.

| Component | Scope | Evidence |
| --- | --- | --- |
| Same-project Codex Desktop to Antigravity Desktop | Existing chat in the same verified project | A locally modified bridge `2.3.2` produced a correlated reply on Windows on `2026-11-16`. |
| Same-project Antigravity Desktop to Codex Desktop | Verified sender, existing Codex chat, native relay | The same installation delivered a reverse message on `2026-11-16`. |
| Cross-project Codex Desktop to Antigravity Desktop | Patched local bridge `2.3.2` (`desktop.crossProjectDiscovery=true`, `receiptProjectFields=true`, `outbound.targetCwdRequired=true`) | Verified live on Windows on `2026-11-17`: cross-project forward send and correlated `reply_received` succeeded. Does not prove an independently initiated live cross-project reverse send. |
| Cross-project Antigravity Desktop to Codex Desktop | Patched local bridge `2.3.2` (`codexScope="all-saved-local-projects"`, `targetCwdRequired=true`) | Covered by separate, unpublished local bridge runtime tests (`isSameProject` ordering, explicit target `cwd` on `read_agent_task` and `send_to_agent_task`, dual-path receipts `senderCwd`/`targetCwd`). Independently initiated live reverse dispatch across projects has not been verified. |
| Stock upstream bridge `2.3.2` or other versions | Inspect installed schemas and status flags first | Same-project only unless capability flags are present; not established by local patched runs. |
| Other operating systems and Desktop builds | Instructions may apply | No live integration verification recorded; exact app builds from the historical tests were not retained. |
| Offline diagnostic helper (`scripts/doctor.py`) | Python 3.11+, standard library | Executed offline fixture unit tests in `tests/`; no network or dispatch. |
| Agent behavior under these instructions | 11 evaluation scenarios in `evals/scenarios.json` | Evaluation input prompts and expected/forbidden criteria only; not an executed model evaluation or proof of instruction following. |

Local bridge runtime patches (covering project metadata compatibility, Codex-only account routing, entry paths, relay registration, and cross-project `(conversationId, title, projectCwd)` tuple routing) live in a separate local runtime working copy. They have **not** been published upstream and are **not** bundled with this skill. Do not imply that installing or updating this skill upgrades the bridge runtime, and never bypass native verification to imitate those patches.

## Cross-Project Capability Evidence vs. Version String

Both stock and locally patched bridge installations may report `"version": "2.3.2"`. Never enable cross-project routing based on the version number or the mere presence of a `cwd` parameter alone. Enable cross-project workflow **only** when status output provides explicit capability evidence:

- **Codex (`antigravity_bridge_status`)**: `desktop.crossProjectDiscovery=true`, `desktop.receiptProjectFields=true`, and `outbound.targetCwdRequired=true` (with `outbound.scope="existing-desktop-conversations-across-local-projects"`).
- **Antigravity (`agent_bridge_status`)**: `codexScope="all-saved-local-projects"` and `targetCwdRequired=true` (with `read_agent_task` accepting `cwd`).

When these flags are absent, treat the bridge as same-project only (`targetCwd` must equal `sender.cwd`).

## Required Tool Capabilities

Discover live schemas before each workflow; server names may be surfaced with host-specific namespace prefixes.

| Sending host | Required operations |
| --- | --- |
| Codex | `antigravity_bridge_status()`; `list_antigravity_conversations(surface="desktop")`; `send_to_antigravity_conversation(surface, conversationId, cwd, requestId, prompt)`; `read_antigravity_delivery(surface, requestId)` |
| Antigravity | `agent_bridge_status()`; `list_agent_tasks(target="codex")`; `send_to_agent_task(target, conversationId, cwd, requestId, prompt)`; `read_agent_delivery(requestId)`; `read_agent_task(target, conversationId, cwd)` (pass `cwd=<discovered target projectCwd>` whenever the live schema or `targetCwdRequired=true` supports/requires it) |
| Codex reverse-route companion | `native_relay_status()` reports runtime and native dispatch readiness; it is not itself a message test. |

Do not pass `surface` to a status tool whose schema has no arguments. The outbound `conversationId` field identifies the destination Codex thread; do not rename the parameter to `threadId` without an installed schema change. On cross-project-capable runtimes, always pass the discovered target `projectCwd` as `cwd` (never `sender.cwd`) for both `send_to_agent_task` and `read_agent_task(target="codex", ...)`.

## Integration Acceptance

After installing on a new machine, first inspect status (including cross-project capability flags) and select the exact authorized recipient tuple `(conversationId, title, targetCwd)`. A live integration test additionally requires permission to send its test messages. Verify a unique forward echo and, for two-way testing, an actual reverse message. Stop on ambiguity, a busy destination, or missing native permissions.

Re-run affected checks after bridge or host changes. Record only the necessary version, capability flags, and result in the current chat; never publish local identities, user paths, fingerprints, configuration dumps, or real conversation payloads.
