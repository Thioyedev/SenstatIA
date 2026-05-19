import json
from unittest.mock import MagicMock, patch

import pytest

from agents.compute_agent import _run_sandbox, _validate_ast, compute_agent


# ── Pure logic: _validate_ast ─────────────────────────────────────────────────

class TestValidateAst:
    def test_simple_arithmetic_is_valid(self):
        ok, _ = _validate_ast("result = 2 + 2")
        assert ok

    def test_allowed_import_math(self):
        ok, _ = _validate_ast("import math\nresult = math.sqrt(9)")
        assert ok

    def test_allowed_import_statistics(self):
        ok, _ = _validate_ast("import statistics\nresult = statistics.mean([1, 2, 3])")
        assert ok

    def test_blocks_os_import(self):
        ok, reason = _validate_ast("import os\nresult = os.getcwd()")
        assert not ok
        assert "os" in reason

    def test_blocks_subprocess_import(self):
        ok, reason = _validate_ast("import subprocess\nresult = 1")
        assert not ok

    def test_blocks_socket_import(self):
        ok, reason = _validate_ast("import socket\nresult = 1")
        assert not ok

    def test_blocks_eval_builtin(self):
        ok, reason = _validate_ast("result = eval('1+1')")
        assert not ok
        assert "eval" in reason

    def test_blocks_exec_builtin(self):
        ok, reason = _validate_ast("exec('result = 1')")
        assert not ok

    def test_blocks_open_builtin(self):
        ok, reason = _validate_ast("result = open('/etc/passwd').read()")
        assert not ok

    def test_blocks_dunder_import(self):
        ok, reason = _validate_ast("result = __import__('os')")
        assert not ok

    def test_syntax_error_returns_false(self):
        ok, reason = _validate_ast("result = (")
        assert not ok
        assert "SyntaxError" in reason


# ── Sandbox execution ─────────────────────────────────────────────────────────

class TestRunSandbox:
    def test_simple_addition(self):
        out = _run_sandbox("result = 2 + 2")
        assert out == {"result": 4}

    def test_float_calculation(self):
        out = _run_sandbox("result = round(37.5 / 100 * 17_000_000)")
        assert out == {"result": 6375000}

    def test_uses_math_module(self):
        out = _run_sandbox("import math\nresult = math.floor(3.7)")
        assert out == {"result": 3}

    def test_list_result(self):
        out = _run_sandbox("result = [1, 2, 3]")
        assert out == {"result": [1, 2, 3]}

    def test_timeout_returns_error(self):
        out = _run_sandbox("import time; time.sleep(60); result = 1", timeout=1)
        # time is not in ALLOWED_IMPORTS — AST validator should block this
        assert "error" in out

    def test_blocked_import_returns_error(self):
        out = _run_sandbox("import os; result = os.getcwd()")
        assert "error" in out

    def test_syntax_error_returns_error(self):
        out = _run_sandbox("result = (")
        assert "error" in out


# ── compute_agent end-to-end (mocked) ────────────────────────────────────────

class TestComputeAgent:
    def test_returns_result_and_interpretation(self, base_state):
        code_resp = MagicMock()
        code_resp.content = [MagicMock(text="result = round(37.5 / 100 * 17_000_000)")]

        interp_resp = MagicMock()
        interp_resp.content = [MagicMock(text="Environ 6,4 millions de Sénégalais vivent sous le seuil de pauvreté.")]

        with patch("agents.compute_agent._client") as mock_client:
            mock_client.messages.create.side_effect = [code_resp, interp_resp]
            result = compute_agent({**base_state, "intent": "compute"})

        assert result["compute_output"] is not None
        assert result["compute_output"]["result"] == 6375000
        assert result["compute_output"]["interpretation"]
        assert result["compute_output"]["code"]

    def test_returns_none_when_no_chunks(self, base_state):
        result = compute_agent({**base_state, "retrieved_chunks": []})
        assert result["compute_output"] is None

    def test_returns_none_on_unsafe_code(self, base_state):
        code_resp = MagicMock()
        code_resp.content = [MagicMock(text="import os; result = os.getcwd()")]

        with patch("agents.compute_agent._client") as mock_client:
            mock_client.messages.create.return_value = code_resp
            result = compute_agent({**base_state, "intent": "compute"})

        assert result["compute_output"] is None

    def test_returns_none_on_api_error(self, base_state):
        with patch("agents.compute_agent._client") as mock_client:
            mock_client.messages.create.side_effect = Exception("API error")
            result = compute_agent({**base_state, "intent": "compute"})
        assert result["compute_output"] is None
