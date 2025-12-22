import os
import pandas as pd
import json
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

def analyze_file(file_path):
    os.makedirs("output", exist_ok=True)

    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_name)[1].lower()

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

        # ---------- BASIC STATS ----------
        rows, cols = df.shape
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        completeness = round((df.notna().sum().sum() / (rows * cols)) * 100, 2)
        duplicate_pct = round((df.duplicated().sum() / rows) * 100, 2)

        high_missing_cols = [
            col for col in df.columns if df[col].isna().mean() * 100 > 50
        ]

        # ---------- MODEL READINESS SCORE ----------
        model_readiness = round(
            (completeness * 0.5) +
            ((100 - duplicate_pct) * 0.2) +
            (min(len(numeric_cols) / cols, 1) * 100 * 0.15) +
            (min(len(categorical_cols) / cols, 1) * 100 * 0.15),
            2
        )

        # ---------- EXECUTIVE SUMMARY ----------
        exec_summary = f"""
This dataset contains {rows} rows and {cols} columns.
Overall completeness is {completeness}% with {duplicate_pct}% duplicate records.

The dataset has {len(numeric_cols)} numeric and {len(categorical_cols)} categorical features.

Model readiness score is {model_readiness}/100.
"""

        if high_missing_cols:
            exec_summary += f"\nHigh missing columns detected: {', '.join(high_missing_cols)}."

        if model_readiness >= 80:
            exec_summary += "\nThe dataset is well-suited for machine learning."
        elif model_readiness >= 60:
            exec_summary += "\nThe dataset requires moderate cleaning before modeling."
        else:
            exec_summary += "\nThe dataset needs significant preprocessing before modeling."

        # ---------- INIT PDF ----------
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "AUTO GENERATED DATA REPORT", ln=True)
        pdf.ln(5)

        # ---------- DATASET OVERVIEW ----------
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 10, "Dataset Overview", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(
            0, 8,
            f"File Name: {file_name}\n"
            f"Rows: {rows}\n"
            f"Columns: {cols}\n"
            f"Completeness: {completeness}%\n"
            f"Duplicate Rows: {duplicate_pct}%\n"
        )

        # ---------- EXECUTIVE SUMMARY PAGE ----------
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Executive Summary", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 8, exec_summary)

        # ---------- MODEL READINESS ----------
        pdf.ln(5)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 10, "Model Readiness Assessment", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(
            0, 8,
            f"Model Readiness Score: {model_readiness}/100\n"
            f"Numeric Features: {len(numeric_cols)}\n"
            f"Categorical Features: {len(categorical_cols)}"
        )

        # ---------- COLUMN STATS ----------
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Column Statistics", ln=True)
        pdf.set_font("Arial", "", 11)

        for col in numeric_cols:
            pdf.multi_cell(
                0, 7,
                f"{col}\n"
                f"Min: {df[col].min()}\n"
                f"Max: {df[col].max()}\n"
                f"Avg: {round(df[col].mean(),2)}\n"
                + "-" * 40
            )

        # ---------- SAVE PDF ----------
        pdf.output("output/report.pdf")

        # ---------- RETURN ----------
        return {
            "summary": {
                "rows": rows,
                "columns": cols,
                "completeness": completeness,
                "model_readiness": model_readiness
            }
        }

    except Exception as e:
        return {"error": str(e)}
