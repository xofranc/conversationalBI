from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.cache import KnowledgeCache
from core.classifier import Classifier, NodeType
from core.context import ContextBuilder
from core.extractor import CodeExtractor, ModuleInfo
from core.graph import GraphAnalyzer
from core.llm import LLMConfig, LLMFactory, LLMProvider, LLMResponse
from core.parser import Graph, GraphNode


@dataclass
class KnowledgeObject:
    id: str = ""
    type: str = ""
    name: str = ""
    summary: str = ""
    purpose: str = ""
    responsibilities: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    used_by: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    called_from: list[str] = field(default_factory=list)
    source_file: str = ""
    language: str = ""
    tags: list[str] = field(default_factory=list)
    architecture_notes: str = ""
    improvements: list[str] = field(default_factory=list)
    code_hash: str = ""
    last_updated: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeObject:
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            name=data.get("name", ""),
            summary=data.get("summary", ""),
            purpose=data.get("purpose", ""),
            responsibilities=data.get("responsibilities", []),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            dependencies=data.get("dependencies", []),
            used_by=data.get("used_by", []),
            calls=data.get("calls", []),
            called_from=data.get("called_from", []),
            source_file=data.get("source_file", ""),
            language=data.get("language", ""),
            tags=data.get("tags", []),
            architecture_notes=data.get("architecture_notes", ""),
            improvements=data.get("improvements", []),
            code_hash=data.get("code_hash", ""),
            last_updated=data.get("last_updated", ""),
            raw=data.get("raw", data),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("raw", None)
        return data

    def to_serializable(self) -> dict[str, Any]:
        return self.to_dict()


class KnowledgeEngine:
    def __init__(
        self,
        graph: Graph,
        analyzer: GraphAnalyzer,
        classifier: Classifier,
        extractor: CodeExtractor,
        cache: KnowledgeCache,
        context_builder: ContextBuilder,
        llm_provider: Optional[LLMProvider] = None,
        project_root: Optional[Path] = None,
    ) -> None:
        self.graph = graph
        self.analyzer = analyzer
        self.classifier = classifier
        self.extractor = extractor
        self.cache = cache
        self.context_builder = context_builder
        self.llm_provider = llm_provider
        self.project_root = project_root

    def _resolve(self, path: Path) -> Path:
        if self.project_root and not path.is_absolute():
            return (self.project_root / path).resolve()
        return path.resolve() if not path.is_absolute() else path

    def process_node(self, node: GraphNode, use_llm: bool = True) -> KnowledgeObject:
        source_path = Path(node.source_file) if node.source_file else None
        resolved_path = self._resolve(source_path) if source_path else None
        cached = self.cache.get_cached(node.source_file)
        current_hash = self.cache.hash_file(resolved_path) if resolved_path else ""

        if cached and not self.cache.is_changed(node.source_file, current_hash or ""):
            ko = KnowledgeObject.from_dict(cached)
            ko.code_hash = current_hash or ""
            if use_llm and self.llm_provider and node.source_file and not ko.summary:
                module_info = None
                if resolved_path:
                    module_info = self.extractor.extract(resolved_path)
                ko = self._enrich_with_llm(node, ko, module_info)
                if node.source_file:
                    self.cache.set_cached(node.source_file, current_hash or "", ko.to_serializable())
            return ko

        module_info = None
        if resolved_path:
            module_info = self.extractor.extract(resolved_path)

        ko = self._build_base_knowledge(node, module_info, current_hash or "")

        ko = self._enrich_with_graph(node, ko)

        if use_llm and self.llm_provider and node.source_file:
            ko = self._enrich_with_llm(node, ko, module_info)

        if node.source_file:
            self.cache.set_cached(node.source_file, current_hash or "", ko.to_serializable())

        return ko

    def process_all(self, use_llm: bool = True, max_workers: int = 1) -> list[KnowledgeObject]:
        file_nodes = [n for n in self.graph.get_file_nodes() if n.source_file]
        if max_workers <= 1 or not use_llm:
            results: list[KnowledgeObject] = []
            for node in file_nodes:
                ko = self.process_node(node, use_llm=use_llm)
                results.append(ko)
            return results
        return self._process_concurrent(file_nodes, use_llm=use_llm, max_workers=max_workers)

    def _process_concurrent(self, nodes: list[GraphNode], use_llm: bool, max_workers: int = 5) -> list[KnowledgeObject]:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        results: list[KnowledgeObject] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.process_node, n, use_llm): n for n in nodes}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    node = futures[future]
                    print(f"[KE] Error processing {node.label}: {e}")
        return results

    def process_community(self, community_id: int, use_llm: bool = True) -> list[KnowledgeObject]:
        results: list[KnowledgeObject] = []
        nodes = self.analyzer.get_community_nodes(community_id)
        for node in nodes:
            if node.is_file_node and node.source_file:
                ko = self.process_node(node, use_llm=use_llm)
                results.append(ko)
        return results

    def process_changed(self, use_llm: bool = True) -> list[KnowledgeObject]:
        results: list[KnowledgeObject] = []
        file_nodes = self.graph.get_file_nodes()
        for node in file_nodes:
            if not node.source_file:
                continue
            source_path = self._resolve(Path(node.source_file))
            current_hash = self.cache.hash_file(source_path) or ""
            if self.cache.is_changed(node.source_file, current_hash):
                ko = self.process_node(node, use_llm=use_llm)
                results.append(ko)
        return results

    def _build_base_knowledge(self, node: GraphNode, module_info: Optional[ModuleInfo], code_hash: str) -> KnowledgeObject:
        node_type = self.classifier.classify(node).value

        ko = KnowledgeObject(
            id=node.id,
            type=node_type,
            name=node.label,
            source_file=node.source_file or "",
            code_hash=code_hash,
            last_updated=datetime.now().isoformat(),
            raw=node.raw,
        )

        if node.source_file:
            lang = self.extractor.detect_language(self._resolve(Path(node.source_file)))
            ko.language = lang

        if module_info:
            if module_info.docstring:
                ko.summary = module_info.docstring[:300]
            ko.tags = [node_type.lower()]
            if module_info.classes:
                ko.tags.extend(c.name.lower() for c in module_info.classes[:5])

        return ko

    def _enrich_with_graph(self, node: GraphNode, ko: KnowledgeObject) -> KnowledgeObject:
        deps = self.analyzer.get_dependencies(node.id)
        ko.dependencies = [d.label for d in deps]

        dependents = self.analyzer.get_dependents(node.id)
        ko.used_by = [d.label for d in dependents]

        calls = self.analyzer.get_calls(node.id)
        ko.calls = []
        for c in calls:
            target = self.graph.get_node(c.target)
            if target:
                ko.calls.append(target.label)

        callers = self.analyzer.get_callers(node.id)
        ko.called_from = []
        for c in callers:
            source = self.graph.get_node(c.source)
            if source:
                ko.called_from.append(source.label)

        return ko

    def _enrich_with_llm(self, node: GraphNode, ko: KnowledgeObject, module_info: Optional[ModuleInfo]) -> KnowledgeObject:
        prompt = self.context_builder.build_llm_enrichment_prompt(node, module_info)

        response = self.llm_provider.complete_json(prompt) if self.llm_provider else LLMResponse(content="")

        if response.parsed:
            parsed = response.parsed
            ko.summary = parsed.get("summary", ko.summary)
            ko.purpose = parsed.get("purpose", ko.purpose)
            ko.responsibilities = parsed.get("responsibilities", ko.responsibilities)
            ko.inputs = parsed.get("inputs", ko.inputs)
            ko.outputs = parsed.get("outputs", ko.outputs)
            ko.architecture_notes = parsed.get("architecture_notes", ko.architecture_notes)
            ko.improvements = parsed.get("improvements", ko.improvements)

        return ko

    def save_knowledge_object(self, ko: KnowledgeObject, output_dir: Path) -> Path:
        node_dir = output_dir / "nodes"
        node_dir.mkdir(parents=True, exist_ok=True)
        safe_name = ko.id.replace("/", "_").replace("\\", "_")
        file_path = node_dir / f"{safe_name}.json"
        file_path.write_text(json.dumps(ko.to_serializable(), indent=2, default=str))
        return file_path

    def load_knowledge_object(self, file_path: Path) -> Optional[KnowledgeObject]:
        if not file_path.exists():
            return None
        try:
            data = json.loads(file_path.read_text())
            return KnowledgeObject.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return None

    def get_architecture_knowledge(self) -> list[KnowledgeObject]:
        communities = self.graph.get_communities()
        results: list[KnowledgeObject] = []
        for comm_id, nodes in communities.items():
            file_nodes = [n for n in nodes if n.is_file_node and n.source_file]
            if not file_nodes:
                continue
            types: dict[str, int] = {}
            for n in nodes:
                t = self.classifier.classify(n).value
                types[t] = types.get(t, 0) + 1

            ko = KnowledgeObject(
                id=f"community_{comm_id}" if comm_id is not None else "community_none",
                type="Architecture",
                name=f"Community {comm_id}" if comm_id is not None else "Unclassified",
                summary=f"Community with {len(nodes)} nodes across {len(file_nodes)} files",
                tags=list(types.keys()),
                dependencies=[n.label for n in file_nodes[:20]],
                architecture_notes=f"Composition: {types}",
            )
            results.append(ko)
        return results
