"""Records every tool call so the UI can show a live 'agent trace' panel. Used by the offline pipeline and by the
Strands agents (via TraceHandler)."""
import time

class Trace:
    def __init__(self):
        self.events = []
        self._t0 = time.time()

    def call(self, agent: str, tool_name: str, fn, **kwargs):
        result = fn(**kwargs)
        self.events.append({"t": round(time.time() - self._t0, 3), "agent": agent, "tool": tool_name,
                            "input": _short(kwargs), "output": _short(result)})
        return result

    def note(self, agent: str, text: str):
        self.events.append({"t": round(time.time() - self._t0, 3), "agent": agent, "tool": None, "input": None, "output": text})

def _short(obj, n=220):
    s = str(obj)
    return s if len(s) <= n else s[: n - 3] + "..."

class TraceHandler:
    """Pass as Agent(callback_handler=TraceHandler(trace, 'Auditor')). Records each tool use once."""
    def __init__(self, trace: Trace, agent_name: str):
        self.trace, self.agent_name, self._seen = trace, agent_name, set()

    def __call__(self, **kwargs):
        tu = kwargs.get("current_tool_use")
        if tu and tu.get("name") and tu.get("toolUseId") not in self._seen:
            self._seen.add(tu["toolUseId"])
            self.trace.events.append({"t": round(time.time() - self.trace._t0, 3), "agent": self.agent_name,
                                      "tool": tu["name"], "input": _short(tu.get("input")), "output": None})
