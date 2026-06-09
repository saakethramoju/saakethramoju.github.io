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
    def fullflow_api(
        path: str,
        show_description: bool = False,
        prepend_description: str = "",
        append_description: str = "",
    ) -> str:
        """Render a FullFlow class reference from its docstring."""
        obj = _import_object(path)
        doc = inspect.getdoc(obj) or ""

        parsed = _parse_numpy_docstring(doc)
        summary = _summary(doc)

        description_html = _description_block(
            summary=summary,
            show_description=show_description,
            prepend_description=prepend_description,
            append_description=append_description,
        )

        return f"""
<div class="ff-api">
  <div class="ff-object-path">{html.escape(path)}</div>

  {description_html}

  {_section("Parameters", _table(parsed.get("Parameters", "")))}
  {_section("Returns", _table(parsed.get("Returns", "")))}
  {_section("Outputs", _table(parsed.get("Outputs", "")))}
  {_section("Iteration Variables", _table(parsed.get("Iteration Variables", "")))}
  {_section("Residuals", _table(parsed.get("Residuals", "")))}
</div>
"""


def _import_object(path: str):
    """Import an object from a dotted module or attribute path."""
    parts = path.split(".")

    for i in range(len(parts), 0, -1):
        module_name = ".".join(parts[:i])

        try:
            obj = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue

        for attr in parts[i:]:
            obj = getattr(obj, attr)

        return obj

    raise ImportError(f"Could not import object from path {path!r}.")


def _description_block(
    summary: str,
    show_description: bool,
    prepend_description: str,
    append_description: str,
) -> str:
    """Render the optional description block above the API tables."""
    parts = []

    if prepend_description:
        parts.append(_description(prepend_description.strip()))

    if show_description and summary:
        parts.append(summary)

    if append_description:
        parts.append(_description(append_description.strip()))

    if not parts:
        return ""

    return f"""
<div class="ff-summary">
  {''.join(parts)}
</div>
"""


def _summary(doc: str) -> str:
    """Extract the leading description before the first NumPy-style section."""
    if not doc:
        return ""

    lines = doc.splitlines()
    summary_lines: list[str] = []

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        is_section = (
            stripped
            and i + 1 < len(lines)
            and lines[i + 1].strip()
            and set(lines[i + 1].strip()) == {"-"}
        )

        if is_section:
            break

        summary_lines.append(lines[i])
        i += 1

    return _description("\n".join(summary_lines).strip())


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


def _table(text: str) -> str:
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
            f"<td class='ff-desc'>{_description(desc)}</td>"
            "</tr>"
        )

    return f"""
<table class="ff-table">
  <colgroup>
    <col class="ff-col-name">
    <col class="ff-col-type">
    <col class="ff-col-description">
  </colgroup>
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


def _description(text: str) -> str:
    """Render description text with inline code and display equations."""
    if not text:
        return ""

    # Capture double-backtick display equations, including multiline equations.
    parts = re.split(r"(``.*?``)", text, flags=re.DOTALL)

    output: list[str] = []

    for part in parts:
        part = part.strip()

        if not part:
            continue

        if part.startswith("``") and part.endswith("``"):
            equation = part[2:-2].strip()
            output.append(_equation(equation))
            continue

        paragraphs = re.split(r"\n\s*\n", part)

        for paragraph in paragraphs:

            lines = [
                line.strip()
                for line in paragraph.splitlines()
                if line.strip()
            ]

            if not lines:
                continue

            # bullet list
            if all(line.startswith("* ") for line in lines):
                items = "".join(
                    f"<li>{_inline_code(line[2:])}</li>"
                    for line in lines
                )

                output.append(f"<ul>{items}</ul>")
                continue

            text = " ".join(lines)
            output.append(f"<p>{_inline_code(text)}</p>")

    return "\n".join(output)


def _equation(text: str) -> str:
    """Render text as a display equation block."""
    equation = html.escape(text.strip())
    return f"<div class='ff-equation'><code>{equation}</code></div>"


def _inline_code(text: str) -> str:
    """Convert single-backtick spans to inline code."""
    escaped = html.escape(text)

    return re.sub(
        r"`([^`]+)`",
        lambda match: f"<code>{html.escape(match.group(1))}</code>",
        escaped,
    )


def _code(text: str) -> str:
    """Render plain text as inline code."""
    escaped = html.escape(text)

    escaped = escaped.replace(
        "_",
        "_<wbr>"
    )

    return f"<code>{escaped}</code>"


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