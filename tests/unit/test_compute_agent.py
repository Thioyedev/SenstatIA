import json
from unittest.mock import MagicMock, patch

import pytest

from agents.compute_agent import _run_sandbox, _validate_ast, compute_agent


class TestValidateAst:
    def test_simple_arithmetic_is_valid(self):
        ok, _ = _validate_ast("result = 2 + 2")
        assert ok

    def test_allowed_import_math(self):
        ok, _ = _validate_ast("import math\nresult = math.sqrt(9)")
        assert ok

    def test_allowed_import_statistics(self):
        ok, _ = _validate_ast("import statistics\nresult = statistics.mean([1,2,3])")
        assert ok

    def test_blocks_os_import(self):
        ok, reason = _validate_ast("import os\nresult = os.getcwd()")
        assert not ok and "os" in reason

    def test_blocks_subprocess_import(self):
        ok, _ = _validate_ast("import subprocess\nresult = 1")
        assert not ok

    def test_blocks_socket_import(self):
        ok, _ = _validate_ast("import socket\nresult = 1")
        assert not ok

    def test_blocks_eval_builtin(self):
        ok, reason = _validate_ast("result = eval('1+1')")
        assert not ok and "eval" in reason

    def test_blocks_exec_builtin(self):
        ok, _ = _validate_ast("exec('result = 1')")
        assert not ok

    def test_blocks_open_builtin(self):
        ok, _ = _validate_ast("result = open('/etc/passwd').read()")
        assert not ok

    def test_blocks_dunder_import(self):
        ok, _ = _validate_ast("result = __import__('os')")
        assert not ok

    def test_syntax_error_returns_false(self):
        ok, reason = _validate_ast("result = (")
        assert not ok and "SyntaxError" in reason


class TestRunSandbox:
    def test_simple_addition(self):
        assert _run_sandbox("result = 2 + 2") == {"result": 4}

    def test_float_calculation(self):
        assert _run_sandbox("result = round(37.5 / 100 * 17_000_000)") == {"result": 6375000}

    def test_uses_math_module(self):
        assert _run_sandbox("import math\nresult = math.floor(3.7)") == {"result": 3}

    def test_blocked_import_returns_error(self):
        out = _run_sandbox("import os; result = os.getcwd()")
        assert "error" in out

    def test_syntax_error_returns_error(self):
        assert "error" in _run_sandbox("result = (")


class TestComputeAgent:
    def test_returns_result_and_interpretation(self, base_state):
        code_resp = MagicMock()
        code_resp.content = [MagicMock(text="result = round(37.5 / 100 * 17_000_000)")]
        interp_resp = MagicMock()
        interp_resp.content = [MagicMock(text="6,4 millions de Sénégalais sous le seuil.")]
        with patch("agents.compute_agent._client") as c:
            c.messages.create.side_effect = [code_resp, interp_resp]
            result = compute_agent({**base_state, "intent": "compute"})
        assert result["compute_output"]["result"] == 6375000
        assert result["compute_output"]["interpretation"]

    def test_returns_none_when_no_chunks(self, base_state):
        assert compute_agent({**base_state, "retrieved_chunks": []})["compute_output"] is None

    def test_returns_none_on_unsafe_code(self, base_state):
        code_resp = MagicMock()
        code_resp.content = [MagicMock(text="import os; result = os.getcwd()")]
        with patch("agents.compute_agent._client") as c:
            c.messages.create.return_value = code_resp
            result = compute_agent({**base_state, "intent": "compute"})
        assert result["compute_output"] is None

    def test_returns_none_on_api_error(self, base_state):
        with patch("agents.compute_agent._client") as c:
            c.messages.create.side_effect = Exception("error")
            result = compute_agent({**base_state, "intent": "compute"})
        assert result["compute_output"] is None


class TestSandboxEscapeRoutes:
    """Regression: the validator once blocked builtin names only, so code could
    walk the object graph through dunder attributes and reach os without naming
    a forbidden builtin. Each test pins one route into that graph shut."""

    @pytest.mark.parametrize(
        "code",
        [
            "x = ().__class__",
            "x = (1).__dict__",
            "x = f'{(1).__class__}'",
            "x = 'a' + '__class__'",
            "x = '{0.__class__}'.format(1)",
            "x = '{a}'.format_map({'a': 1})",
            "x = getattr(1, 'real')",
            "x = type(1)",
            "x = dir()",
            "from os import path",
        ],
    )
    def test_route_is_rejected(self, code):
        ok, _ = _validate_ast(code)
        assert not ok

    def test_from_math_import_is_allowed(self):
        assert _run_sandbox("from math import sqrt\nresult = sqrt(16)") == {"result": 4.0}

    def test_fstring_without_dunder_is_allowed(self):
        assert _run_sandbox("v = 37.5\nresult = f'{v:.1f} %'") == {"result": "37.5 %"}

    def test_builtin_outside_allowlist_fails_at_runtime(self):
        # id passes the AST check; the restricted namespace still refuses it.
        out = _run_sandbox("result = id(1)")
        assert "NameError" in out["error"]

    def test_code_reaches_the_child_via_stdin_not_source(self):
        # Triple quotes would have broken the old source-splicing wrapper.
        assert _run_sandbox('result = len("""ab""")') == {"result": 2}
