from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ClassInfo:
    name: str
    lineno: int
    end_lineno: int
    docstring: Optional[str] = None
    bases: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)


@dataclass
class FunctionInfo:
    name: str
    lineno: int
    end_lineno: int
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    params: list[str] = field(default_factory=list)
    return_annotation: Optional[str] = None


@dataclass
class ModuleInfo:
    name: str
    docstring: Optional[str] = None
    imports: list[str] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)


class CodeExtractor:
    SUPPORTED_EXTENSIONS: set[str] = {".py", ".js", ".jsx", ".ts", ".tsx"}

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root

    def _resolve(self, path: Path) -> Path:
        if self.project_root and not path.is_absolute():
            return self.project_root / path
        return path

    def extract(self, source_file: Path, language: Optional[str] = None) -> Optional[ModuleInfo]:
        source_file = self._resolve(source_file)
        if not source_file.exists():
            return None

        content = source_file.read_text(encoding="utf-8", errors="replace")

        if not language:
            language = self._detect_language(source_file)

        if language == "python":
            return self._extract_python(source_file, content)
        return self._extract_generic(source_file, content, language)

    def extract_classes(self, source_file: Path) -> list[ClassInfo]:
        module = self.extract(source_file)
        return module.classes if module else []

    def extract_functions(self, source_file: Path) -> list[FunctionInfo]:
        module = self.extract(source_file)
        return module.functions if module else []

    def extract_docstrings(self, source_file: Path) -> list[tuple[str, str, int]]:
        result: list[tuple[str, str, int]] = []
        module = self.extract(source_file)
        if not module:
            return result
        if module.docstring:
            result.append(("module", module.docstring, 0))
        for cls in module.classes:
            if cls.docstring:
                result.append(("class", cls.docstring, cls.lineno))
            for method in cls.methods:
                pass
        for func in module.functions:
            if func.docstring:
                result.append(("function", func.docstring, func.lineno))
        return result

    def detect_language(self, source_file: Path) -> str:
        return self._detect_language(source_file)

    def _detect_language(self, source_file: Path) -> str:
        ext = source_file.suffix.lower()
        mapping: dict[str, str] = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".vue": "vue",
            ".svelte": "svelte",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
        }
        return mapping.get(ext, "unknown")

    def _extract_python(self, source_file: Path, content: str) -> Optional[ModuleInfo]:
        try:
            tree = ast.parse(content, filename=str(source_file))
        except SyntaxError:
            return None

        module_docstring = ast.get_docstring(tree)
        module = ModuleInfo(
            name=source_file.stem,
            docstring=module_docstring,
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                for alias in node.names:
                    full = f"{module_name}.{alias.name}" if module_name else alias.name
                    module.imports.append(full)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._extract_python_class(node)
                module.classes.append(class_info)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_info = self._extract_python_function(node)
                module.functions.append(func_info)

        return module

    def _extract_python_class(self, node: ast.ClassDef) -> ClassInfo:
        bases: list[str] = []
        for base in node.bases:
            bases.append(ast.dump(base) if isinstance(base, ast.Name) else ast.unparse(base))

        methods: list[str] = []
        for item in ast.iter_child_nodes(node):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        decorators: list[str] = []
        for dec in node.decorator_list:
            decorators.append(ast.unparse(dec) if hasattr(ast, "unparse") else ast.dump(dec))

        return ClassInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            bases=bases,
            methods=methods,
            decorators=decorators,
        )

    def _extract_python_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
        params: list[str] = []
        for arg in node.args.args:
            params.append(arg.arg)

        return_annotation: Optional[str] = None
        if node.returns and hasattr(ast, "unparse"):
            return_annotation = ast.unparse(node.returns)

        decorators: list[str] = []
        for dec in node.decorator_list:
            decorators.append(ast.unparse(dec) if hasattr(ast, "unparse") else ast.dump(dec))

        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            params=params,
            return_annotation=return_annotation,
        )

    def _extract_generic(self, source_file: Path, content: str, language: str) -> Optional[ModuleInfo]:
        module = ModuleInfo(name=source_file.stem)

        class_pattern = re.compile(r"(?:export\s+)?(?:class|interface)\s+(\w+)")
        function_pattern = re.compile(r"(?:export\s+)?(?:function|const)\s+(\w+)\s*(?:[=(]|:)")
        import_pattern = re.compile(r"(?:import|require)\s+.*?from\s+['\"]([^'\"]+)['\"]")

        module.imports = import_pattern.findall(content)

        for match in class_pattern.finditer(content):
            line_no = content[:match.start()].count("\n") + 1
            module.classes.append(ClassInfo(name=match.group(1), lineno=line_no, end_lineno=line_no))

        for match in function_pattern.finditer(content):
            name = match.group(1)
            if name not in ("function", "const"):
                line_no = content[:match.start()].count("\n") + 1
                module.functions.append(FunctionInfo(name=name, lineno=line_no, end_lineno=line_no))

        docstring_pattern = re.compile(r'"""(.*?)"""|\'\'\'(.*?)\'\'\'|/\*\*(.*?)\*/|///(.*?)$', re.DOTALL | re.MULTILINE)
        doc_match = docstring_pattern.search(content)
        if doc_match:
            module.docstring = next(g for g in doc_match.groups() if g is not None).strip()

        return module
