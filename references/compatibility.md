# Compatibility and Evidence

Skill release: **0.1.0**. This is the first packaged release, not a claim of universal Desktop compatibility.

| Component | Scope | Evidence |
| --- | --- | --- |
| Codex Desktop to Antigravity Desktop | Existing chat in the same verified project | A locally modified bridge 2.3.2 produced a correlated reply on Windows on 2026-11-16. |
| Antigravity Desktop to Codex Desktop | Verified sender, existing Codex chat, native relay | The same installation delivered a reverse message on 2026-11-16. |
| Stock upstream bridge 2.3.2 or other versions | Inspect installed schemas first | Not established by that local success. |
| Other operating systems and Desktop builds | Instructions may apply | No live integration verification recorded; exact app builds from the historical test were not retained. |
| Offline diagnostic helper | Python 3.11+, standard library | Automated fixture tests; no network or dispatch. |
| Agent behavior under these instructions | Evaluation scenarios supplied | Scenarios are not a completed model evaluation or proof of instruction following. |

Historical local fixes covered project metadata compatibility, Codex-only account routing, entry paths, and relay registration. They are not bundled here. Do not promise that installing this skill reproduces those changes, and never bypass native verification to imitate them.

## Required Tool Capabilities

Discover live schemas before each workflow; server names may be surfaced with host-specific namespace prefixes.

| Sending host | Required operations |
| --- | --- |
| Codex | `antigravity_bridge_status()`; `list_antigravity_conversations(surface="desktop")`; `send_to_antigravity_conversation(surface, conversationId, cwd, requestId, prompt)`; `read_antigravity_delivery(surface, requestId)` |
| Antigravity | `agent_bridge_status()`; `list_agent_tasks(target="codex")`; `send_to_agent_task(target, conversationId, cwd, requestId, prompt)`; `read_agent_delivery(requestId)`; `read_agent_task(target, conversationId)` |
| Codex reverse-route companion | `native_relay_status()` reports runtime and native dispatch readiness; it is not itself a message test. |

Do not pass `surface` to a status tool whose schema has no arguments. The outbound `conversationId` field identifies the destination Codex thread; do not rename the parameter to `threadId` without an installed schema change.

## Integration Acceptance

After installing on a new machine, first inspect status and select the exact authorized project/recipient. A live integration test additionally requires permission to send its test messages. Verify a unique forward echo and, for two-way testing, an actual reverse message. Stop on ambiguity, a busy destination, or missing native permissions.

Re-run affected checks after bridge or host changes. Record only the necessary version and result in the current chat; never publish local identities, fingerprints, configuration dumps, or real conversation payloads.
