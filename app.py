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

        # ---------- STRONG CORRELATIONS ----------
        strong_corrs = []
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            for i in corr.columns:
                for j in corr.columns:
                    if i != j and abs(corr.loc[i, j]) > 0.7:
                        strong_corrs.append((i, j, round(corr.loc[i, j], 3)))

        # ---------- MODEL READINESS SCORE ----------
        model_readiness = round(
            (completeness * 0.5) +
            ((100 - duplicate_pct) * 0.2) +
            (min(len(numeric_cols) / cols, 1) * 100 * 0.15) +
            (min(len(categorical_cols) / cols, 1) * 100 * 0.15),
            2
        )

        # ---------- ML ALGORITHM SUGGESTION ----------
        ml_suggestions = []

        if rows < 5000:
            ml_suggestions.append("Linear Regression / Logistic Regression")

        if len(numeric_cols) > len(categorical_cols):
            ml_suggestions.append("Random Forest")
            ml_suggestions.append("Gradient Boosting (XGBoost-style)")

        if strong_corrs:
            ml_suggestions.append("Regularized Models (Ridge / Lasso)")

        if len(numeric_cols) >= 3 and len(categorical_cols) == 0:
            ml_suggestions.append("K-Means Clustering")

        ml_suggestions = list(set(ml_suggestions))

        # ---------- FEATURE IMPORTANCE (SIMULATION) ----------
        feature_importance = {}
        if numeric_cols:
            variances = df[numeric_cols].var().sort_values(ascending=False)
            total_var = variances.sum()

            for col, var in variances.items():
                importance = round((var / total_var) * 100, 2) if total_var != 0 else 0
                feature_importance[col] = importance

        # ---------- EXECUTIVE SUMMARY ----------
        exec_summary = f"""
This dataset contains {rows} rows and {cols} columns.
Overall completeness is {completeness}% with {duplicate_pct}% duplicate rows.

Numeric Features: {len(numeric_cols)}
Categorical Features: {len(categorical_cols)}

Model Readiness Score: {model_readiness}/100.
"""

        if high_missing_cols:
            exec_summary += f"\nHigh missing columns detected: {', '.join(high_missing_cols)}."

        if model_readiness >= 80:
            exec_summary += "\nThe dataset is well-prepared for machine learning."
        elif model_readiness >= 60:
            exec_summary += "\nModerate data cleaning is recommended before modeling."
        else:
            exec_summary += "\nSignificant preprocessing is required before modeling."

        # ---------- INIT PDF ----------
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "AUTO GENERATED DATA REPORT", ln=True)
        pdf.ln(5)

        # ---------- EXECUTIVE SUMMARY ----------
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
            f"Model Readiness Score: {model_readiness}/100"
        )

        # ---------- ML SUGGESTIONS ----------
        pdf.ln(4)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 10, "Recommended ML Algorithms", ln=True)
        pdf.set_font("Arial", "", 11)

        for algo in ml_suggestions:
            pdf.cell(0, 7, f"- {algo}", ln=True)

        # ---------- FEATURE IMPORTANCE ----------
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Feature Importance (Simulated)", ln=True)
        pdf.set_font("Arial", "", 11)

        for col, score in feature_importance.items():
            pdf.cell(0, 7, f"{col}: {score}%", ln=True)

        # ---------- SAVE PDF ----------
        pdf.output("output/report.pdf")

        return {
            "summary": {
                "rows": rows,
                "columns": cols,
                "completeness": completeness,
                "model_readiness": model_readiness
            },
            "ml_suggestions": ml_suggestions,
            "feature_importance": feature_importance
        }

    except Exception as e:
        return {"error": str(e)}
