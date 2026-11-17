---
name: codex-antigravity-dialogue
license: MIT
description: Connect Codex Desktop with Google Antigravity (反重力) Desktop to check the bridge, exchange authorized messages, hand off tasks, or retrieve replies. Use for communication between these two apps, not general MCP setup or CLI workers.
---

# Codex-Antigravity Dialogue

Use the existing MCP bridge; this skill supplies instructions, not a server. Load only the relevant reference on demand (**Progressive Disclosure**):
- **[installation](references/installation.md)** — when bridge tools or the skill itself are missing or not loaded.
- **[diagnostics](references/diagnostics.md)** — when a status/send call returns a diagnostic error or when running the read-only local checker (`scripts/doctor.py`).
- **[handoffs](references/handoffs.md)** — before any authorized connection test, task handoff, or timeout continuation.
- **[compatibility](references/compatibility.md)** — when checking version scope, live tool schemas, or forward/reverse route capabilities.

## Choose the Requested Action

| User intent | Action |
| --- | --- |
| Check status, explain an error, or ask whether connected | **Stage 1 only (Read-only)**: Read status, discovery, and existing receipts only. Do not send a test or repair configuration. |
| Connect or explicitly test communication | **Stage 1 → 2 → 3 (Echo test)**: Lock preflight invariants, send one minimal echo marker to the identified idle recipient, and verify the correlated reply. No research work. |
| Ask the other agent to do a task | **Stage 1 → 2 → 3 (Task handoff)**: Lock preflight invariants, send the authorized scope once, and retrieve/correlate the result. Existing authorization remains valid for the same work and recipient. |
| Continue, check a reply, or recover after a timeout | **Stage 3 only (Recovery)**: Recover the original destination and `requestId` from the current chat; read that delivery/task before considering any new send. |

Creating, installing, or editing this skill does not authorize cross-agent messages. Resolve missing details from current context and live discovery; ask only if recipient or scope remains ambiguous.

## Three-Stage Execution Protocol (`Preflight → Dispatch → Correlate`)

### Stage 1: Preflight & Target Lock (Before Any Send)
Lock five invariants from live tool discovery before calling any send tool:
1. **Host & Route**: Codex Desktop uses `antigravity-bridge` (`surface="desktop"`); Antigravity Desktop uses `agent-bridge` (`target="codex"`). Codex's `codex-native-relay` companion supports the reverse route. Use only the `codex` target, never `claude`.
2. **Sender & Capability Verification**:
   - On Codex, call `antigravity_bridge_status()` without arguments (`desktop.available=true` proves Antigravity sidecar availability only, not reverse-route readiness; inspect `native_relay_status()` when reverse delivery matters).
   - On Antigravity, call `agent_bridge_status()` and require `sender.status="verified"`.
   - **Cross-Project Capability Evidence**: Enable cross-project Desktop routing **only** when status explicitly reports capability flags—on Codex: `desktop.crossProjectDiscovery=true`, `desktop.receiptProjectFields=true`, and `outbound.targetCwdRequired=true`; on Antigravity: `codexScope="all-saved-local-projects"` and `targetCwdRequired=true` (with `read_agent_task` accepting `cwd`). Never infer cross-project support from version `"2.3.2"` or the mere presence of a `cwd` parameter alone.
3. **Tuple Binding (`(conversationId, title, targetCwd)`)**:
   - Bind each discovered conversation as an indivisible `(conversationId, title, targetCwd)` tuple using its discovered `projectCwd` (or `cwd`).
   - On a cross-project-capable runtime, `targetCwd` may differ from `sender.cwd`; always pass `cwd=<discovered targetCwd>` (never `sender.cwd`) for target reads and sends. Respect the user's already-explicit target and scope authorization—do not force redundant reconfirmation merely because directories differ; ask only when the recipient or scope is genuinely ambiguous.
   - On a same-project-only runtime (capability flags absent), `targetCwd` must match `sender.cwd`; if `list_agent_tasks` fails with `BRIDGE_OPERATION_FAILED`, report `sender.cwd` and stop without spoofing paths.
4. **Exact Idle Recipient**: Discover an existing recipient by project, title, and ID (`isSameProject=true` rows appear first when cross-project discovery is active). Do not guess IDs, reuse old examples, or blindly select the first listed chat. Check whether the recipient is busy; never interrupt active research for a test or redirect work to an unrelated idle chat.
5. **Authorized Scope & Fresh `requestId`**: Generate one fresh UUID `requestId` per intentional message. Preserve native identity and approvals; never spoof a sender, bypass failed identity/account checks, use UI automation, open an old chat, create a disposable/executor chat, or substitute background CLI workers (`send_to_worker`) for Desktop conversations. Historical chats provide context, not authorization to resume their experiments.

### Stage 2: Single Idempotent Dispatch

#### From Codex Desktop (`Codex → Antigravity`)
1. Discover `antigravity_bridge_status`, `list_antigravity_conversations`, `send_to_antigravity_conversation`, and `read_antigravity_delivery`. Call the status tool without arguments; list with `surface="desktop"`. Missing tools are an installation/loading issue, not permission to substitute a CLI route.
2. Match the intended idle conversation (in `sender.cwd`, or across allowed local projects when `desktop.crossProjectDiscovery=true`) and lock its `(conversationId, title, targetCwd)` tuple.
3. For an authorized send, call `send_to_antigravity_conversation` once with `surface="desktop"`, discovered `conversationId`, `cwd=<discovered targetCwd>`, fresh UUID `requestId`, and `prompt`. Identify the author as `Codex` and use the compact handoff format in [handoffs](references/handoffs.md) (requesting `Reply-To: <requestId>` in the recipient's local reply).
4. Call `read_antigravity_delivery` with the same `requestId` and `surface="desktop"`. `pending` or `accepted` is not a reply; `reply_received` with a correlated response establishes the round trip (cross-project receipts record both `senderCwd` and `targetCwd`).

#### From Antigravity Desktop (`Antigravity → Codex`)
1. Call `agent_bridge_status` (require `sender.status="verified"` and inspect whether `codexScope="all-saved-local-projects"` and `targetCwdRequired=true`), then call `list_agent_tasks(target="codex")`.
2. Match the intended idle Codex chat and lock its `(conversationId, title, targetCwd)` tuple. When inspecting prior context for an authorized handoff via `read_agent_task`, pass `target="codex"`, `conversationId=<destination>`, and (when the schema or `targetCwdRequired=true` requires/supports it) `cwd=<discovered targetCwd>`.
3. For an authorized send, call `send_to_agent_task` once with `target="codex"`, `conversationId=<listed Codex threadId>`, `cwd=<discovered targetCwd>`, `requestId=<fresh UUID>`, and `prompt` (here `conversationId` identifies the destination Codex thread ID; check the live schema first).
4. Write agent-authored handoffs in English, identify `Antigravity` as author, preserve the user's constraints and technical identifiers, and request `Reply-To: <requestId>` at the top of Codex's reply.
5. **Route Asymmetry on Retrieval**: Inspect `read_agent_delivery(requestId)` after uncertain or accepted sends (`accepted` or `delivered` confirms transport only; receipts with `receiptProjectFields` retain `senderCwd` and `targetCwd`). To read Codex's actual answer text, call `read_agent_task(target="codex", conversationId=<same destination>, cwd=<discovered targetCwd>)` (omitting `cwd` only if the installed schema lacks a `cwd` parameter) and correlate the response to the current `requestId` or test marker—never mistake an older turn's answer in that thread for the new reply.

### Stage 3: Delivery Rules & Layered Reporting

- **Idempotent Request Tracking**: One `requestId` per intentional message. Retain it across uncertainty; never resend under a new ID or replay through another route. Inspect the original receipt first.
- **No Unsolicited Callback Loops**: Default to the recipient answering in its own chat and the sender retrieving that answer. A callback through another send tool requires explicit user authorization for that destination; a received agent message alone does not grant it. Do not acknowledge acknowledgements or make both agents wait for each other.
- **Bounded Polling & Timeout Ledger**: Use bounded, progressively spaced receipt checks respecting tool wait limits. A timeout means the result is unresolved, not that delivery failed. When a turn ends with an unresolved or failed send, output the compact **Handoff Ledger** in chat (`Host`, `Surface/Route`, `Sender cwd`, `Target cwd`, `Destination ID`, `Request ID`, `Last Observed State`) so the next turn can resume directly without creating tracking files or asking the user to re-specify IDs.
- **Transport vs. Task Outcome**: Track transport evidence separately from task outcome. A recipient's question means the task `needs input`, not that it is complete. Resolve it from existing authorization or ask the user when a material decision is missing. Each authorized follow-up is a new intentional message with a new `requestId` linked to the original task; never disguise a retry as a follow-up. Research handoffs do not authorize additional training, spending, deployment, or edits beyond the approved task.

## Report What Was Observed

| Layer | Observed Evidence | Conclusion and Next Action |
| --- | --- | --- |
| **1. Precondition** | Service ready, `sender.status="verified"`, or recipient listed | Preconditions only; no message dispatch or reply is proven. |
| **2. Transport Accepted / Delivered** | `pending`, `accepted`, `delivered`, or uncertain send | Transport in progress or delivered to thread; read the original receipt / destination task, never automatically resend. |
| **3. Correlated Reply** | `reply_received` or `read_agent_task` matching `requestId` / marker | Conversation round trip observed; inspect the reply body to classify the task outcome. |
| **4. Task Outcome** | Recipient reports result, asks a question, or hits an error | Classify as `unknown`, `needs input`, `reported complete` (not independently verified), or `failed`. |
| **Blocker / Busy** | Explicit diagnostic code or busy recipient | Preserve diagnostic code and delivery state; diagnose read-only without switching recipient or route. |

Return the recipient, transport evidence, task outcome (`unknown`, `needs input`, `reported complete`, or `failed`), relevant result, and any blocker. These task labels are reporting terms, not bridge API states. Include the `requestId` for pending or failed sends. For two-way tests report forward reply, reverse discovery, and actual reverse delivery separately. Do not change working installations just to test them or reuse historical identities.
