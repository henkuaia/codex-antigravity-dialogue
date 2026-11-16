# Bridge Diagnostics

Use read-only evidence first. Repairs require authorization and must preserve native access checks. Do not infer filesystem isolation from a generic failure or install Claude to fix a Codex-only route.

| Symptom | Narrow investigation |
| --- | --- |
| `MODULE_NOT_FOUND` | Inspect active MCP command/arguments, entry file existence, package location, and runtime. A failed load does not prove a permissions issue. |
| `ANTIGRAVITY_SENDER_UNVERIFIED` | Inspect workspace/project metadata and native conversation identity. A prior 2.3.2 fix supported both `gitFolder.folderUri` and `folderUri`; confirm the installed implementation before treating that as the cause. Never forge metadata or disable verification. |
| `BRIDGE_ACCOUNT_UNVERIFIED` with Codex target | Determine which account was checked. Historical code unnecessarily required Claude for a Codex target. Use a supported Codex-only path; do not fake accounts or disable required Codex authentication. |
| `RELAY_UNREACHABLE` | Check companion status, configured endpoint, relay config, registration, and listener. Codex being open does not establish relay readiness. Distinguish `ENOENT`, `EACCES`, `EPERM`, and connection refusal. |
| `WORKER_RELAY_NOT_CONFIGURED` | This is the separate CLI worker route, not proof that Desktop is broken. Do not set up workers just to test Desktop. |
| `accepted` / `ANTIGRAVITY_REPLY_NOT_OBSERVED` | The app accepted delivery; no correlated final reply has been observed. Inspect the same receipt, never resend automatically. |
| `delivered` (`DELIVERED_AWAITING_TASK_READ`) | Transport delivered to the destination thread (e.g. `Antigravity → Codex`); call `read_agent_task(target="codex", conversationId=...)` and match `Reply-To: <requestId>` to read the actual reply. |
| `failed` / `rejected` (`DELIVERY_FAILED`) | Delivery failed after dispatch attempt; preserve the original `requestId` and diagnostic code without replaying on another route. |

## Windows Local Checks

For deterministic local inspection, use [doctor.py](../scripts/doctor.py) with Python 3.11+ and an explicit configuration path. It reads only the selected files. It never starts a process, contacts a service, sends a message, installs a package, or changes configuration.

```powershell
python scripts/doctor.py --host codex --config "<active-codex-config.toml>"
python scripts/doctor.py --host antigravity --config "<active-antigravity-mcp_config.json>"
python scripts/doctor.py --host codex --status "<status.json>" --relay-status "<relay-status.json>"
python scripts/doctor.py --host codex --delivery "<receipt.json>" --request-id "<original-request-id>"
```

Status and receipt inputs must be the decoded JSON object from the tool, not a transcript or MCP content envelope. For `native_relay_status`, use its `structuredContent` object. Existing exported files may contain private data: do not commit or upload them. Do not create exports just for routine checks when the native tool result already answers the question.

The helper checks named bridge registrations, disabled flags, command presence, direct Node entry files, and the known supervisor worker entry. Other launchers and relative paths remain `unknown`; it does not guess the host working directory. It can classify exported status, relay readiness, known diagnostic codes, and receipt/request matching. It does not list recipients, infer whether a chat is busy, or validate a native reply's contents.

Exit codes: `0` inspection finished (may include `unknown`); `1` a supplied check failed; `2` invalid input. `overall=inspected` means only that supplied checks passed, never that the connection or task completed. Reports omit configuration values, paths, prompts, IDs, and raw errors; only known diagnostic codes are echoed. Inspect original unknown errors locally.

Resolve the actual home directory and `CODEX_HOME` first. A typical installation uses `<CODEX_HOME>/native-relay.json` and a `codex-native-relay` MCP registration. The package may select named pipes rather than TCP; a TCP scan alone is insufficient.

Prefer `native_relay_status`. `nativeDispatch.ready=true` establishes reported dispatch readiness, not a completed cross-agent exchange. Inspect Antigravity's active MCP/sidecar configurations rather than assuming global npm is the running source. Preserve existing local compatibility changes.

If configuration was saved but the companion is absent, distinguish installation from runtime loading. Use a supported refresh if available; otherwise explain that the user may need to restart the owning app after ongoing work is safe. Do not kill apps or open/create chats to trigger loading.

Do not blindly run package-wide setup: inspect effects first. Historical native relay installation could create an internal executor and start an extra app-server; general setup may configure unrelated providers or permissions. Never create an executor chat as a workaround under this skill. If supported installation requires that step, explain the requirement and defer to the host's explicit restrictions and authorization rules.

## Validation Boundary

See [compatibility](compatibility.md) for historical integration evidence and its limits. Do not treat offline helper tests as a live bridge test.
