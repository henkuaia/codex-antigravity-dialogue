import contextlib
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import doctor


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def config(self, spec, host="antigravity"):
        path = self.root / "mcp.json"
        path.write_text(json.dumps({"mcpServers": {"agent-bridge": spec}}), encoding="utf-8")
        return doctor.inspect_config(path, host)

    def launch_spec(self):
        node = self.root / "node.exe"
        node.touch()
        entry = self.root / "mcp-supervisor.mjs"
        entry.touch()
        worker = self.root / "antigravity-outbound-bridge.mjs"
        worker.touch()
        return {"command": str(node), "args": [str(entry), worker.name]}

    def test_local_supervisor_files_found_without_running_them(self):
        spec = self.launch_spec()
        with patch.object(subprocess, "Popen", side_effect=AssertionError("must not execute")), patch.object(socket, "socket", side_effect=AssertionError("must not connect")):
            checks = self.config(spec)
        self.assertEqual([item["state"] for item in checks], ["pass", "pass", "pass"])

    def test_missing_supervisor_entry(self):
        spec = self.launch_spec()
        Path(spec["args"][0]).unlink()
        self.assertEqual(self.config(spec)[1]["code"], "MODULE_NOT_FOUND")

    def test_missing_worker_entry(self):
        spec = self.launch_spec()
        (self.root / spec["args"][1]).unlink()
        self.assertEqual(self.config(spec)[2]["code"], "MODULE_NOT_FOUND")

    def test_disabled_server_is_not_enabled(self):
        self.assertEqual(self.config({"disabled": True})[0]["code"], "SERVER_DISABLED")

    def test_missing_runtime(self):
        checks = self.config({"command": str(self.root / "absent.exe")})
        self.assertEqual(checks[0]["code"], "COMMAND_NOT_FOUND")

    def test_relative_entry_is_unknown_not_missing(self):
        spec = self.launch_spec()
        spec["args"][0] = "relative/entry.mjs"
        self.assertEqual(self.config(spec)[1]["code"], "RELATIVE_ENTRY")

    def test_other_launcher_is_not_executed_or_guessed(self):
        checks = self.config({"command": sys.executable, "args": ["wrapper.py"]})
        self.assertEqual(checks[-1]["code"], "ENTRY_NOT_CHECKED")

    def test_codex_toml_and_missing_reverse_registration(self):
        path = self.root / "config.toml"
        path.write_text('[mcp_servers.antigravity-bridge]\ncommand = ' + json.dumps(sys.executable) + '\n', encoding="utf-8")
        checks = doctor.inspect_config(path, "codex")
        self.assertEqual(checks[0]["code"], "COMMAND_FOUND")
        self.assertEqual(checks[-1]["check"], "codex-native-relay")
        self.assertEqual(checks[-1]["code"], "SERVER_NOT_CONFIGURED")

    def test_config_values_and_secrets_are_not_in_output(self):
        checks = self.config({"command": sys.executable, "env": {"TOKEN": "private-test-token"}, "args": ["secret-argument"]})
        text = json.dumps(checks)
        self.assertNotIn("private-test-token", text)
        self.assertNotIn("secret-argument", text)
        self.assertNotIn(sys.executable, text)

    def test_invalid_args_fail_explicitly(self):
        with self.assertRaises(ValueError):
            self.config({"command": "node", "args": "entry.mjs"})

    def test_available_sidecar_is_not_reverse_readiness(self):
        check = doctor.inspect_status({"desktop": {"available": True}}, "codex")[0]
        self.assertEqual(check["code"], "SIDECAR_REPORTED_AVAILABLE")

    def test_missing_fields_remain_unknown(self):
        for host in ("codex", "antigravity"):
            with self.subTest(host=host):
                self.assertEqual(doctor.inspect_status({}, host)[0]["state"], "unknown")

    def test_false_sidecar_is_a_failure(self):
        self.assertEqual(doctor.inspect_status({"desktop": {"available": False}}, "codex")[0]["state"], "fail")

    def test_unverified_sender(self):
        check = doctor.inspect_status({"sender": {"status": "unverified"}}, "antigravity")[0]
        self.assertEqual(check["code"], "ANTIGRAVITY_SENDER_UNVERIFIED")

    def test_verified_sender_does_not_prove_delivery(self):
        check = doctor.inspect_status({"sender": {"status": "verified"}}, "antigravity")[0]
        self.assertEqual(check["code"], "SENDER_REPORTED_VERIFIED")

    def test_known_diagnostic_keeps_code_not_private_reason(self):
        check = doctor.inspect_status({"code": "RELAY_UNREACHABLE", "error": "private pipe path"}, "antigravity")[0]
        self.assertEqual(check["code"], "RELAY_UNREACHABLE")
        self.assertNotIn("private pipe path", json.dumps(check))

    def test_unknown_diagnostic_is_not_echoed(self):
        check = doctor.inspect_status({"code": "private-unknown-code"}, "codex")[0]
        self.assertEqual(check["state"], "unknown")
        self.assertNotIn("private-unknown-code", json.dumps(check))

    def test_relay_readiness_true_false_and_missing(self):
        for value, expected in ((True, "pass"), (False, "fail"), (None, "unknown")):
            with self.subTest(value=value):
                self.assertEqual(doctor.inspect_relay({"nativeDispatch": {"ready": value}})[0]["state"], expected)

    def test_receipt_requires_matching_request(self):
        data = {"requestId": "request-a", "status": "reply_received"}
        self.assertEqual(doctor.inspect_delivery(data, None)[0]["state"], "unknown")
        self.assertEqual(doctor.inspect_delivery(data, "request-b")[0]["code"], "REQUEST_MISMATCH")
        self.assertEqual(doctor.inspect_delivery(data, "request-a")[0]["code"], "REPLY_REPORTED")

    def test_pending_accepted_and_unknown_do_not_prove_reply(self):
        for status in ("pending", "accepted", "unknown"):
            with self.subTest(status=status):
                check = doctor.inspect_delivery({"requestId": "a", "status": status}, "a")[0]
                self.assertEqual(check["code"], "AWAITING_REPLY")

    def test_nested_reply_observation(self):
        data = {"requestId": "a", "status": "accepted", "replyObservation": {"status": "reply_received"}}
        self.assertEqual(doctor.inspect_delivery(data, "a")[0]["code"], "REPLY_REPORTED")

    def test_not_sent_and_reply_not_observed_are_different(self):
        self.assertEqual(doctor.inspect_delivery({"requestId": "a", "deliveryState": "not_sent"}, "a")[0]["state"], "fail")
        self.assertEqual(doctor.inspect_delivery({"code": "ANTIGRAVITY_REPLY_NOT_OBSERVED"}, "a")[0]["state"], "unknown")

    def test_delivered_requires_destination_task_read_and_failed_is_reported(self):
        delivered = doctor.inspect_delivery({"requestId": "a", "status": "delivered"}, "a")[0]
        self.assertEqual(delivered["state"], "unknown")
        self.assertEqual(delivered["code"], "DELIVERED_AWAITING_TASK_READ")
        for fail_state in ("failed", "rejected", "error"):
            with self.subTest(fail_state=fail_state):
                failed = doctor.inspect_delivery({"requestId": "a", "status": fail_state}, "a")[0]
                self.assertEqual(failed["state"], "fail")
                self.assertEqual(failed["code"], "DELIVERY_FAILED")

    def test_cli_is_read_only_and_never_claims_task_completion(self):
        path = self.root / "status.json"
        payload = json.dumps({"desktop": {"available": True}})
        path.write_text(payload, encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = doctor.main(["--host", "codex", "--status", str(path)])
        report = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(report["task_completion"], "not_verified")
        self.assertFalse(report["live_probe_performed"])
        self.assertEqual(path.read_text(encoding="utf-8"), payload)

    def test_cli_failure_exit_code(self):
        path = self.root / "status.json"
        path.write_text('{"sender":{"status":"unverified"}}', encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(doctor.main(["--host", "antigravity", "--status", str(path)]), 1)

    def test_cli_invalid_input_does_not_echo_contents_or_path(self):
        path = self.root / "private-config.json"
        path.write_text('{"secret": "private-test-token"', encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = doctor.main(["--host", "codex", "--status", str(path)])
        self.assertEqual(code, 2)
        self.assertNotIn("private-test-token", output.getvalue())
        self.assertNotIn("private-config", output.getvalue())


if __name__ == "__main__":
    unittest.main()
