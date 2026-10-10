"""Records every tool call so the UI can show what the office did. Used by the offline pipeline (Trace.call) and by the
Strands agents (TraceHooks), so both modes produce the same {agent, tool, input, output} events."""
import json
import time

class Trace:
    def __init__(self):
        self.events = []
        self._t0 = time.time()

    def _t(self):
        return round(time.time() - self._t0, 3)

    def call(self, agent: str, tool_name: str, fn, **kwargs):
        result = fn(**kwargs)
        self.events.append({"t": self._t(), "agent": agent, "tool": tool_name, "input": _short(kwargs), "output": _short(result)})
        return result

    def note(self, agent: str, text: str):
        self.events.append({"t": self._t(), "agent": agent, "tool": None, "input": None, "output": text})

def _short(obj, n=220):
    s = obj if isinstance(obj, str) else str(obj)
    return s if len(s) <= n else s[: n - 3] + "..."

def tool_result_text(result) -> str:
    """The readable part of a Strands ToolResult: its text and JSON content blocks."""
    parts = []
    for block in (result or {}).get("content", []) or []:
        if "text" in block:
            parts.append(block["text"])
        elif "json" in block:
            parts.append(json.dumps(block["json"], default=str))
    out = " ".join(parts)
    return f"[{result.get('status')}] {out}" if result and result.get("status") == "error" else out

def _is_answer(event) -> bool:
    from strands.tools.structured_output.structured_output_tool import StructuredOutputTool
    return isinstance(getattr(event, "selected_tool", None), StructuredOutputTool)

class TraceHooks:
    """Strands hook provider for one agent.

    - Guardrail: before a tool runs, anything outside this agent's allowlist is cancelled (and recorded), so no
      document or prompt can make an agent call a tool it was not given.
    - Recorder: after a tool runs, its input and real output are added to the trace.
    The agent's own answer form (Strands' structured-output tool, named after the answer model) is always allowed and is
    not recorded: it is how the agent returns its result, not an action."""

    def __init__(self, trace: Trace | None, agent_name: str, allowed: set[str] | None = None):
        self.trace, self.agent_name, self.allowed = trace, agent_name, allowed

    def register_hooks(self, registry, **kwargs):
        from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent
        registry.add_callback(BeforeToolCallEvent, self.before_tool)
        registry.add_callback(AfterToolCallEvent, self.after_tool)

    def before_tool(self, event):
        name = event.tool_use.get("name")
        if _is_answer(event):
            return
        if self.allowed is not None and name not in self.allowed:
            event.cancel_tool = f"Tool '{name}' is not allowed for the {self.agent_name}."
            if self.trace:
                self.trace.note(self.agent_name, f"Blocked a call to '{name}': not one of its tools.")

    def after_tool(self, event):
        if self.trace is None or _is_answer(event):
            return
        self.trace.events.append({"t": self.trace._t(), "agent": self.agent_name, "tool": event.tool_use.get("name"),
                                  "input": _short(event.tool_use.get("input")), "output": _short(tool_result_text(event.result))})
