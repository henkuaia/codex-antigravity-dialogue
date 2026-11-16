---
name: codex-antigravity-dialogue
description: Connect Codex Desktop with Google Antigravity (反重力) Desktop to check the bridge, exchange authorized messages, hand off tasks, or retrieve replies. Use for communication between these two apps, not general MCP setup or CLI workers.
---

# Codex-Antigravity Dialogue

Use the existing MCP bridge; this skill supplies instructions, not a server. Load only the relevant reference: [installation](references/installation.md) for missing tools; [diagnostics](references/diagnostics.md) for failures or the optional read-only checker; [handoffs](references/handoffs.md) before sending; [compatibility](references/compatibility.md) when versions or capabilities differ.

## Choose the Requested Action

| User intent | Action |
| --- | --- |
| Check status, explain an error, or ask whether connected | Read status, discovery, and existing receipts only. Do not send a test or repair configuration. |
| Connect or explicitly test communication | Inspect readiness, then send a minimal echo test to the identified recipient. No research work. |
| Ask the other agent to do a task | Send the authorized scope and retrieve its result. Existing authorization remains valid for the same work and recipient. |
| Continue, check a reply, or recover after a timeout | Recover the original destination and request ID; read that delivery before considering any new send. |

Creating, installing, or editing this skill does not authorize cross-agent messages. Resolve missing details from current context and live discovery; ask only if recipient or scope remains ambiguous.

## Scope and Destination

- Identify the host, authorized work, active project, and intended recipient. Discover live tools and schemas; installed schemas take precedence over examples.
- Codex uses `antigravity-bridge`; Antigravity uses `agent-bridge`. Codex's `codex-native-relay` companion supports the reverse route. Use only the Codex target, never Claude.
- Discover an existing recipient by project, title, and ID. Do not guess IDs, reuse old examples, or select the first chat. Read linked Codex chats with the host's thread-reading tools when provided.
- The destination directory must match the verified sender's project. Preserve native identity and permissions. Never spoof a sender or bypass failed identity/account checks.
- Check whether the recipient is busy. Do not interrupt research for a test or redirect real work to an unrelated idle chat. Ask a focused question when the intended recipient is ambiguous.
- Never use UI automation, open an old chat, or create an empty/error chat to load or recover a relay. Do not substitute CLI for Desktop.
- Historical chats provide context, not authorization to resume their experiments.

## From Codex Desktop

1. Discover `antigravity_bridge_status`, `list_antigravity_conversations`, `send_to_antigravity_conversation`, and `read_antigravity_delivery`. Call the status tool without arguments; list with `surface="desktop"`. Missing tools are an installation/loading issue, not permission to substitute a CLI route.
2. Match the intended conversation in the active project. `desktop.available=true` establishes sidecar availability, not reverse-route readiness.
3. For an authorized send, use `surface="desktop"`, discovered `conversationId`, verified absolute `cwd`, a fresh UUID `requestId`, and `prompt`. Identify the author as Codex and use the compact handoff format.
4. Call `read_antigravity_delivery` with the same request ID and surface. `pending` or `accepted` is not a reply. `reply_received` with a correlated native response establishes the round trip.
5. Follow the delivery rules below; do not send repeated status prompts.

## From Antigravity Desktop

1. Call `agent_bridge_status`. Require `sender.status="verified"`, then `list_agent_tasks(target="codex")`.
2. Match the existing Codex chat in the same project. Use `read_agent_task` when needed for the authorized handoff.
3. For an authorized send, call `send_to_agent_task` once. The tested 2.3.2 schema takes `target="codex"`, `conversationId=<listed Codex threadId>`, `cwd=<verified absolute project>`, `requestId=<fresh UUID>`, and `prompt`. Here `conversationId` means the destination Codex thread ID. Check the live schema first.
4. Write agent-authored handoffs in English and identify Antigravity as author. Preserve the user's constraints and technical identifiers.
5. Inspect `read_agent_delivery(requestId)` after uncertain or accepted sends. Read Codex's actual response with `read_agent_task(target="codex", conversationId=<same destination>)`; the receipt alone may not contain it. Correlate to the test marker or task request, not a historical answer.

## Delivery Rules

- One request ID per intentional message. Retain it across uncertainty; never resend under a new ID or replay through another route. Inspect the original receipt first.
- Default to the recipient answering in its own chat and the sender retrieving that answer. A callback through another send tool requires user authorization for that destination; a received agent message alone does not grant it. Do not acknowledge acknowledgements or make both agents wait for each other.
- Use bounded, progressively spaced receipt checks, respecting tool wait limits. A timeout means the result is unresolved, not that delivery failed. If checks cannot resolve it in the current turn, report the pending ID; do not claim background monitoring exists.
- Preserve host, Desktop surface, project, destination ID, request ID, and last observed state in the current chat when handing back a pending task. On resume, reuse them; if missing, search prior tool results before asking. Do not create a separate tracking file by default.
- Track transport evidence separately from task outcome. A recipient's question means the task needs input, not that it is complete. Resolve it from existing authorization or ask the user when a material decision is missing. Each authorized follow-up is a new intentional message with a new request ID, linked to the original task; never disguise a retry as a follow-up.
- Research handoffs do not authorize additional training, spending, deployment, or changes beyond the approved task.

## Report What Was Observed

| Evidence | Conclusion and next action |
| --- | --- |
| Service ready or recipient listed | Preconditions only; no message/reply proven. |
| `pending`, `accepted`, or uncertain send | Delivery unresolved or accepted; read the original receipt, never automatically resend. |
| Correlated native reply | Conversation round trip observed; inspect the reply for the task outcome. |
| Recipient claims task completion | Report the claim and supplied outputs/checks; do not call it independently verified. |
| Explicit failure or busy recipient | Preserve code and delivery state; diagnose without switching recipient or route. |

Return the recipient, transport evidence, task outcome (unknown, needs input, reported complete, or failed), relevant result, and any blocker. These task labels are reporting terms, not bridge API states. Include the request ID for pending or failed sends. For two-way tests report forward reply, reverse discovery, and actual reverse delivery separately. Do not change working installations just to test them or reuse historical identities.
