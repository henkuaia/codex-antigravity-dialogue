#!/usr/bin/env python3
"""Read local MCP configuration and exported bridge JSON; never contact a service."""

import argparse
import json
from pathlib import Path
import shutil
import sys
import tomllib


SERVERS = {
    "codex": ("antigravity-bridge", "codex-native-relay"),
    "antigravity": ("agent-bridge",),
}
DIAGNOSTICS = {
    "MODULE_NOT_FOUND": "Check the configured runtime and entry files.",
    "ANTIGRAVITY_SENDER_UNVERIFIED": "Check native sender and project identity; do not bypass verification.",
    "BRIDGE_ACCOUNT_UNVERIFIED": "Check the required account for the Codex target; do not install another provider.",
    "BRIDGE_OPERATION_FAILED": "Check whether the sender workspace matches a saved local Codex project; do not spoof cwd.",
    "RELAY_UNREACHABLE": "Inspect native relay registration and its actual endpoint.",
    "ANTIGRAVITY_SIDECAR_UNAVAILABLE": "Inspect the Desktop sidecar; this does not prove the app is closed.",
    "WORKER_RELAY_NOT_CONFIGURED": "This is a CLI worker diagnostic, not Desktop readiness.",
    "ANTIGRAVITY_REPLY_NOT_OBSERVED": "Read the original receipt; do not resend.",
}


def object_value(value):
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON/TOML object.")
    return value


def load_json(path):
    return object_value(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def check(name, state, code, action):
    return {"check": name, "state": state, "code": code, "next_action": action}


def inspect_config(path, host):
    text = Path(path).read_text(encoding="utf-8-sig")
    data = tomllib.loads(text) if host == "codex" else json.loads(text)
    key = "mcp_servers" if host == "codex" else "mcpServers"
    servers = object_value(object_value(data).get(key, {}))
    checks = []
    for name in SERVERS[host]:
        if name not in servers:
            checks.append(check(name, "fail", "SERVER_NOT_CONFIGURED", "Inspect the active host configuration."))
            continue
        spec = object_value(servers[name])
        if spec.get("enabled") is False or spec.get("disabled") is True:
            checks.append(check(name, "fail", "SERVER_DISABLED", "Report that the server is disabled; do not enable it automatically."))
            continue
        command, args = spec.get("command"), spec.get("args", [])
        if not isinstance(command, str) or not command:
            checks.append(check(name, "unknown", "LOCAL_COMMAND_NOT_CONFIGURED", "This checker only inspects local stdio bridge commands."))
            continue
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise ValueError("MCP args must be an array of strings.")
        executable = Path(command)
        if executable.is_absolute():
            found = executable.is_file()
        elif executable.name == command:
            found = shutil.which(command) is not None
        else:
            checks.append(check(name, "unknown", "RELATIVE_COMMAND", "Resolve the host process working directory before judging this path."))
            continue
        checks.append(check(name, "pass" if found else "fail", "COMMAND_FOUND" if found else "COMMAND_NOT_FOUND", "File presence does not establish process or connection readiness."))
        if executable.name.lower() not in ("node", "node.exe") or not args or Path(args[0]).suffix not in (".js", ".cjs", ".mjs"):
            checks.append(check(name + ".entry", "unknown", "ENTRY_NOT_CHECKED", "Inspect this launcher's entry resolution manually; it was not executed."))
            continue
        entry = Path(args[0])
        if not entry.is_absolute():
            checks.append(check(name + ".entry", "unknown", "RELATIVE_ENTRY", "Resolve the host process working directory; do not assume the config directory."))
            continue
        exists = entry.is_file()
        checks.append(check(name + ".entry", "pass" if exists else "fail", "ENTRY_FOUND" if exists else "MODULE_NOT_FOUND", "Check the active installation without running package setup."))
        if entry.name == "mcp-supervisor.mjs":
            worker = entry.parent / args[1] if len(args) > 1 else None
            exists = worker is not None and worker.is_file()
            checks.append(check(name + ".worker", "pass" if exists else "fail", "WORKER_ENTRY_FOUND" if exists else "MODULE_NOT_FOUND", "Check the supervisor's selected worker file."))
    return checks


def diagnostic_check(data, name):
    diagnostic = object_value(data.get("diagnostic", {}))
    code = data.get("code", diagnostic.get("code"))
    if code is None:
        return None
    if not isinstance(code, str):
        raise ValueError("Diagnostic code must be a string.")
    if code == "ANTIGRAVITY_REPLY_NOT_OBSERVED":
        return check(name, "unknown", code, DIAGNOSTICS[code])
    if code in DIAGNOSTICS:
        return check(name, "fail", code, DIAGNOSTICS[code])
    return check(name, "unknown", "UNRECOGNIZED_DIAGNOSTIC", "Inspect the original diagnostic locally; do not publish its raw payload.")


def inspect_status(data, host):
    data = object_value(data)
    error = diagnostic_check(data, "bridge")
    if error:
        return [error]
    if host == "codex":
        desktop = object_value(data.get("desktop", {}))
        error = diagnostic_check(desktop, "desktop")
        if error:
            return [error]
        available = desktop.get("available")
        if available is True:
            return [check("desktop", "pass", "SIDECAR_REPORTED_AVAILABLE", "Read-only readiness only; reverse route and messages are unverified.")]
        if available is False:
            return [check("desktop", "fail", "SIDECAR_REPORTED_UNAVAILABLE", "Inspect sidecar configuration without opening chats.")]
    else:
        sender = object_value(data.get("sender", {})).get("status")
        if sender == "verified":
            return [check("sender", "pass", "SENDER_REPORTED_VERIFIED", "Identity only; Codex discovery and delivery remain unverified.")]
        if sender == "unverified":
            return [check("sender", "fail", "ANTIGRAVITY_SENDER_UNVERIFIED", DIAGNOSTICS["ANTIGRAVITY_SENDER_UNVERIFIED"])]
    return [check("bridge", "unknown", "STATUS_NOT_RECOGNIZED", "Use the decoded JSON body from the correct host's status tool.")]


def inspect_relay(data):
    data = object_value(data)
    error = diagnostic_check(data, "relay")
    if error:
        return [error]
    ready = object_value(data.get("nativeDispatch", {})).get("ready")
    state = "pass" if ready is True else "fail" if ready is False else "unknown"
    return [check("relay", state, "RELAY_REPORTED_READY" if ready is True else "RELAY_NOT_VERIFIED", "Dispatch readiness is not actual reverse-message delivery.")]


def inspect_delivery(data, request_id):
    data = object_value(data)
    error = diagnostic_check(data, "delivery")
    if error:
        return [error]
    if not request_id or not data.get("requestId"):
        return [check("delivery", "unknown", "REQUEST_CORRELATION_MISSING", "Recover the original request ID and read its receipt; do not resend.")]
    if data["requestId"] != request_id:
        return [check("delivery", "fail", "REQUEST_MISMATCH", "This receipt is for another request; read the original request.")]
    states = [data.get("status"), data.get("deliveryState")]
    for key in ("result", "replyObservation"):
        if key in data and data[key] is not None:
            states.append(object_value(data[key]).get("status"))
    if "reply_received" in states:
        return [check("delivery", "pass", "REPLY_REPORTED", "Inspect the correlated native reply and task outputs; completion is not verified by this script.")]
    if "not_sent" in states:
        return [check("delivery", "fail", "NOT_SENT", "Inspect the rejection and original authorization before any new send.")]
    if any(state in ("failed", "rejected", "error") for state in states):
        return [check("delivery", "fail", "DELIVERY_FAILED", "Inspect the delivery failure locally and preserve the request ID; do not automatically resend.")]
    if "delivered" in states:
        return [check("delivery", "unknown", "DELIVERED_AWAITING_TASK_READ", "Transport delivered to the destination chat; read the destination task/chat to inspect the correlated reply.")]
    if any(state in ("pending", "accepted", "unknown") for state in states):
        return [check("delivery", "unknown", "AWAITING_REPLY", "Read the same request with bounded waits; never automatically resend.")]
    return [check("delivery", "unknown", "DELIVERY_NOT_RECOGNIZED", "Inspect the original receipt locally; do not infer task completion.")]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=tuple(SERVERS), required=True)
    parser.add_argument("--config", type=Path, help="Explicit active Codex TOML or Antigravity JSON config")
    parser.add_argument("--status", type=Path, help="Decoded status-tool JSON body, not a transcript")
    parser.add_argument("--relay-status", type=Path, help="Decoded native_relay_status JSON body")
    parser.add_argument("--delivery", type=Path, help="Decoded delivery-tool JSON body")
    parser.add_argument("--request-id", help="Original request ID for receipt correlation")
    args = parser.parse_args(argv)
    if not any((args.config, args.status, args.relay_status, args.delivery)):
        parser.error("provide at least one explicit input file")
    try:
        checks = inspect_config(args.config, args.host) if args.config else []
        if args.status:
            checks.extend(inspect_status(load_json(args.status), args.host))
        if args.relay_status:
            checks.extend(inspect_relay(load_json(args.relay_status)))
        if args.delivery:
            checks.extend(inspect_delivery(load_json(args.delivery), args.request_id))
    except (OSError, ValueError) as error:
        # Do not echo parser errors: they can contain private configuration text.
        print(json.dumps({"schema_version": 1, "error": "INPUT_UNREADABLE_OR_INVALID", "kind": type(error).__name__}))
        return 2
    failed = any(item["state"] == "fail" for item in checks)
    report = {
        "schema_version": 1,
        "host": args.host,
        "overall": "blocked" if failed else "incomplete" if any(item["state"] == "unknown" for item in checks) else "inspected",
        "checks": checks,
        "task_completion": "not_verified",
        "live_probe_performed": False,
    }
    print(json.dumps(report, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
