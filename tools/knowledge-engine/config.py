from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    project_root: Path = Path.cwd()
    graph_path: Path = Path.cwd() / "graphify-out" / "graph.json"
    manifest_path: Path = Path.cwd() / "graphify-out" / "manifest.json"
    output_dir: Path = Path.cwd() / "knowledge-out"

    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    llm_api_key: Optional[str] = None
    llm_api_base: Optional[str] = None
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    render_markdown: bool = True
    render_mermaid: bool = True
    render_obsidian: bool = True
    render_html: bool = False

    obsidian_vault: Optional[Path] = None

    include_patterns: list[str] = field(default_factory=lambda: ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"])
    exclude_patterns: list[str] = field(default_factory=lambda: ["*migrations*", "node_modules", ".venv", "__pycache__"])

    verbose: bool = False

    @property
    def nodes_dir(self) -> Path:
        return self.output_dir / "nodes"

    @property
    def architecture_dir(self) -> Path:
        return self.output_dir / "architecture"

    @property
    def cache_dir(self) -> Path:
        return self.output_dir / "cache"

    @classmethod
    def from_env(cls) -> Config:
        api_key = os.getenv("KE_LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        provider = os.getenv("KE_LLM_PROVIDER", "")
        if not provider and api_key:
            prefix = api_key[:8] if api_key else ""
            if prefix.startswith("sk-ant"):
                provider = "anthropic"
            elif prefix.startswith("sk-"):
                provider = "openai"
        return cls(
            llm_provider=provider or os.getenv("KE_LLM_PROVIDER", "openai"),
            llm_model=os.getenv("KE_LLM_MODEL", "claude-sonnet-4-20250514" if provider == "anthropic" else "gpt-4o"),
            llm_api_key=api_key,
            llm_api_base=os.getenv("KE_LLM_API_BASE"),
            llm_temperature=float(os.getenv("KE_LLM_TEMPERATURE", "0.1")),
            llm_max_tokens=int(os.getenv("KE_LLM_MAX_TOKENS", "4096")),
            verbose=os.getenv("KE_VERBOSE", "false").lower() == "true",
        )

    def ensure_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.nodes_dir.mkdir(parents=True, exist_ok=True)
        self.architecture_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
