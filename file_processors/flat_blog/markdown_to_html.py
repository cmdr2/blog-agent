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
        self.strikethrough_pattern = re.compile(r"\~\~(.+?)\~\~")
        self.link_pattern = re.compile(r"\[(.+?)\]\((.+?)\)")
        self.ul_list_pattern = re.compile(r"^[-*]\s+(.+)", re.MULTILINE)
        self.ol_list_pattern = re.compile(r"^\d+\.\s+(.+)", re.MULTILINE)
        self.table_pattern = re.compile(r"^\|(.+?)\|\n\|(?:\s*:?-+:?\s*\|)+\n((?:\|.+?\|\n)+)", re.MULTILINE)
        self.code_blocks = {}

    def convert(self, markdown: str) -> str:
        html = markdown

        # Extract code blocks and replace them with placeholders
        html = self.code_block_pattern.sub(self._extract_code_block, html)

        # Process headers
        # html = self.header_pattern.sub(self._replace_header, html)

        # Handle inline code
        html = self.inline_code_pattern.sub(lambda m: f"<code>{self._escape_html(m.group(1))}</code>", html)

        # Handle bold text
        html = self.bold_pattern.sub(r"<strong>\1</strong>", html)

        # Handle italic text
        html = self.italic_pattern.sub(r"<em>\1</em>", html)

        # Handle strikethrough text
        html = self.strikethrough_pattern.sub(r"<del>\1</del>", html)

        # Handle links
        html = self.link_pattern.sub(r'<a href="\2">\1</a>', html)

        # Handle unordered lists
        html = self._replace_unordered_lists(html)

        # Handle ordered lists
        html = self._replace_ordered_lists(html)

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
        return f'<pre><code class="codeblock language-{language}">{escaped_code}</code></pre>'

    def _replace_header(self, match):
        header_level = len(match.group(1))
        content = match.group(2)
        return f"<h{header_level}>{content}</h{header_level}>"

    def _replace_ordered_lists(self, text: str) -> str:
        lines = text.split("\n")
        result = []
        in_ol = False
        ol_items = []
        start_index = None

        for line in lines:
            match = self.ol_list_pattern.match(line)
            if match:
                number = int(line.split(".")[0])  # Extract the starting number
                if not in_ol:
                    in_ol = True
                    start_index = number
                    ol_items = []
                ol_items.append(f"<li>{match.group(1)}</li>")
            else:
                if in_ol:
                    start_attr = f' start="{start_index}"' if start_index != 1 else ""
                    result.append(f"<ol{start_attr}>")
                    result.extend(ol_items)
                    result.append("</ol>")
                    in_ol = False
                    ol_items = []
                    start_index = None
                result.append(line)

        # Close any remaining list at the end
        if in_ol:
            start_attr = f' start="{start_index}"' if start_index != 1 else ""
            result.append(f"<ol{start_attr}>")
            result.extend(ol_items)
            result.append("</ol>")

        return "\n".join(result)

    def _replace_unordered_lists(self, text: str) -> str:
        lines = text.split("\n")
        result = []
        in_ul = False
        for line in lines:
            match = self.ul_list_pattern.match(line)
            if match:
                if not in_ul:
                    result.append("<ul>")
                    in_ul = True
                result.append(f"<li>{match.group(1)}</li>")
            else:
                if in_ul:
                    result.append("</ul>")
                    in_ul = False
                result.append(line)
        if in_ul:
            result.append("</ul>")
        return "\n".join(result)

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
