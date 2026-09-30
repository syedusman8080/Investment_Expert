import logging
import json
import subprocess
from urllib import request as urlrequest
from pathlib import Path
from time import perf_counter

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(
        self,
        model_path: Path,
        cli_path: Path,
        context_size: int,
        temperature: float,
        max_tokens: int,
        gpu_layers: int,
        provider: str = "local",
        api_url: str = "",
        api_key: str = "",
        api_model: str = "",
    ):
        self.model_path = model_path
        self.cli_path = cli_path
        self.context_size = context_size
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.gpu_layers = gpu_layers
        self.provider = provider.lower()
        self.api_url = api_url
        self.api_key = api_key
        self.api_model = api_model
        self._model = None

    def _load(self):
        if self._model is None:
            if not self.model_path.exists():
                raise RuntimeError(f"Local LLM model not found at '{self.model_path}'.")
            try:
                from llama_cpp import Llama
                self._model = Llama(
                    model_path=str(self.model_path),
                    n_ctx=self.context_size,
                    n_gpu_layers=self.gpu_layers,
                    verbose=False,
                )
            except Exception as exc:
                logger.warning("Python llama-cpp binding unavailable; trying local llama.cpp CLI: %s", exc)
                if not self.cli_path.exists():
                    raise RuntimeError(
                        f"Local LLM could not be loaded. Install llama-cpp-python or provide a "
                        f"valid llama-cli executable at '{self.cli_path}'."
                    ) from exc
                return self.cli_path
        return self._model

    def generate(self, prompt: str) -> str:
        started = perf_counter()
        try:
            if self.provider == "demo":
                return (
                    "Based on the Finance Guru knowledge base: "
                    "I can help you learn about investing step by step. "
                    "For a useful answer, tell me your goal, time horizon, and comfort with risk. "
                    "This is educational information, not personalized financial advice."
                )
            if self.provider in {"openai", "hosted", "huggingface"}:
                return self._generate_hosted(prompt)
            model = self._load()
            if isinstance(model, Path):
                result = subprocess.run(
                    [
                        str(model),
                        "--model", str(self.model_path),
                        "--ctx-size", str(self.context_size),
                        "--n-predict", str(self.max_tokens),
                        "--temperature", str(self.temperature),
                        "--n-gpu-layers", str(self.gpu_layers),
                        "--no-display-prompt",
                        "--no-perf",
                        "--simple-io",
                        "--single-turn",
                        "--prompt", prompt,
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    timeout=600,
                )
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip() or "llama.cpp CLI exited with an error.")
                answer = result.stdout.strip()
            else:
                result = model(
                    prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stop=["<|im_end|>", "</s>"],
                )
                answer = result["choices"][0]["text"].strip()
            logger.info("LLM inference duration_ms=%.1f", (perf_counter() - started) * 1000)
            return answer
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError("LLM inference failed.") from exc

    def _generate_hosted(self, prompt: str) -> str:
        if not self.api_key or not self.api_url:
            raise RuntimeError("Hosted LLM is selected but LLM_API_KEY or LLM_API_URL is missing.")
        body = json.dumps({
            "model": self.api_model,
            "messages": [
                {"role": "system", "content": "You are Finance Guru, a patient investing educator for complete beginners. Explain simply, avoid guarantees, and clearly distinguish education from personalized financial advice."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }).encode()
        req = urlrequest.Request(
            self.api_url, data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        )
        try:
            with urlrequest.urlopen(req, timeout=120) as response:
                payload = json.loads(response.read().decode())
            return payload["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise RuntimeError("Hosted LLM request failed.") from exc
