# Install on Either Host

The portable unit is the `codex-antigravity-dialogue` folder with `SKILL.md` at its root. Copy the whole release folder, including `references` and `scripts`. `agents/openai.yaml` is optional Codex UI metadata; core instructions do not depend on it. The Python checker is optional; the instructions themselves need no Python runtime.

## Locate the Skill Root

Resolve the current user's home and configured skill root. The Windows installation used to develop this skill has these locations:

- Codex: `<CODEX_HOME>/skills/codex-antigravity-dialogue` (locally, `CODEX_HOME` defaults to `<home>/.codex`).
- Antigravity: `<home>/.gemini/config/skills/codex-antigravity-dialogue` (verified local root, not a universal default).

These are local host skill directories, not task destinations. Do not assume they apply to another user. For another machine, locate that version's configured user or workspace skill root through its skill listing, configuration, or current official documentation. Do not scatter duplicate copies across candidate directories.

Current Codex documentation also describes `.agents/skills` roots. Do not relocate a working installation merely to match a newer convention. Check the installed host's actual discovery mechanism. Antigravity versions may likewise differ from the development machine.

Extract so the confirmed skill root contains `codex-antigravity-dialogue/SKILL.md`, without another nested directory. If the name exists, inspect it before updating and preserve user changes. Refresh skill discovery or use the next session if necessary. Files on disk do not prove the current chat has loaded the skill.

## MCP Prerequisites

The ZIP contains instructions and an optional offline diagnostic helper. It does not install bridge code, credentials, services, account settings, or permissions.

- Codex needs `antigravity-bridge` tools for Desktop sends and replies.
- Antigravity needs `agent-bridge` tools for sender verification and Codex task discovery/sending.
- Codex's `codex-native-relay` companion must be operational for reverse delivery.
- By default, stock bridge installations require both hosts to share the same authorized local project directory (`sender.cwd == targetCwd`). Cross-project Desktop discovery and routing work **only** when the installed bridge runtime explicitly reports cross-project capability (`desktop.crossProjectDiscovery=true`, `receiptProjectFields=true`, `outbound.targetCwdRequired=true` on Codex; `codexScope="all-saved-local-projects"`, `targetCwdRequired=true` on Antigravity). Installing or updating this skill does **not** upgrade the bridge runtime.

If prerequisites are missing, diagnose before changing anything. Install/configure a bridge only when the user requests that additional work. Review current package instructions and side effects; do not assume general setup is Codex-only.

Documentation to consult for the installed version:

- Codex skills: https://developers.openai.com/codex/skills
- Antigravity skills: https://antigravity.google/docs/skills
- Bridge: https://github.com/buidangminh23/codex-mcp-bridge

## Invocation

In Codex invoke `$codex-antigravity-dialogue` with the project and recipient. In Antigravity ask it to use `codex-antigravity-dialogue` for Codex communication using its supported skill invocation mechanism. Natural-language Codex-Antigravity requests may also select the skill.

Specify the task or connection test, whether a return message is authorized, and exclusions such as no experiments. Recipient IDs are discovered at runtime.

Status inspection is read-only. An actual echo test sends a message. A task handoff sends the approved work and retrieves the reply; a reverse callback is a separate send that must be included in the authorization.
