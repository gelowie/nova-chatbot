#!/usr/bin/env python3
"""Check that Nova's files agree with each other.

    python .github/scripts/check_repo.py              offline checks (paths, links, badges, HTML, Python, Java, JSON, YAML)
    python .github/scripts/check_repo.py --external   http(s) links only (needs a network)

Standard library only. The YAML checks use PyYAML when it is installed.
Exit status is 1 when any error is found; warnings never fail the run.
"""
from __future__ import annotations

import argparse
import ast
import glob
import html.parser
import json
import os
import posixpath
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = "gelowie/nova-chatbot"
SKIP_DIRS = {".git", "__pycache__", "node_modules", "out"}
KEEP_UNREFERENCED = {"docs/img/social-preview.png"}
SKIP_EXTERNAL = ("/security/advisories/new", "localhost", "127.0.0.1", "0.0.0.0", "example.com", "w3.org/")
FORBIDDEN_TRACKED = (".pyc", ".class", ".DS_Store")
BADGE_NAMES = ("version", "license", "runtime", "dependencies")
TEXT_SUFFIXES = {".md", ".py", ".java", ".html", ".json", ".yml", ".yaml", ".svg", ".txt"}

LINK = re.compile(r"\]\(\s*<?([^)\s>]+)")
REF_DEFINITION = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)")
HTML_REF = re.compile(r"""\b(?:src|href)\s*=\s*["']([^"']+)["']""")
MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(")
HTML_IMG = re.compile(r"<img\b[^>]*>", re.I)
INLINE_CODE = re.compile(r"`[^`\n]*`")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)
OWN_URL = re.compile(rf"^https://github\.com/{REPO}/(?:blob|tree|raw)/(?:refs/heads/)?main(?:/([^#?]*))?", re.I)
OWN_URL_ANYWHERE = re.compile(rf"https://github\.com/{REPO}/(?:blob|tree|raw)/main(?:/[^\s)\"'<>]*)?", re.I)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, path: object, line: int | None, message: str) -> None:
        self._add(self.errors, "error", path, line, message)

    def warn(self, path: object, line: int | None, message: str) -> None:
        self._add(self.warnings, "warning", path, line, message)

    def _add(self, bucket: list[str], level: str, path: object, line: int | None, message: str) -> None:
        where = f"{path}:{line}" if line else str(path)
        bucket.append(f"{where}: {message}")
        if os.environ.get("GITHUB_ACTIONS"):
            location = f"file={path}" + (f",line={line}" if line else "")
            print(f"::{level} {location}::{message}")
        else:
            print(f"{level.upper():7} {where}: {message}")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def repo_files() -> list[Path]:
    found: list[Path] = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        found.extend(Path(base, name) for name in sorted(names))
    return found


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def exists_exact(path: Path) -> bool:
    """True only when every part of the path matches the on-disk letter case."""
    try:
        parts = path.resolve().relative_to(ROOT).parts
    except ValueError:
        return False
    current = ROOT
    for part in parts:
        if part not in os.listdir(current):
            return False
        current = current / part
    return True


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


class Project:
    """Everything the checks compare files against, gathered once."""

    def __init__(self, report: Report) -> None:
        self.report = report
        self.files = repo_files()
        self.referenced: set[str] = set()
        self.checked: Counter[str] = Counter()
        self.server = None
        self._slugs: dict[Path, set[str]] = {}
        self.brain = self._load_brain()

    def _load_brain(self) -> dict | None:
        path = ROOT / "src" / "json" / "brain.json"
        try:
            return json.loads(read(path))
        except (OSError, ValueError) as err:
            self.report.error(rel(path), None, f"cannot load the brain: {err}")
            return None

    def by_suffix(self, *suffixes: str) -> list[Path]:
        return [f for f in self.files if f.suffix in suffixes]

    def heading_slugs(self, md: Path) -> set[str]:
        if md not in self._slugs:
            seen: Counter[str] = Counter()
            slugs: set[str] = set()
            for _, line in prose_lines(read(md)):
                match = HEADING.match(line)
                if not match:
                    continue
                slug = slugify(match.group(2))
                slugs.add(slug if not seen[slug] else f"{slug}-{seen[slug]}")
                seen[slug] += 1
            self._slugs[md] = slugs
        return self._slugs[md]


def prose_lines(text: str):
    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        elif not in_fence:
            yield number, line


def slugify(title: str) -> str:
    title = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", title)
    title = re.sub(r"[`*~]", "", title).lower()
    return re.sub(r"[^\w\- ]", "", title).replace(" ", "-")


def resolve(source: Path, target: str) -> tuple[Path, str] | None:
    """Destination and anchor of a local link, or None when the link is external."""
    own = OWN_URL.match(target)
    if own:
        return ROOT / urllib.parse.unquote(own.group(1) or ""), target.partition("#")[2]
    if SCHEME.match(target):
        return None
    path, _, anchor = target.partition("#")
    path = urllib.parse.unquote(path.partition("?")[0])
    if not path:
        return source, anchor
    base = ROOT if path.startswith("/") else source.parent
    return base / path.lstrip("/"), anchor


def check_target(project: Project, source: Path, line: int, target: str) -> None:
    resolved = resolve(source, target)
    if resolved is None:
        return
    project.checked["local links"] += 1
    dest, anchor = resolved
    where = rel(source)
    if not dest.exists():
        project.report.error(where, line, f"broken link, no such file: {target}")
        return
    if not exists_exact(dest):
        project.report.error(where, line, f"letter case does not match the file on disk: {target}")
        return
    project.referenced.add(rel(dest))
    anchor = urllib.parse.unquote(anchor).lower()
    if anchor and anchor != "top" and dest.suffix == ".md" and anchor not in project.heading_slugs(dest):
        project.report.error(where, line, f"no heading for anchor #{anchor} in {rel(dest)}")


def check_markdown(project: Project) -> None:
    for md in project.by_suffix(".md"):
        where = rel(md)
        project.checked["Markdown files"] += 1
        for number, raw in prose_lines(read(md)):
            line = INLINE_CODE.sub("", raw)
            targets = [m.group(1) for m in LINK.finditer(line)]
            targets += [m.group(1) for m in HTML_REF.finditer(line)]
            if (definition := REF_DEFINITION.match(line)):
                targets.append(definition.group(1))
            for target in targets:
                check_target(project, md, number, target)
            for image in MD_IMAGE.finditer(line):
                if not image.group(1).strip():
                    project.report.error(where, number, "image without alt text")
            for tag in HTML_IMG.findall(line):
                if not re.search(r"""\balt\s*=\s*["'][^"']+["']""", tag):
                    project.report.error(where, number, "<img> without alt text")


def check_own_urls(project: Project) -> None:
    """Absolute links to this repo's files, outside Markdown (issue forms, templates)."""
    for path in project.files:
        if path.suffix not in TEXT_SUFFIXES - {".md"}:
            continue
        text = read(path)
        for match in OWN_URL_ANYWHERE.finditer(text):
            check_target(project, path, line_of(text, match.start()), match.group(0))


def check_text_files(project: Project) -> None:
    for path in project.files:
        if path.suffix in TEXT_SUFFIXES:
            try:
                read(path)
            except UnicodeDecodeError as err:
                project.report.error(rel(path), None, f"not valid UTF-8: {err.reason}")
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    if tracked.returncode == 0:
        for name in tracked.stdout.splitlines():
            if name.endswith(FORBIDDEN_TRACKED) or "__pycache__/" in name:
                project.report.error(name, None, "build or system file should not be committed")


def count_tests() -> int:
    total = 0
    tests = ROOT / "tests"
    for path in tests.glob("test_*.py"):
        for node in ast.walk(ast.parse(read(path))):
            if isinstance(node, ast.ClassDef):
                total += sum(isinstance(f, ast.FunctionDef) and f.name.startswith("test") for f in node.body)
    return total


def python_minimum() -> str | None:
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    if not workflow.exists():
        return None
    match = re.search(r"python-version:\s*\[([^\]]+)\]", read(workflow))
    versions = re.findall(r"(\d+)\.(\d+)", match.group(1)) if match else []
    return "{}.{}".format(*min(versions, key=lambda v: (int(v[0]), int(v[1])))) if versions else None


def third_party_imports(project: Project) -> set[str]:
    local = {"src", "server", "tests"}
    found: set[str] = set()
    for path in project.by_suffix(".py"):
        if ".github" in path.relative_to(ROOT).parts:
            continue
        for node in ast.walk(ast.parse(read(path))):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            found.update(n.split(".")[0] for n in names)
    return {n for n in found if n not in sys.stdlib_module_names and n not in local}


def check_facts(project: Project) -> None:
    report, brain = project.report, project.brain
    if brain is None:
        return
    intents = brain["intents"]
    counts = {
        "intents": len(intents),
        "patterns": sum(len(i["patterns"]) for i in intents),
        "replies": sum(len(i["responses"]) for i in intents),
        "phrase fixes": len(brain["phraseFixes"]),
        "typo fixes": len(brain["typos"]),
        "tests": count_tests(),
    }
    version = str(brain["meta"]["version"])

    changelog = ROOT / "CHANGELOG.md"
    if changelog.exists():
        headings = [v for v in re.findall(r"^## \[([^\]]+)\]", read(changelog), re.M) if v.lower() != "unreleased"]
        if headings and headings[0] != version:
            report.error("CHANGELOG.md", None, f"latest release is {headings[0]} but brain.json says {version}")

    readme = ROOT / "README.md"
    text = read(readme)
    row = re.search(r"\|\s*Version\s*\|\s*([^|]+?)\s*\|", text)
    if row and row.group(1) != version:
        report.error("README.md", line_of(text, row.start()), f"version {row.group(1)} but brain.json says {version}")

    stats = re.search(r"(\d+) intents · (\d+) patterns · (\d+) replies · (\d+) phrase fixes · (\d+) typo fixes", text)
    if stats:
        written = dict(zip(["intents", "patterns", "replies", "phrase fixes", "typo fixes"], map(int, stats.groups())))
        for name, value in written.items():
            if value != counts[name]:
                report.error("README.md", line_of(text, stats.start()), f"README says {value} {name}, brain.json has {counts[name]}")
    for match in re.finditer(r"\b(\d+) topics\b", text):
        if int(match.group(1)) != counts["intents"]:
            report.error("README.md", line_of(text, match.start()), f"README says {match.group(1)} topics, brain.json has {counts['intents']}")
    tests = re.search(r"\|\s*Tests\s*\|\s*(\d+)", text)
    if tests and int(tests.group(1)) != counts["tests"]:
        report.error("README.md", line_of(text, tests.start()), f"README says {tests.group(1)} tests, found {counts['tests']}")
    engine = ROOT / "src" / "py" / "engine.py"
    threshold = re.search(r"_MATCH_THRESHOLD\s*=\s*([\d.]+)", read(engine)) if engine.exists() else None
    written_threshold = re.search(r"\|\s*Match threshold\s*\|\s*([\d.]+)", text)
    if threshold and written_threshold and threshold.group(1) != written_threshold.group(1):
        report.error("README.md", line_of(text, written_threshold.start()),
                     f"README says threshold {written_threshold.group(1)}, engine.py uses {threshold.group(1)}")

    for translation in sorted((ROOT / "docs" / "readme").glob("*.md")):
        body = read(translation)
        if not re.search(rf"(?<!\d){counts['intents']}(?!\d)", body):
            report.error(rel(translation), None, f"does not state the current topic count ({counts['intents']})")
        if threshold and not re.search(rf"(?<!\d){re.escape(threshold.group(1)).replace(chr(92) + '.', '[.,]')}(?!\d)", body):
            report.error(rel(translation), None, f"does not state the current match threshold ({threshold.group(1)})")

    project.facts = {
        "version": version,
        "license": (read(ROOT / "LICENSE").splitlines() or [""])[0].replace(" License", "").strip() if (ROOT / "LICENSE").exists() else None,
        "runtime": f"Python {python_minimum()}+" if python_minimum() else None,
        "dependencies": "none" if not third_party_imports(project) and not any(
            (ROOT / name).exists() for name in ("requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "package.json")
        ) else "some",
    }


def check_badges(project: Project) -> None:
    report = project.report
    facts = getattr(project, "facts", None)
    if not facts:
        return
    pages = [ROOT / "README.md", *sorted((ROOT / "docs" / "readme").glob("*.md"))]
    svg_labels: dict[Path, str | None] = {}
    patterns = (
        re.compile(r"""<img\s+[^>]*src=["']([^"']*badges/([\w-]+)\.svg)["'][^>]*alt=["']([^"']*)["']"""),
        re.compile(r"""!\[([^\]]*)\]\(([^)\s]*badges/([\w-]+)\.svg)"""),
    )
    for page in pages:
        text = read(page)
        for pattern in patterns:
            for match in pattern.finditer(text):
                if pattern is patterns[0]:
                    src, name, alt = match.groups()
                else:
                    alt, src, name = match.groups()
                line, where = line_of(text, match.start()), rel(page)
                if name not in BADGE_NAMES:
                    report.warn(where, line, f"badge '{name}' is not checked against project facts")
                    continue
                expected = f"{name}: {facts[name]}" if facts.get(name) else None
                if expected and alt != expected:
                    report.error(where, line, f"badge alt text is '{alt}' but the project says '{expected}'")
                svg = (page.parent / src).resolve()
                project.checked["badges"] += 1
                if svg.exists() and svg not in svg_labels:
                    try:
                        svg_labels[svg] = ET.parse(svg).getroot().get("aria-label")
                    except ET.ParseError as err:
                        report.error(rel(svg), None, f"badge is not valid SVG: {err}")
                        svg_labels[svg] = None
                    label = svg_labels[svg]
                    if expected and label is not None and label != expected:
                        report.error(rel(svg), None, f"badge says '{label}' but the project says '{expected}'")


class PageParser(html.parser.HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
    OPTIONAL_END = {"p", "li", "dt", "dd", "tr", "td", "th", "option", "thead", "tbody", "tfoot"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int]] = []
        self.problems: list[tuple[int, str]] = []
        self.ids: dict[str, int] = {}
        self.refs: list[tuple[int, str]] = []
        self.scripts: list[tuple[int, str]] = []
        self.styles: list[tuple[int, str]] = []
        self.doctype = False
        self.lang = False
        self.charset = False
        self.viewport = False
        self.title = ""
        self._capture: tuple[str, int, list[str]] | None = None

    def handle_decl(self, decl: str) -> None:
        self.doctype = self.doctype or decl.lower().startswith("doctype html")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line = self.getpos()[0]
        values = {k: (v or "") for k, v in attrs}
        if tag == "html" and values.get("lang"):
            self.lang = True
        if tag == "meta":
            self.charset = self.charset or "charset" in values
            self.viewport = self.viewport or values.get("name") == "viewport"
        if "id" in values:
            if values["id"] in self.ids:
                self.problems.append((line, f"duplicate id '{values['id']}' (first used on line {self.ids[values['id']]})"))
            self.ids.setdefault(values["id"], line)
        for key in ("src", "href"):
            if values.get(key):
                self.refs.append((line, values[key]))
        if tag == "img" and not values.get("alt", "").strip():
            self.problems.append((line, "<img> without alt text"))
        if tag in self.VOID:
            return
        self.stack.append((tag, line))
        if tag in ("script", "style") and not values.get("src"):
            self._capture = (tag, line, [])
        elif tag == "title":
            self._capture = (tag, line, [])

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
            self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._capture[2].append(data)

    def handle_endtag(self, tag: str) -> None:
        line = self.getpos()[0]
        if self._capture and self._capture[0] == tag:
            kind, start, chunks = self._capture
            body = "".join(chunks)
            if kind == "script":
                self.scripts.append((start, body))
            elif kind == "style":
                self.styles.append((start, body))
            else:
                self.title = body.strip()
            self._capture = None
        open_tags = [t for t, _ in self.stack]
        if tag not in open_tags:
            self.problems.append((line, f"</{tag}> has no matching opening tag"))
            return
        while self.stack[-1][0] != tag:
            name, opened = self.stack.pop()
            if name not in self.OPTIONAL_END:
                self.problems.append((opened, f"<{name}> is never closed"))
        self.stack.pop()

    def finish(self) -> None:
        for name, opened in self.stack:
            if name not in self.OPTIONAL_END:
                self.problems.append((opened, f"<{name}> is never closed"))


def check_html(project: Project) -> None:
    report = project.report
    node = shutil.which("node")
    for page in project.by_suffix(".html"):
        where = rel(page)
        project.checked["HTML pages"] += 1
        parser = PageParser()
        parser.feed(read(page))
        parser.close()
        parser.finish()
        for line, message in parser.problems:
            report.error(where, line, message)
        for ok, message in ((parser.doctype, "missing <!doctype html>"), (parser.lang, "<html> has no lang attribute"),
                            (parser.charset, "missing <meta charset>"), (parser.viewport, "missing viewport meta tag"),
                            (bool(parser.title), "missing or empty <title>")):
            if not ok:
                report.error(where, None, message)

        served = getattr(project.server, "STATIC_FILES", None) if project.server else None
        assets = list(parser.refs)
        for start, body in parser.scripts:
            for match in re.finditer(r"""["'](\.{1,2}/[^"']+\.(?:png|jpe?g|svg|gif|webp|ico|css|js|json))["']""", body):
                assets.append((start + body.count("\n", 0, match.start()), match.group(1)))
            for match in re.finditer(r"""\$\(\s*["']([\w-]+)["']\s*\)|getElementById\(\s*["']([\w-]+)["']\s*\)""", body):
                wanted = match.group(1) or match.group(2)
                if wanted not in parser.ids:
                    report.error(where, start + body.count("\n", 0, match.start()), f"script looks up #{wanted} but no element has that id")
        for start, body in parser.styles:
            for match in re.finditer(r"url\(\s*[\"']?([^)\"']+)", body):
                assets.append((start + body.count("\n", 0, match.start()), match.group(1)))
            plain = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
            if plain.count("{") != plain.count("}"):
                report.error(where, start, "CSS braces are not balanced")
        for line, ref in assets:
            if ref.startswith("#") or SCHEME.match(ref) or ref.startswith("//"):
                continue
            dest = (page.parent / urllib.parse.unquote(ref.partition("#")[0].partition("?")[0])).resolve()
            if not dest.exists():
                report.error(where, line, f"broken path: {ref}")
                continue
            if not exists_exact(dest):
                report.error(where, line, f"letter case does not match the file on disk: {ref}")
                continue
            project.referenced.add(rel(dest))
            if served is not None and dest.suffix not in (".html", ".md"):
                url = posixpath.normpath(posixpath.join("/", ref))
                if url not in served:
                    report.error(where, line, f"{ref} resolves to {url}, which server.py does not serve")

        if node is None:
            report.warn(where, None, "node not found, JavaScript syntax was not checked")
            continue
        for start, body in parser.scripts:
            project.checked["inline scripts"] += 1
            with tempfile.TemporaryDirectory() as tmp:
                script = Path(tmp, "inline.js")
                script.write_text(body, encoding="utf-8")
                result = subprocess.run([node, "--check", str(script)], capture_output=True, text=True)
            if result.returncode:
                lines = result.stderr.splitlines()
                at = re.search(r"inline\.js:(\d+)", result.stderr)
                reason = next((l for l in lines if "Error" in l), "syntax error")
                report.error(where, start + int(at.group(1)) - 1 if at else start, f"JavaScript: {reason}")


def check_python(project: Project) -> None:
    report = project.report
    for path in project.by_suffix(".py"):
        project.checked["Python files"] += 1
        try:
            compile(read(path), str(path), "exec")
        except SyntaxError as err:
            report.error(rel(path), err.lineno, f"syntax error: {err.msg}")
    for name in sorted(third_party_imports(project)):
        report.error("src/", None, f"imports '{name}', which is not in the standard library (Nova has no dependencies)")

    sys.path.insert(0, str(ROOT))
    try:
        import server
        project.server = server
    except Exception as err:
        report.error("server.py", None, f"cannot be imported: {type(err).__name__}: {err}")
        return
    finally:
        sys.path.pop(0)
    for label in ("BRAIN_PATH", "FRONTEND"):
        value = getattr(server, label, None)
        if value is None or not Path(value).exists():
            report.error("server.py", None, f"{label} points to a file that does not exist: {value}")
    for url, (path, _) in getattr(server, "STATIC_FILES", {}).items():
        if not Path(path).exists():
            report.error("server.py", None, f"static file {url} points to a missing file: {rel(Path(path))}")
        else:
            project.referenced.add(rel(Path(path)))
    try:
        reply = server.engine.respond("whats 5 plus 3 times 2")
        if reply.get("skill") != "math":
            report.error("src/py/engine.py", None, f"'whats 5 plus 3 times 2' was answered by '{reply.get('skill')}', not the math skill")
    except Exception as err:
        report.error("src/py/engine.py", None, f"engine failed on a simple message: {type(err).__name__}: {err}")


def javac_command() -> list[str] | None:
    if shutil.which("javac"):
        return ["javac"]
    if shutil.which("java"):
        probe = subprocess.run(["java", "--describe-module", "jdk.compiler"], capture_output=True)
        if probe.returncode == 0:
            return ["java", "-m", "jdk.compiler/com.sun.tools.javac.Main"]
    return None


def check_java(project: Project) -> None:
    report = project.report
    sources = sorted((ROOT / "src" / "java").glob("*.java"))
    for path in sources:
        text = read(path)
        if not re.search(r"^package\s+nova\s*;", text, re.M):
            report.error(rel(path), None, "missing 'package nova;'")
        public = re.search(r"^public\s+(?:final\s+|abstract\s+)*(?:class|interface|record|enum)\s+(\w+)", text, re.M)
        if public and public.group(1) != path.stem:
            report.error(rel(path), line_of(text, public.start()), f"public type {public.group(1)} must be in {public.group(1)}.java")
    command = javac_command()
    if not sources:
        return
    if command is None:
        report.warn("src/java", None, "no Java compiler found, compilation was not checked")
        return
    with tempfile.TemporaryDirectory() as out:
        result = subprocess.run([*command, "-encoding", "UTF-8", "-Xlint:all", "-d", out, *map(str, sources)],
                                capture_output=True, text=True)
    project.checked["Java files compiled"] += len(sources)
    found = False
    for match in re.finditer(r"^(.+\.java):(\d+): (error|warning): (.*)$", result.stderr, re.M):
        found = True
        path, line, level, message = match.groups()
        (report.error if level == "error" else report.warn)(rel(Path(path)), int(line), f"javac: {message}")
    if result.returncode and not found:
        report.error("src/java", None, f"javac failed: {result.stderr.strip()[:200]}")


def check_json(project: Project) -> None:
    report = project.report
    for path in project.by_suffix(".json"):
        project.checked["JSON files"] += 1
        try:
            json.loads(read(path))
        except ValueError as err:
            report.error(rel(path), getattr(err, "lineno", None), f"invalid JSON: {err}")
    brain = project.brain
    if brain is None:
        return
    where = "src/json/brain.json"
    meta = brain.get("meta", {})
    for key in ("version", "fallbacks", "unknownSuggestions"):
        if key not in meta:
            report.error(where, None, f"meta.{key} is missing")
    if not all(isinstance(m, str) and m.strip() for m in meta.get("fallbacks", [])) or not meta.get("fallbacks"):
        report.error(where, None, "meta.fallbacks must be a non-empty list of non-empty strings")
    tags: Counter[str] = Counter()
    owners: dict[str, str] = {}
    for index, intent in enumerate(brain.get("intents", [])):
        tag = intent.get("tag")
        label = f"intent #{index + 1} ({tag})"
        if not isinstance(tag, str) or not tag:
            report.error(where, None, f"intent #{index + 1} has no tag")
            continue
        tags[tag] += 1
        for key in ("patterns", "responses"):
            items = intent.get(key)
            if not isinstance(items, list) or not items or not all(isinstance(i, str) and i.strip() for i in items):
                report.error(where, None, f"{label}: '{key}' must be a non-empty list of non-empty strings")
        for reply in intent.get("responses", []):
            if isinstance(reply, str) and re.search(r"\b(TODO|FIXME|lorem ipsum)\b", reply, re.I):
                report.error(where, None, f"{label}: unfinished reply: {reply[:50]}")
        priority = intent.get("priority", 1)
        if isinstance(priority, bool) or not isinstance(priority, (int, float)) or priority <= 0:
            report.error(where, None, f"{label}: priority must be a positive number")
        for pattern in intent.get("patterns", []):
            key = pattern.strip().lower() if isinstance(pattern, str) else ""
            if key in owners and owners[key] != tag:
                report.warn(where, None, f"pattern '{pattern}' is used by both '{owners[key]}' and '{tag}'")
            owners.setdefault(key, tag)
    for tag, count in tags.items():
        if count > 1:
            report.error(where, None, f"tag '{tag}' is used by {count} intents")
    for table in ("phraseFixes", "typos"):
        for wrong, right in brain.get(table, {}).items():
            if not isinstance(right, str) or not wrong.strip() or not right.strip():
                report.error(where, None, f"{table}: empty entry for '{wrong}'")
            elif wrong == right:
                report.warn(where, None, f"{table}: '{wrong}' maps to itself")


def check_yaml(project: Project) -> None:
    report = project.report
    files = project.by_suffix(".yml", ".yaml")
    try:
        import yaml
    except ImportError:
        report.warn(".github", None, "PyYAML is not installed, YAML files were not checked")
        return
    for path in files:
        where = rel(path)
        project.checked["YAML files"] += 1
        try:
            data = yaml.safe_load(read(path))
        except yaml.YAMLError as err:
            report.error(where, getattr(getattr(err, "problem_mark", None), "line", -1) + 1 or None, f"invalid YAML: {err}")
            continue
        parent = path.parent.name
        if parent == "workflows":
            check_workflow(report, where, data)
        elif parent == "ISSUE_TEMPLATE" and path.name != "config.yml":
            check_issue_form(report, where, data)
        elif path.name == "dependabot.yml":
            for update in data.get("updates", []):
                directory = ROOT / str(update.get("directory", "")).lstrip("/")
                if not directory.exists():
                    report.error(where, None, f"directory {update.get('directory')} does not exist")
                if update.get("package-ecosystem") == "github-actions" and not (ROOT / ".github" / "workflows").exists():
                    report.error(where, None, "github-actions ecosystem but there is no .github/workflows folder")


def check_workflow(report: Report, where: str, data: dict) -> None:
    if not isinstance(data, dict) or "jobs" not in data:
        report.error(where, None, "workflow has no jobs")
        return
    if "on" not in data and True not in data:
        report.error(where, None, "workflow has no trigger ('on')")
    for name, job in data["jobs"].items():
        if "runs-on" not in job and "uses" not in job:
            report.error(where, None, f"job '{name}' has no runs-on")
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses and not uses.startswith("./") and "@" not in uses:
                report.error(where, None, f"job '{name}': '{uses}' is not pinned to a version")
            script = re.sub(r"https?://\S+|\$\{\{.*?\}\}", "", step.get("run", ""))
            for token in re.findall(r"(?<![\w./$-])((?:\.?[\w-]+/)+[\w.*-]*)", script):
                if not glob.glob(token, root_dir=ROOT):
                    report.error(where, None, f"job '{name}': path '{token}' does not exist in the repository")


def check_issue_form(report: Report, where: str, data: dict) -> None:
    for key in ("name", "description", "body"):
        if key not in data:
            report.error(where, None, f"issue form is missing '{key}'")
    ids: Counter[str] = Counter()
    for field in data.get("body", []):
        if field.get("type") not in ("markdown", "textarea", "input", "dropdown", "checkboxes"):
            report.error(where, None, f"unknown field type '{field.get('type')}'")
        if "id" in field:
            ids[field["id"]] += 1
        if field.get("type") == "dropdown" and not field.get("attributes", {}).get("options"):
            report.error(where, None, f"dropdown '{field.get('id')}' has no options")
        if field.get("type") != "markdown" and not field.get("attributes", {}).get("label") and field.get("type") != "checkboxes":
            report.error(where, None, f"field '{field.get('id')}' has no label")
    for name, count in ids.items():
        if count > 1:
            report.error(where, None, f"field id '{name}' is used {count} times")


def check_unreferenced_images(project: Project) -> None:
    for path in project.by_suffix(".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp"):
        name = rel(path)
        if name not in project.referenced and name not in KEEP_UNREFERENCED:
            project.report.warn(name, None, "image is not used by any page, document or server route")


def external_urls(project: Project) -> dict[str, str]:
    found: dict[str, str] = {}
    for path in project.files:
        if path.suffix not in (".md", ".yml", ".html"):
            continue
        text = "\n".join(line for _, line in prose_lines(read(path))) if path.suffix == ".md" else read(path)
        text = INLINE_CODE.sub("", text) if path.suffix == ".md" else text
        for match in re.finditer(r"https?://[^\s)\"'<>\]]+", text):
            url = match.group(0).rstrip(".,;:")
            if OWN_URL.match(url) or any(skip in url for skip in SKIP_EXTERNAL):
                continue
            found.setdefault(url, rel(path))
    return found


def probe(url: str) -> tuple[str, str]:
    headers = {"User-Agent": "nova-chatbot-link-check (+https://github.com/gelowie/nova-chatbot)"}
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=15):
                return "ok", ""
        except urllib.error.HTTPError as err:
            if err.code in (403, 405, 501) and method == "HEAD":
                continue
            if err.code in (404, 410):
                return "error", f"HTTP {err.code}"
            return "warning", f"HTTP {err.code}"
        except urllib.error.URLError as err:
            if isinstance(err.reason, socket.gaierror):
                return "error", "host name does not resolve"
            return "warning", f"could not connect ({err.reason})"
        except (TimeoutError, OSError) as err:
            return "warning", f"could not connect ({err})"
    return "warning", "no usable response"


def check_external(project: Project) -> None:
    urls = external_urls(project)
    print(f"Checking {len(urls)} external links...")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(probe, urls))
    for (url, source), (level, message) in zip(urls.items(), results):
        if level == "error":
            project.report.error(source, None, f"dead link {url}: {message}")
        elif level == "warning":
            project.report.warn(source, None, f"could not verify {url}: {message}")


def write_summary(report: Report, title: str) -> None:
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    lines = [f"## {title}", "", f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)", ""]
    lines += [f"- :x: {e}" for e in report.errors] + [f"- :warning: {w}" for w in report.warnings]
    with open(target, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--external", action="store_true", help="check http(s) links instead of the offline checks")
    args = parser.parse_args()

    report = Report()
    project = Project(report)
    if args.external:
        check_external(project)
        title = "External links"
    else:
        for step in (check_python, check_json, check_text_files, check_facts, check_markdown, check_badges,
                     check_html, check_own_urls, check_java, check_yaml, check_unreferenced_images):
            step(project)
        title = "Repository checks"
    write_summary(report, title)
    if project.checked:
        print("\nChecked: " + ", ".join(f"{n} {name}" for name, n in project.checked.items()))
    print(f"{title}: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
