import os
import pandas as pd
import matplotlib.pyplot as plt
import json
from fpdf import FPDF

def analyze_file(file_path):
    os.makedirs("output", exist_ok=True)

    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_name)[1].lower()

    image_paths = []

    try:
        # ---------- READ FILE ----------
        if ext == ".csv":
            df = pd.read_csv(file_path, low_memory=False)

        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)

        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.json_normalize(data)

        elif ext == ".py":
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            with open("output/README.md", "w", encoding="utf-8") as f:
                f.write("AUTO GENERATED DOCUMENTATION\n\n")
                f.write("PYTHON FILE\n\n")
                f.write(code)

            return {"file": file_name, "type": "python"}

        else:
            return {"error": "Unsupported file type"}

        # ---------- SUMMARY ----------
        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns)
        }

        # ---------- README ----------
        readme_path = "output/README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("AUTO GENERATED DOCUMENTATION\n\n")
            f.write(f"File Name: {file_name}\n\n")
            f.write(f"Total Rows: {summary['rows']}\n")
            f.write(f"Total Columns: {summary['columns']}\n\n")
            f.write("COLUMNS\n\n")
            for col in df.columns:
                f.write(f"- {col} ({df[col].dtype})\n")

        # ---------- NUMERIC CHART ----------
        numeric_cols = df.select_dtypes(include="number").columns
        if len(numeric_cols) > 0:
            fig, ax = plt.subplots(figsize=(8, 4))
            df[numeric_cols].hist(ax=ax)
            plt.tight_layout()

            num_img = "output/numeric_summary.png"
            plt.savefig(num_img)
            plt.close()

            image_paths.append(num_img)

        # ---------- CATEGORICAL CHARTS ----------
        cat_cols = df.select_dtypes(include="object").columns
        for col in cat_cols:
            if df[col].nunique() <= 10:
                fig, ax = plt.subplots(figsize=(6, 4))
                df[col].value_counts().plot(kind="bar", ax=ax)
                ax.set_title(col)
                plt.tight_layout()

                img_path = f"output/{col}_chart.png"
                plt.savefig(img_path)
                plt.close()

                image_paths.append(img_path)

        # ---------- PDF GENERATION ----------
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "AUTO GENERATED DOCUMENTATION", ln=True)

        pdf.set_font("Arial", "", 12)
        pdf.ln(5)
        pdf.cell(0, 8, f"File Name: {file_name}", ln=True)
        pdf.cell(0, 8, f"Total Rows: {summary['rows']}", ln=True)
        pdf.cell(0, 8, f"Total Columns: {summary['columns']}", ln=True)

        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "COLUMNS", ln=True)

        pdf.set_font("Arial", "", 11)
        for col in df.columns:
            pdf.multi_cell(0, 7, f"{col} ({df[col].dtype})")

        # ---------- INSERT IMAGES INTO PDF ----------
        for img in image_paths:
            pdf.add_page()
            pdf.image(img, w=180)

        pdf.output("output/report.pdf")

        return summary

    except Exception as e:
        return {"error": str(e)}
