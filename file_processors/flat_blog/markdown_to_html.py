import re
import uuid


class MarkdownToHtmlConverter:
    def __init__(self):
        # Updated regex patterns to handle code blocks properly, including '+' in language names
        self.code_block_pattern = re.compile(r"```([\w+]+)?\n(.*?)```", re.DOTALL)
        self.inline_code_pattern = re.compile(r"`([^`]+)`")
        self.header_pattern = re.compile(r"^(#{1,6})\s*(.+)", re.MULTILINE)
        self.bold_pattern = re.compile(r"\*\*(.+?)\*\*")
        self.italic_pattern = re.compile(r"\*(.+?)\*")
        self.link_pattern = re.compile(r"\[(.+?)\]\((.+?)\)")
        self.list_pattern = re.compile(r"^\*\s+(.+)", re.MULTILINE)
        self.table_pattern = re.compile(r"^\|(.+?)\|\n\|(?:\s*:?-+:?\s*\|)+\n((?:\|.+?\|\n)+)", re.MULTILINE)
        self.code_blocks = {}

    def convert(self, markdown: str) -> str:
        html = markdown

        # Extract code blocks and replace them with placeholders
        html = self.code_block_pattern.sub(self._extract_code_block, html)

        # Process headers
        html = self.header_pattern.sub(self._replace_header, html)

        # Handle inline code
        html = self.inline_code_pattern.sub(r"<code>\1</code>", html)

        # Handle bold text
        html = self.bold_pattern.sub(r"<strong>\1</strong>", html)

        # Handle italic text
        html = self.italic_pattern.sub(r"<em>\1</em>", html)

        # Handle links
        html = self.link_pattern.sub(r'<a href="\2">\1</a>', html)

        # Handle unordered lists
        html = self.list_pattern.sub(self._replace_list, html)

        # Handle tables
        html = self.table_pattern.sub(self._replace_table, html)

        # Wrap paragraphs around text blocks
        html = self._wrap_paragraphs(html)

        # Replace GUID placeholders with actual code block contents
        for guid, (language, code) in self.code_blocks.items():
            html = html.replace(guid, self._wrap_code_block(language, code))

        return html

    def _extract_code_block(self, match):
        language = match.group(1) if match.group(1) else "plaintext"
        code = match.group(2)

        # Generate a GUID placeholder
        guid = str(uuid.uuid4())
        self.code_blocks[guid] = (language, code)  # Store the language and code block

        return guid  # Return the placeholder

    def _wrap_code_block(self, language: str, code: str) -> str:
        # Escape HTML characters in the code
        escaped_code = self._escape_html(code)
        return f'<pre><code class="language-{language}">{escaped_code}</code></pre>'

    def _replace_header(self, match):
        header_level = len(match.group(1))
        content = match.group(2)
        return f"<h{header_level}>{content}</h{header_level}>"

    def _replace_list(self, match):
        return f"<li>{match.group(1)}</li>"

    def _replace_table(self, match):
        headers = match.group(1).strip().split("|")
        rows = match.group(2).strip().split("\n")

        # Build the HTML for the table
        thead = (
            "<thead><tr>"
            + "".join(f"<th>{self._escape_html(header.strip())}</th>" for header in headers)
            + "</tr></thead>"
        )
        tbody = "<tbody>"
        for row in rows:
            columns = row.strip().split("|")
            tbody += "<tr>" + "".join(f"<td>{self._escape_html(col.strip())}</td>" for col in columns) + "</tr>"
        tbody += "</tbody>"

        return f"<table>{thead}{tbody}</table>"

    def _wrap_paragraphs(self, html: str) -> str:
        lines = html.split("\n")
        inside_paragraph = False
        result = []
        for line in lines:
            if not line.strip():
                if inside_paragraph:
                    result.append("</p>")
                    inside_paragraph = False
            else:
                if not inside_paragraph:
                    result.append("<p>")
                    inside_paragraph = True
                result.append(line)
        if inside_paragraph:
            result.append("</p>")
        return "\n".join(result)

    def _escape_html(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )
