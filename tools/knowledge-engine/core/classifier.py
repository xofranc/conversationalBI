from __future__ import annotations

import re
from enum import Enum
from pathlib import Path

from core.parser import GraphNode


class NodeType(str, Enum):
    MODEL = "Model"
    VIEW = "View"
    SERVICE = "Service"
    SERIALIZER = "Serializer"
    TEST = "Test"
    REPOSITORY = "Repository"
    FRONTEND = "Frontend"
    CONFIG = "Config"
    MIGRATION = "Migration"
    ADMIN = "Admin"
    URL = "URL"
    APP = "App"
    PERMISSION = "Permission"
    MIDDLEWARE = "Middleware"
    SIGNAL = "Signal"
    VALIDATOR = "Validator"
    UTILITY = "Utility"
    COMMAND = "Command"
    SCHEMA = "Schema"
    TASK = "Task"
    MODULE = "Module"
    FUNCTION = "Function"
    CLASS = "Class"
    UNKNOWN = "Unknown"


_FILE_TYPE_PATTERNS: list[tuple[re.Pattern, NodeType]] = [
    (re.compile(r"/models\.py$|/models/"), NodeType.MODEL),
    (re.compile(r"/views\.py$|/views/"), NodeType.VIEW),
    (re.compile(r"/services\.py$|/services/"), NodeType.SERVICE),
    (re.compile(r"/serializers\.py$|/serializers/"), NodeType.SERIALIZER),
    (re.compile(r"/tests?\.py$|/tests/|test_"), NodeType.TEST),
    (re.compile(r"/repositor"), NodeType.REPOSITORY),
    (re.compile(r"/admin\.py$"), NodeType.ADMIN),
    (re.compile(r"/urls\.py$"), NodeType.URL),
    (re.compile(r"/apps\.py$"), NodeType.APP),
    (re.compile(r"/permissions\.py$"), NodeType.PERMISSION),
    (re.compile(r"/middleware"), NodeType.MIDDLEWARE),
    (re.compile(r"/signals\.py$"), NodeType.SIGNAL),
    (re.compile(r"/validators\.py$"), NodeType.VALIDATOR),
    (re.compile(r"/management/commands/"), NodeType.COMMAND),
    (re.compile(r"/schemas?\.py$"), NodeType.SCHEMA),
    (re.compile(r"/tasks\.py$"), NodeType.TASK),
    (re.compile(r"/migrations/"), NodeType.MIGRATION),
    (re.compile(r"/config/|/settings\.py$"), NodeType.CONFIG),
]

_FRONTEND_PATTERNS: list[re.Pattern] = [
    re.compile(r"frontend/|/src/"),
    re.compile(r"\.(js|jsx|ts|tsx|vue|svelte)$"),
]

_FUNCTION_OR_CLASS_PATTERNS: list[re.Pattern] = [
    re.compile(r"[A-Z][a-zA-Z]+\(\)"),  # ClassName()
    re.compile(r"^[a-z_][a-zA-Z_]+\(\)$"),  # function_name()
]


class Classifier:
    def classify(self, node: GraphNode) -> NodeType:
        source_file = node.source_file or ""
        label = node.label or ""
        norm_label = node.norm_label or ""

        if node.is_file_node or not source_file:
            return self._classify_file(source_file, label, norm_label)
        return self._classify_symbol(source_file, label, norm_label)

    def classify_path(self, path: str) -> NodeType:
        return self._classify_file(path, Path(path).stem, Path(path).stem)

    def _classify_file(self, source_file: str, label: str, norm_label: str) -> NodeType:
        for pattern, node_type in _FILE_TYPE_PATTERNS:
            if pattern.search(source_file):
                return node_type

        for pattern in _FRONTEND_PATTERNS:
            if pattern.search(source_file):
                return NodeType.FRONTEND

        if source_file.endswith(".py"):
            return NodeType.MODULE

        if any(source_file.endswith(ext) for ext in (".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte")):
            return NodeType.FRONTEND

        return NodeType.UNKNOWN

    def _classify_symbol(self, source_file: str, label: str, norm_label: str) -> NodeType:
        for pattern, node_type in _FILE_TYPE_PATTERNS:
            if pattern.search(source_file):
                return node_type

        if re.match(r"^[A-Z]", label):
            return NodeType.CLASS
        if re.match(r"^[a-z_]", label):
            return NodeType.FUNCTION

        return NodeType.UNKNOWN
