from pathlib import Path
from types import SimpleNamespace

from app.llm.service import LLMService


def test_python_llm_uses_remaining_context_for_response_budget():
    class Model:
        def tokenize(self, prompt):
            return [1] * 19

        def __call__(self, prompt, **kwargs):
            self.max_tokens = kwargs["max_tokens"]
            return {"choices": [{"text": "Complete response"}]}

    model = Model()
    service = LLMService(
        Path("model.gguf"), Path("llama-cli"), context_size=64,
        temperature=0.2, max_tokens=4096, gpu_layers=0,
    )
    service._load = lambda: model

    assert service.generate("prompt") == "Complete response"
    assert model.max_tokens == 45


def test_cli_generation_runs_until_context_is_full(monkeypatch):
    cli = Path("llama-cli")
    service = LLMService(
        Path("model.gguf"), cli, context_size=64,
        temperature=0.2, max_tokens=4096, gpu_layers=0,
    )
    service._load = lambda: cli
    captured = {}

    def run(arguments, **kwargs):
        captured["arguments"] = arguments
        return SimpleNamespace(returncode=0, stdout="Complete response", stderr="")

    monkeypatch.setattr("app.llm.service.subprocess.run", run)

    assert service.generate("prompt") == "Complete response"
    assert captured["arguments"][captured["arguments"].index("--n-predict") + 1] == "-2"
