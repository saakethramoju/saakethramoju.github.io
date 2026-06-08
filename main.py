import html
import importlib
import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))


def define_env(env):
    @env.macro
    def fullflow_api(path: str) -> str:
        """Render a FullFlow class reference from its docstring."""
        obj = _import_object(path)
        doc = inspect.getdoc(obj) or ""
        parsed = _parse_numpy_docstring(doc)

        return f"""
<div class="ff-api">
  <div class="ff-object-path">{html.escape(path)}</div>

  {_section("Parameters", _table(parsed.get("Parameters", "")))}
  {_section("Outputs", _table(parsed.get("Outputs", "")))}
  {_section("Iteration Variables", _table(parsed.get("Iteration Variables", "")))}
  {_section("Residuals", _table(parsed.get("Residuals", ""), show_equations=True))}
</div>
"""


def _import_object(path: str):
    """Import an object from a dotted module path."""
    module_name, object_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def _parse_numpy_docstring(doc: str) -> dict[str, str]:
    """Parse simple NumPy-style docstring sections."""
    sections: dict[str, list[str]] = {}
    current: str | None = None

    lines = doc.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        is_section = (
            stripped
            and i + 1 < len(lines)
            and lines[i + 1].strip()
            and set(lines[i + 1].strip()) == {"-"}
        )

        if is_section:
            current = stripped
            sections[current] = []
            i += 2
            continue

        if current:
            sections[current].append(line)

        i += 1

    return {key: "\n".join(value).strip() for key, value in sections.items()}


def _table(text: str, show_equations: bool = False) -> str:
    """Render a NumPy-style field section as a simple table."""
    rows = _parse_fields(text)

    if not rows:
        return ""

    html_rows = []

    for name, typ, desc in rows:
        html_rows.append(
            "<tr>"
            f"<td class='ff-name'>{_code(name)}</td>"
            f"<td class='ff-type'>{_code(typ)}</td>"
            f"<td class='ff-desc'>{_description(desc, show_equations)}</td>"
            "</tr>"
        )

    return f"""
<table class="ff-table">
  <thead>
    <tr>
      <th>Name</th>
      <th>Type</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    {''.join(html_rows)}
  </tbody>
</table>
"""


def _parse_fields(text: str) -> list[tuple[str, str, str]]:
    """Parse fields written as `name : type` followed by indented text."""
    rows: list[tuple[str, str, str]] = []
    pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+)$")

    current_name: str | None = None
    current_type: str | None = None
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        match = pattern.match(stripped)

        if match:
            if current_name is not None and current_type is not None:
                rows.append(
                    (
                        current_name,
                        current_type,
                        "\n".join(current_lines).strip(),
                    )
                )

            current_name = match.group(1)
            current_type = match.group(2)
            current_lines = []
            continue

        if current_name is not None:
            current_lines.append(line)

    if current_name is not None and current_type is not None:
        rows.append((current_name, current_type, "\n".join(current_lines).strip()))

    return rows


def _description(text: str, show_equations: bool = False) -> str:
    """Render a field description with optional equation blocks."""
    if not text:
        return ""

    lines = text.splitlines()
    output: list[str] = []
    equation_lines: list[str] = []
    in_equation = False

    for raw_line in lines:
        stripped = raw_line.strip()

        if stripped == "Equation:":
            in_equation = True
            continue

        if in_equation:
            if stripped:
                equation_lines.append(stripped)
                continue

            if equation_lines:
                output.append(_equation(equation_lines))
                equation_lines = []
                in_equation = False
            continue

        if stripped:
            output.append(f"<p>{_inline_code(stripped)}</p>")

    if equation_lines:
        output.append(_equation(equation_lines))

    return "\n".join(output)


def _equation(lines: list[str]) -> str:
    """Render equation lines as a readable equation block."""
    equation = "\n".join(html.escape(line) for line in lines)
    return f"<pre class='ff-equation'><code>{equation}</code></pre>"


def _inline_code(text: str) -> str:
    """Convert backtick spans to inline code."""
    escaped = html.escape(text)

    return re.sub(
        r"`([^`]+)`",
        lambda match: f"<code>{html.escape(match.group(1))}</code>",
        escaped,
    )


def _code(text: str) -> str:
    """Render plain text as inline code."""
    return f"<code>{html.escape(text)}</code>"


def _section(title: str, content: str) -> str:
    """Render a titled API section."""
    if not content:
        return ""

    slug = title.lower().replace(" ", "-")

    return f"""
<section class="ff-section ff-section-{slug}">
  <h2>{html.escape(title)}</h2>
  {content}
</section>
"""