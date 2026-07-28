import os
import sys
import re
from pathlib import Path

# Load markdown file
md_path = Path("docs/documentation.md")
pdf_path = Path("docs/documentation.pdf")

if not md_path.exists():
    print(f"Error: {md_path} does not exist.")
    sys.exit(1)

md_text = md_path.read_text(encoding="utf-8")

def md_to_html(text):
    # Basic Markdown to HTML converter with academic styling
    lines = text.split("\n")
    html_lines = []
    in_code = False
    in_table = False
    table_headers = []
    
    for line in lines:
        if line.startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append("<pre><code>")
                in_code = True
            continue
            
        if in_code:
            # Escape HTML characters in code blocks
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_lines.append(escaped)
            continue

        # Headers
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("#### "):
            html_lines.append(f"<h4>{line[5:]}</h4>")
        elif line.startswith("---"):
            html_lines.append("<hr>")
        elif line.startswith("| ") and "|" in line[2:]:
            # Table processing
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if "---" in parts[0] or ":---" in parts[0]:
                continue # Header separator
            if not in_table:
                in_table = True
                html_lines.append("<table>")
                html_lines.append("<tr>" + "".join([f"<th>{p}</th>" for p in parts]) + "</tr>")
            else:
                html_lines.append("<tr>" + "".join([f"<td>{p}</td>" for p in parts]) + "</tr>")
        else:
            if in_table and not line.startswith("|"):
                html_lines.append("</table>")
                in_table = False
                
            if line.strip() == "":
                continue
                
            # Inline formatting
            formatted = line
            formatted = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", formatted)
            formatted = re.sub(r"\*(.*?)\*", r"<i>\1</i>", formatted)
            formatted = re.sub(r"`(.*?)`", r"<code>\1</code>", formatted)
            
            html_lines.append(f"<p>{formatted}</p>")

    if in_table:
        html_lines.append("</table>")

    return "\n".join(html_lines)

html_body = md_to_html(md_text)

full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #1e293b;
        margin: 25px;
    }}
    h1 {{
        font-size: 20pt;
        color: #0f172a;
        text-align: center;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 10px;
        margin-top: 10px;
    }}
    h2 {{
        font-size: 14pt;
        color: #1e3a8a;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 5px;
        margin-top: 25px;
    }}
    h3 {{
        font-size: 12pt;
        color: #1e40af;
        margin-top: 18px;
    }}
    code {{
        font-family: 'Consolas', monospace;
        background-color: #f1f5f9;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 9.5pt;
        color: #0f172a;
    }}
    pre {{
        background-color: #0f172a;
        color: #f8fafc;
        padding: 12px;
        border-radius: 6px;
        font-family: 'Consolas', monospace;
        font-size: 8.5pt;
        line-height: 1.4;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 10pt;
    }}
    th, td {{
        border: 1px solid #cbd5e1;
        padding: 6px 10px;
        text-align: left;
    }}
    th {{
        background-color: #f1f5f9;
        font-weight: bold;
        color: #0f172a;
    }}
    hr {{
        border: none;
        border-top: 1px solid #cbd5e1;
        margin: 20px 0;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

# Generate PDF via PyQt6
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QTextDocument
    from PyQt6.QtPrintSupport import QPrinter

    app = QApplication(sys.argv)
    doc = QTextDocument()
    doc.setHtml(full_html)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(pdf_path))
    printer.setPageMargins(QPrinter().pageLayout().margins())

    doc.print(printer)
    print(f"Successfully generated PDF at: {pdf_path.resolve()}")
except Exception as e:
    print(f"PyQt6 PDF generation failed: {e}")
