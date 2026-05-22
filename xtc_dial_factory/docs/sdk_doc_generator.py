"""Parse Java stub files and generate structured documentation (HTML/Markdown)."""

import os
import re
import html as html_module
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Regex patterns for Java source parsing
# ---------------------------------------------------------------------------

# javadoc comment block immediately preceding a declaration
RE_JAVADOC = re.compile(r'/\*\*([\s\S]*?)\*/')

# package declaration
RE_PACKAGE = re.compile(r'^\s*package\s+([\w.]+)\s*;', re.MULTILINE)

# class / interface declaration
RE_CLASS = re.compile(
    r'(?:(public|protected|private|abstract|final|static)\s+)?'
    r'(class|interface|@interface)\s+(\w+)'
    r'(?:\s*<\s*(\w+(?:\s*extends\s+\w+)?(?:\s*,\s*\w+(?:\s*extends\s+\w+)?)*)\s*>)?'
    r'(?:\s+extends\s+([\w.]+(?:\s*<\s*[\w.\s,]+>)?))?'
    r'(?:\s+implements\s+([\w.,\s]+(?:<\s*[\w.\s,]+>)?))?'
)

# method declaration – accounts for generics, annotations, varargs
RE_METHOD = re.compile(
    r'((?:(?:public|protected|private|static|abstract|final|synchronized|native)\s+)*)'
    r'(?:<\s*[\w\s,]+(?:\s*extends\s+\w+)?\s*>\s+)?'  # type params like <T>
    r'(\w+(?:<[\w.?,\s]+>)?(?:\[\])?(?:\.\w+)?)\s+'  # return type
    r'(\w+)\s*'  # method name
    r'\(([^)]*)\)'  # parameter list
    r'\s*(?:throws\s+[\w.,\s]+)?\s*[;{]'  # ; for interfaces, { for classes
)

# field declaration
RE_FIELD = re.compile(
    r'(?:(public|protected|private|static|final|abstract|synchronized|transient|volatile)\s+)*'
    r'(\w+(?:<[\w?,\s]+>)?(?:\[\])?(?:\.\w+)?)\s+'  # type
    r'(\w+)\s*'  # name
    r'(?:\s*=\s*[^;]+)?\s*;'
)

# single-line annotation  (e.g.  @Override)
RE_ANNOTATION = re.compile(r'^\s*@\w+')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_JAVA_KEYWORDS = frozenset({
    'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
    'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
    'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements',
    'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new',
    'package', 'private', 'protected', 'public', 'return', 'short', 'static',
    'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
    'transient', 'try', 'void', 'volatile', 'while',
})

_BUILTIN_TYPES = frozenset({
    'int', 'long', 'float', 'double', 'boolean', 'char', 'byte', 'short',
    'void', 'String', 'Object', 'Integer', 'Long', 'Float', 'Double',
    'Boolean', 'Character', 'Byte', 'Short', 'Void',
})


def _is_builtin_type(t: str) -> bool:
    return t in _BUILTIN_TYPES


def _highlight_java(code: str) -> str:
    """Apply basic syntax highlighting to Java code fragments.

    Order matters — highlight everything that can appear in *code* first
    (annotations, strings, numbers), and only then insert HTML keyword
    tags, so that the inserted ``class="kw"`` attributes are not mistaken
    for string literals.
    """
    escaped = html_module.escape(code)

    # 1. Highlight annotations (safe first — no HTML yet)
    escaped = re.sub(r'(@\w+)', r'<span class="ann">\1</span>', escaped)
    # 2. Highlight string literals (safe — no class="kw" HTML yet)
    escaped = re.sub(r'("(?:[^"\\]|\\.)*")', r'<span class="str">\1</span>', escaped)
    # 3. Highlight numbers (safe — no keywords in them)
    escaped = re.sub(r'\b(\d+)\b', r'<span class="num">\1</span>', escaped)

    # 4. Keywords & built-in types — single pass via callback so earlier
    #    matches (e.g. "class") cannot re-match inside the <span> HTML
    #    inserted for later matches.
    kw_map: dict[str, str] = {}
    for kw in _JAVA_KEYWORDS:
        kw_map[kw] = "kw"
    for bt in _BUILTIN_TYPES:
        kw_map[bt] = "bt"

    if kw_map:
        pattern = '|'.join(
            r'\b' + re.escape(k) + r'\b'
            for k in sorted(kw_map, key=len, reverse=True)
        )
        def _replace_kw(m: re.Match) -> str:
            word = m.group(0)
            return f'<span class="{kw_map[word]}">{word}</span>'
        escaped = re.sub(pattern, _replace_kw, escaped)

    return escaped


def _parse_javadoc(javadoc: str) -> str:
    """Convert raw javadoc text into clean plain text description."""
    lines = []
    for line in javadoc.split('\n'):
        # Strip leading whitespace and * (common javadoc formatting)
        line = re.sub(r'^\s*\*\s?', '', line).strip()
        if line.startswith('@') or line == '':
            continue
        lines.append(line)

    # Join and collapse whitespace
    text = ' '.join(lines)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _parse_param_javadoc(javadoc: str) -> dict[str, str]:
    """Extract @param descriptions from javadoc text."""
    params: dict[str, str] = {}
    for match in re.finditer(r'@param\s+(\w+)\s+(.+)', javadoc, re.MULTILINE):
        params[match.group(1)] = match.group(2).strip()
    return params


def _parse_return_javadoc(javadoc: str) -> Optional[str]:
    """Extract @return text from javadoc."""
    m = re.search(r'@return\s+(.+)', javadoc, re.MULTILINE)
    return m.group(1).strip() if m else None


def _parse_see_javadoc(javadoc: str) -> list[str]:
    """Extract @see references from javadoc."""
    return [
        m.group(1).strip()
        for m in re.finditer(r'@see\s+(.+)', javadoc, re.MULTILINE)
    ]


def _parse_javadoc_tags(javadoc: str) -> dict:
    """Extract all structured javadoc information."""
    return {
        'description': _parse_javadoc(javadoc),
        'params': _parse_param_javadoc(javadoc),
        'returns': _parse_return_javadoc(javadoc),
        'see': _parse_see_javadoc(javadoc),
    }


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


class SdkDocGenerator:
    """Parses Java stub files and generates HTML / Markdown documentation."""

    def __init__(self, stubs_dir: str | None = None):
        self.stubs_dir = (
            stubs_dir
            if stubs_dir is not None
            else os.path.join(os.path.dirname(__file__), '..', '..',
                              'resources', 'stubs')
        )
        self.stubs_dir = os.path.normpath(self.stubs_dir)
        self._parsed_cache: list[dict] | None = None

    # ------------------------------------------------------------------
    # Scanning & Parsing
    # ------------------------------------------------------------------

    def scan_stubs(self) -> list[dict]:
        """Scan all .java files under stubs_dir and return parsed classes.

        Each entry contains:
            package, name, modifiers, type (class/interface),
            extends, implements, methods, fields, javadoc
        """
        if self._parsed_cache is not None:
            return self._parsed_cache

        results: list[dict] = []
        base = Path(self.stubs_dir)
        if not base.is_dir():
            return results

        for java_file in sorted(base.rglob('*.java')):
            try:
                parsed = self._parse_java_file(str(java_file))
                if parsed:
                    results.append(parsed)
            except Exception as exc:
                print(f'Warning: failed to parse {java_file}: {exc}')

        self._parsed_cache = results
        return results

    def _parse_java_file(self, filepath: str) -> dict | None:
        """Parse a single .java file with regex and return a structured dict."""

        with open(filepath, 'r', encoding='utf-8') as fh:
            source = fh.read()

        # --- Javadoc blocks ---
        # Collect javadoc comments mapped by their end position in the source
        javadoc_map: dict[int, str] = {}
        for m in RE_JAVADOC.finditer(source):
            # The javadoc comment ends at m.end()
            javadoc_map[m.end()] = m.group(1)

        # --- Package ---
        pkg_match = RE_PACKAGE.search(source)
        if not pkg_match:
            return None
        package_name = pkg_match.group(1)

        # --- Class / Interface declaration ---
        class_match = RE_CLASS.search(source)
        if not class_match:
            return None

        modifiers = class_match.group(1) or ''
        class_type = class_match.group(2)   # 'class' or 'interface'
        class_name = class_match.group(3)
        extends = class_match.group(5) or ''
        implements = class_match.group(6) or ''

        # Grab javadoc for the class
        class_javadoc_raw = ''
        for end_pos, jdoc in javadoc_map.items():
            # javadoc block should end right before the class declaration starts
            gap = source[end_pos:class_match.start()]
            if re.match(r'^\s*$', gap):
                class_javadoc_raw = jdoc
                break

        # --- Methods ---
        methods: list[dict] = []
        for m in RE_METHOD.finditer(source):
            # Skip if inside a javadoc block or string
            method_modifiers = m.group(1) or ''
            return_type = m.group(2)
            method_name = m.group(3)
            params_raw = m.group(4).strip()

            params: list[dict] = []
            if params_raw:
                for param in re.split(r',\s*', params_raw):
                    param = param.strip()
                    if not param:
                        continue
                    # Split on last whitespace to get type + name
                    parts = param.rsplit(None, 1)
                    if len(parts) == 2:
                        p_type, p_name = parts
                    else:
                        p_type, p_name = parts[0], ''
                    # Handle varargs
                    if '...' in p_type:
                        p_type = p_type.replace('...', '...')
                    params.append({'type': p_type.strip(), 'name': p_name.strip()})

            # Check for trailing annotation (e.g., "@Override")
            preceding = source[m.start() - 20:m.start()].strip()
            has_override = '@Override' in preceding

            # Grab javadoc just before the method
            method_jdoc_raw = ''
            for end_pos, jdoc in javadoc_map.items():
                gap = source[end_pos:m.start()]
                if re.match(r'^\s*(?:\n\s*)*$', gap):
                    method_jdoc_raw = jdoc
                    break

            methods.append({
                'modifiers': method_modifiers,
                'return_type': return_type,
                'name': method_name,
                'params': params,
                'javadoc': _parse_javadoc_tags(method_jdoc_raw) if method_jdoc_raw else {},
                'has_override': has_override,
                'signature': self._format_method_signature(
                    method_modifiers, return_type, method_name, params),
            })

            # Fix constructor parsing: when the ungreedy modifiers group
            # gave up, a modifier keyword like "public" may have ended up
            # as the captured return type.  Detect and swap.
            last_method = methods[-1]
            if (last_method['return_type']
                    and last_method['return_type']
                    in {'public', 'protected', 'private', 'static',
                        'abstract', 'final'}):
                old_mods = last_method['modifiers'].strip()
                kw = last_method['return_type']
                last_method['modifiers'] = (kw + ' ' + old_mods).strip()
                last_method['return_type'] = ''
                last_method['signature'] = self._format_method_signature(
                    last_method['modifiers'], last_method['return_type'],
                    last_method['name'], last_method['params'])

        # --- Fields ---
        fields: list[dict] = []
        for m in RE_FIELD.finditer(source):
            # Skip matches that are actually method declarations
            if m.group(3) in {m_.group(3) for m_ in RE_METHOD.finditer(source)}:
                continue
            field_modifiers = (m.group(1) or '').strip()
            field_type = m.group(2)
            field_name = m.group(3)

            field_jdoc_raw = ''
            for end_pos, jdoc in javadoc_map.items():
                gap = source[end_pos:m.start()]
                if re.match(r'^\s*(?:\n\s*)*$', gap):
                    field_jdoc_raw = jdoc
                    break

            fields.append({
                'modifiers': field_modifiers,
                'type': field_type,
                'name': field_name,
                'javadoc': _parse_javadoc_tags(field_jdoc_raw) if field_jdoc_raw else {},
            })

        # --- Result ---
        return {
            'package': package_name,
            'name': class_name,
            'modifiers': modifiers,
            'type': class_type,
            'extends': extends,
            'implements': implements,
            'methods': methods,
            'fields': fields,
            'javadoc': _parse_javadoc_tags(class_javadoc_raw) if class_javadoc_raw else {},
            'filepath': filepath,
            'binary_name': f'{package_name}.{class_name}',
        }

    @staticmethod
    def _format_method_signature(modifiers: str, return_type: str,
                                 method_name: str,
                                 params: list[dict]) -> str:
        """Build a compact method signature string."""
        parts = []
        if modifiers:
            parts.append(modifiers.strip())
        if return_type:
            parts.append(f'{return_type} {method_name}(')
        else:
            parts.append(f'{method_name}(')
        param_strs = [f'{p["type"]} {p["name"]}' if p['name'] else p['type']
                      for p in params]
        parts.append(', '.join(param_strs))
        parts.append(');')
        return ' '.join(parts)

    # ------------------------------------------------------------------
    # HTML generation
    # ------------------------------------------------------------------

    _CSS = '''
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                     "Helvetica Neue", Arial, sans-serif;
        background: #1e1e1e; color: #d4d4d4; font-size: 14px;
        display: flex; min-height: 100vh;
    }
    /* Navigation sidebar */
    nav.sidebar {
        width: 280px; min-width: 280px; background: #252526;
        border-right: 1px solid #3c3c3c; overflow-y: auto;
        padding: 16px 0; height: 100vh; position: sticky; top: 0;
    }
    nav.sidebar h2 {
        font-size: 13px; text-transform: uppercase; letter-spacing: 1px;
        color: #888; padding: 0 16px 8px; border-bottom: 1px solid #3c3c3c;
        margin-bottom: 8px;
    }
    nav.sidebar ul { list-style: none; }
    nav.sidebar li a {
        display: block; padding: 6px 16px; color: #cccccc;
        text-decoration: none; font-size: 13px; transition: background 0.15s;
    }
    nav.sidebar li a:hover { background: #37373d; color: #ffffff; }
    nav.sidebar li a.active { background: #094771; color: #ffffff; }
    nav.sidebar .class-badge {
        display: inline-block; font-size: 10px; padding: 0 5px;
        border-radius: 3px; margin-right: 6px; font-weight: 600;
    }
    .badge-class { background: #1a6e1a; color: #fff; }
    .badge-interface { background: #6e3a1a; color: #fff; }
    .badge-enum { background: #1a3a6e; color: #fff; }

    /* Main content */
    main { flex: 1; padding: 32px 40px; max-width: 960px; }
    h1 { font-size: 28px; font-weight: 600; margin-bottom: 4px; }
    h1 .type-label {
        font-size: 14px; font-weight: 400; color: #888;
        margin-left: 12px;
    }
    .package-path { color: #888; font-size: 13px; margin-bottom: 16px; }
    .class-header {
        background: #2d2d2d; border: 1px solid #3c3c3c; border-radius: 6px;
        padding: 16px 20px; margin-bottom: 24px;
    }
    .class-header code {
        font-size: 13px; color: #9cdcfe; line-height: 1.6;
    }
    .description { margin-bottom: 24px; line-height: 1.6; color: #d4d4d4; }

    h2 {
        font-size: 18px; font-weight: 600; margin: 28px 0 12px;
        padding-bottom: 6px; border-bottom: 1px solid #3c3c3c;
    }
    h3 { font-size: 15px; font-weight: 600; margin: 20px 0 8px; }

    /* Method / field cards */
    .member-card {
        background: #2d2d2d; border: 1px solid #3c3c3c; border-radius: 6px;
        padding: 14px 18px; margin-bottom: 10px;
    }
    .member-card .sig {
        font-family: "Fira Code", "Cascadia Code", "JetBrains Mono",
                     "Consolas", monospace;
        font-size: 13px; color: #dcdcaa; margin-bottom: 6px;
    }
    .member-card .sig .kw { color: #569cd6; }
    .member-card .sig .bt { color: #4ec9b0; }
    .member-card .sig .ann { color: #d7ba7d; }
    .member-card .sig .str { color: #ce9178; }
    .member-card .sig .num { color: #b5cea8; }
    .member-desc { color: #b4b4b4; font-size: 13px; line-height: 1.5; }
    .param-table {
        margin-top: 8px; border-collapse: collapse; width: 100%;
        font-size: 13px;
    }
    .param-table th {
        text-align: left; color: #888; font-weight: 500;
        padding: 2px 12px 2px 0; border-bottom: 1px solid #3c3c3c;
    }
    .param-table td {
        padding: 3px 12px 3px 0; border-bottom: 1px solid #333;
        vertical-align: top;
    }
    .param-table td:first-child { color: #9cdcfe; font-family: monospace; }
    .param-table td:last-child { color: #b4b4b4; }
    .return-info { margin-top: 6px; font-size: 13px; color: #b4b4b4; }
    .return-info strong { color: #888; }

    /* Index page */
    .index-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 12px; margin-top: 16px;
    }
    .index-card {
        background: #2d2d2d; border: 1px solid #3c3c3c; border-radius: 6px;
        padding: 16px; transition: border-color 0.2s;
    }
    .index-card:hover { border-color: #094771; }
    .index-card .name {
        font-weight: 600; font-size: 16px; margin-bottom: 4px;
    }
    .index-card .name a {
        color: #9cdcfe; text-decoration: none;
    }
    .index-card .name a:hover { text-decoration: underline; }
    .index-card .pkg { color: #888; font-size: 12px; margin-bottom: 6px; }
    .index-card .desc { color: #b4b4b4; font-size: 13px; line-height: 1.5; }

    .count-badge {
        display: inline-block; background: #333; color: #aaa;
        border-radius: 10px; padding: 0 8px; font-size: 12px;
        margin-left: 8px;
    }
    hr { border: none; border-top: 1px solid #3c3c3c; margin: 24px 0; }
    '''

    @staticmethod
    def _page_header(title: str, sidebar_items: list[dict],
                     active_class: str = '') -> str:
        """Build the shared HTML head, sidebar, and opening <main> tag."""
        classes_html = ''
        for item in sidebar_items:
            is_active = ' active' if item['name'] == active_class else ''
            badge = f'<span class="class-badge badge-{item["type"]}">{item["type"][0]}</span>'
            classes_html += (
                f'<li><a class="sidebar-link{is_active}" '
                f'href="{item["html_file"]}">{badge}{item["name"]}</a></li>\n'
            )

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_module.escape(title)} - XTC Dial Factory SDK</title>
<style>
{SdkDocGenerator._CSS}
</style>
</head>
<body>
<nav class="sidebar">
<h2>Classes / Interfaces</h2>
<ul>
{classes_html}
</ul>
</nav>
<main>
'''

    @staticmethod
    def _page_footer() -> str:
        return '\n</main>\n</body>\n</html>'

    @staticmethod
    def _method_html(m: dict) -> str:
        """Render a single method card as HTML."""
        sig = _highlight_java(m['signature'])
        parts = [f'<div class="member-card">']
        parts.append(f'<div class="sig">{sig}</div>')

        jdoc = m.get('javadoc', {})
        desc = jdoc.get('description', '')
        if desc:
            parts.append(f'<div class="member-desc">{html_module.escape(desc)}</div>')

        if jdoc.get('params'):
            parts.append('<table class="param-table">')
            parts.append('<tr><th>Parameter</th><th>Description</th></tr>')
            for p in m['params']:
                p_desc = html_module.escape(jdoc['params'].get(p['name'], ''))
                parts.append(
                    f'<tr><td>{html_module.escape(p["name"])}</td>'
                    f'<td>{p_desc}</td></tr>')
            parts.append('</table>')

        ret = jdoc.get('returns')
        if ret:
            ret_type = html_module.escape(m['return_type'])
            ret_desc = html_module.escape(ret)
            parts.append(
                f'<div class="return-info"><strong>Returns</strong> '
                f'({ret_type}): {ret_desc}</div>')

        parts.append('</div>')
        return '\n'.join(parts)

    @staticmethod
    def _field_html(f: dict) -> str:
        """Render a single field card as HTML."""
        sig_parts = []
        if f['modifiers']:
            sig_parts.append(f['modifiers'])
        sig_parts.append(f'{f["type"]} {f["name"]}')
        sig = _highlight_java(' '.join(sig_parts))
        parts = [f'<div class="member-card">']
        parts.append(f'<div class="sig">{sig}</div>')
        desc = f.get('javadoc', {}).get('description', '')
        if desc:
            parts.append(f'<div class="member-desc">{html_module.escape(desc)}</div>')
        parts.append('</div>')
        return '\n'.join(parts)

    def _class_html(self, cls: dict, all_classes: list[dict]) -> str:
        """Generate full HTML page for a single class/interface."""
        sidebar_items = []
        for other in sorted(all_classes, key=lambda x: x['name']):
            sidebar_items.append({
                'name': other['name'],
                'type': other['type'],
                'html_file': f'{other["name"]}.html',
            })

        type_label = 'Interface' if cls['type'] == 'interface' else 'Class'
        header = self._page_header(f'{cls["name"]} - SDK Docs',
                                   sidebar_items, active_class=cls['name'])

        # Title
        parts = [header]
        parts.append(f'<h1>{cls["name"]} <span class="type-label">{type_label}</span></h1>')

        pkg = html_module.escape(cls['package'])
        parts.append(f'<div class="package-path">{pkg}</div>')

        # Class declaration box
        decl_parts = []
        if cls['modifiers']:
            decl_parts.append(cls['modifiers'])
        decl_parts.append(cls['type'])
        decl_parts.append(cls['name'])
        if cls['extends']:
            decl_parts.append(f'extends {cls["extends"]}')
        if cls['implements']:
            impls = re.sub(r'\s+', '', cls['implements'])
            decl_parts.append(f'implements {impls}')
        decl_code = _highlight_java(' '.join(decl_parts))

        parts.append(f'<div class="class-header"><code>{decl_code}</code></div>')

        # Description
        desc = cls.get('javadoc', {}).get('description', '')
        if desc:
            parts.append(f'<div class="description">{html_module.escape(desc)}</div>')

        # Field summary
        if cls['fields']:
            parts.append('<h2>Fields</h2>')
            for f in cls['fields']:
                parts.append(self._field_html(f))

        # Method summary
        if cls['methods']:
            parts.append(f'<h2>Methods <span class="count-badge">{len(cls["methods"])}</span></h2>')
            for m in cls['methods']:
                parts.append(self._method_html(m))

        parts.append(self._page_footer())
        return '\n'.join(parts)

    def _index_html(self, all_classes: list[dict]) -> str:
        """Generate the overview index page."""
        sidebar_items = []
        for other in sorted(all_classes, key=lambda x: x['name']):
            sidebar_items.append({
                'name': other['name'],
                'type': other['type'],
                'html_file': f'{other["name"]}.html',
            })

        parts = [self._page_header('XTC Dial Factory SDK', sidebar_items)]
        parts.append('<h1>XTC Dial Factory SDK <span class="type-label">Java API Reference</span></h1>')
        parts.append('<div class="description">')
        parts.append('Documentation generated from stub files used for XTC watch face and plugin compilation.')
        parts.append('</div>')
        parts.append('<hr>')
        parts.append('<h2>Classes and Interfaces</h2>')
        parts.append('<div class="index-grid">')

        for cls in sorted(all_classes, key=lambda x: x['name']):
            pkg = html_module.escape(cls['package'])
            name = cls['name']
            desc = cls.get('javadoc', {}).get('description', '')
            type_badge = cls['type']
            method_count = len(cls['methods'])
            html_file = f'{name}.html'
            parts.append(
                f'<div class="index-card">'
                f'<div class="name">'
                f'<span class="class-badge badge-{type_badge}">{type_badge[0]}</span> '
                f'<a href="{html_file}">{name}</a>'
                f'</div>'
                f'<div class="pkg">{pkg}</div>'
                f'<div class="desc">{html_module.escape(desc) if desc else "No description"}</div>'
                f'<div style="margin-top:6px;color:#888;font-size:12px;">'
                f'{method_count} method{"s" if method_count != 1 else ""}'
                f'</div>'
                f'</div>'
            )

        parts.append('</div>')
        parts.append(self._page_footer())
        return '\n'.join(parts)

    def generate_html(self, output_dir: str) -> str:
        """Generate HTML documentation files in output_dir.

        Returns the path to index.html.
        """
        classes = self.scan_stubs()
        if not classes:
            raise RuntimeError('No classes found in stubs directory: '
                               f'{self.stubs_dir}')

        os.makedirs(output_dir, exist_ok=True)

        # Write class pages
        for cls in classes:
            html = self._class_html(cls, classes)
            filepath = os.path.join(output_dir, f'{cls["name"]}.html')
            with open(filepath, 'w', encoding='utf-8') as fh:
                fh.write(html)

        # Write index
        index_html = self._index_html(classes)
        index_path = os.path.join(output_dir, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as fh:
            fh.write(index_html)

        return index_path

    # ------------------------------------------------------------------
    # Markdown generation
    # ------------------------------------------------------------------

    def generate_markdown(self, output_dir: str) -> str:
        """Generate Markdown documentation files in output_dir.

        Returns the path to index.md.
        """
        classes = self.scan_stubs()
        if not classes:
            raise RuntimeError('No classes found in stubs directory: '
                               f'{self.stubs_dir}')

        os.makedirs(output_dir, exist_ok=True)

        for cls in classes:
            md = self._class_markdown(cls, classes)
            filepath = os.path.join(output_dir, f'{cls["name"]}.md')
            with open(filepath, 'w', encoding='utf-8') as fh:
                fh.write(md)

        index_md = self._index_markdown(classes)
        index_path = os.path.join(output_dir, 'index.md')
        with open(index_path, 'w', encoding='utf-8') as fh:
            fh.write(index_md)

        return index_path

    @staticmethod
    def _class_markdown(cls: dict, all_classes: list[dict]) -> str:
        """Generate Markdown for a single class."""
        lines = []
        type_label = 'Interface' if cls['type'] == 'interface' else 'Class'
        lines.append(f'# {cls["name"]} — {type_label}')
        lines.append('')
        lines.append(f'**Package:** `{cls["package"]}`')
        lines.append('')

        # Declaration
        decl_parts = []
        if cls['modifiers']:
            decl_parts.append(cls['modifiers'])
        decl_parts.append(cls['type'])
        decl_parts.append(cls['name'])
        if cls['extends']:
            decl_parts.append(f'extends {cls["extends"]}')
        if cls['implements']:
            decl_parts.append(f'implements {cls["implements"]}')
        lines.append(f'```java\n{" ".join(decl_parts)}\n```')
        lines.append('')

        desc = cls.get('javadoc', {}).get('description', '')
        if desc:
            lines.append(desc)
            lines.append('')

        # Fields
        if cls['fields']:
            lines.append('## Fields')
            lines.append('')
            for f in cls['fields']:
                mod = f'{f["modifiers"]} ' if f['modifiers'] else ''
                field_desc = f.get('javadoc', {}).get('description', '')
                lines.append(f'- `{mod}{f["type"]} {f["name"]}`')
                if field_desc:
                    lines.append(f'  - {field_desc}')
            lines.append('')

        # Methods
        if cls['methods']:
            lines.append('## Methods')
            lines.append('')
            for m in cls['methods']:
                lines.append(f'### `{m["signature"]}`')
                lines.append('')
                jdoc = m.get('javadoc', {})
                if jdoc.get('description'):
                    lines.append(jdoc['description'])
                    lines.append('')

                if jdoc.get('params'):
                    lines.append('**Parameters:**')
                    for p in m['params']:
                        p_desc = jdoc['params'].get(p['name'], '')
                        lines.append(f'- `{p["name"]}` ({p["type"]}): {p_desc}')
                    lines.append('')

                if jdoc.get('returns'):
                    lines.append(f'**Returns:** ({m["return_type"]}): {jdoc["returns"]}')
                    lines.append('')

        return '\n'.join(lines)

    @staticmethod
    def _index_markdown(classes: list[dict]) -> str:
        """Generate overview index Markdown."""
        lines = [
            '# XTC Dial Factory SDK — Java API Reference',
            '',
            'Documentation generated from stub files used for XTC watch face '
            'and plugin compilation.',
            '',
            '## Classes and Interfaces',
            '',
        ]

        for cls in sorted(classes, key=lambda x: x['name']):
            desc = cls.get('javadoc', {}).get('description', '')
            link_text = f'[{cls["name"]}]({cls["name"]}.md)'
            lines.append(f'- {link_text} (`{cls["package"]}`)')
            if desc:
                lines.append(f'  - {desc}')

        lines.append('')
        return '\n'.join(lines)
