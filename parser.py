import pandas as pd
import os
import matplotlib.pyplot as plt
from fpdf import FPDF
import ast

def analyze_file(file_path, column_descriptions=None):
    """
    column_descriptions: dict, e.g. {"Name": "Employee name", "Salary": "Monthly salary"}
    Supports CSV, Excel (.xls/.xlsx), JSON, and Python (.py) files.
    Generates README.md and PDF in 'output/' folder in plain text with bold headings.
    """
    os.makedirs("output", exist_ok=True)

    def safe_text(text):
        """Replace unsupported characters for PDF"""
        return str(text).replace("→", "->").replace("📄", "").replace("…", "...")

    try:
        # ---------------- Load file ----------------
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path, low_memory=False, encoding='utf-8', on_bad_lines='skip')
            file_type = "tabular"
        elif file_path.endswith((".xls", ".xlsx")):
            df = pd.read_excel(file_path)
            file_type = "tabular"
        elif file_path.endswith(".json"):
            df = pd.read_json(file_path)
            file_type = "tabular"
        elif file_path.endswith(".py"):
            file_type = "python"
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            tree = ast.parse(code)
            py_summary = []
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    doc = ast.get_docstring(node)
                    py_summary.append({"Type":"Function","Name":node.name,"Docstring":doc})
                elif isinstance(node, ast.ClassDef):
                    doc = ast.get_docstring(node)
                    py_summary.append({"Type":"Class","Name":node.name,"Docstring":doc})
        else:
            return {"error": "Unsupported file type"}

        summary = {}

        # ---------------- README.md ----------------
        readme_path = "output/README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# 📄 Auto-Generated Documentation\n\n")
            if file_type == "tabular":
                summary = {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns)
                }
                f.write(f"**Total Rows:** {summary['rows']}\n\n")
                f.write(f"**Total Columns:** {summary['columns']}\n\n")
                f.write("## Columns Overview\n")
                for col in df.columns:
                    dtype = df[col].dtype
                    desc = column_descriptions.get(col,"") if column_descriptions else ""
                    examples = df[col].dropna().unique()[:5]
                    examples_str = ", ".join([str(e) for e in examples])
                    f.write(f"- **{col}** ({dtype}): {desc} | Example values → {examples_str}\n")
            elif file_type == "python":
                f.write("## Python File Summary\n")
                for item in py_summary:
                    doc = item["Docstring"] if item["Docstring"] else ""
                    f.write(f"- **{item['Type']}** {item['Name']}: {doc}\n")

        # ---------------- PDF Export ----------------
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.multi_cell(0, 10, safe_text("Auto-Generated Documentation\n\n"))

        pdf.set_font("Arial", 'B', 12)
        if file_type == "tabular":
            pdf.multi_cell(0, 8, f"Total Rows: {summary['rows']}")
            pdf.multi_cell(0, 8, f"Total Columns: {summary['columns']}\n")
            pdf.multi_cell(0, 10, "Columns Overview:")

            pdf.set_font("Arial", '', 12)
            for col in df.columns:
                dtype = df[col].dtype
                desc = column_descriptions.get(col,"") if column_descriptions else ""
                examples = df[col].dropna().unique()[:5]
                examples_str = ", ".join([str(e) for e in examples])
                pdf.multi_cell(0, 8, safe_text(f"- {col} ({dtype}): {desc} | Example values -> {examples_str}"))
        elif file_type == "python":
            pdf.multi_cell(0, 10, "Python File Summary:")
            pdf.set_font("Arial", '', 12)
            for item in py_summary:
                doc = item["Docstring"] if item["Docstring"] else ""
                pdf.multi_cell(0, 8, safe_text(f"- {item['Type']} {item['Name']}: {doc}"))

        pdf.output("output/report.pdf")
        return summary

    except Exception as e:
        print("Error processing file:", e)
        return {"error": str(e)}
