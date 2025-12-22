import os
import pandas as pd
import json
from fpdf import FPDF
import matplotlib.pyplot as plt
import streamlit as st

# ---------- ANALYSIS FUNCTION ----------
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
            readme_path = "output/README.md"
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write("AUTO GENERATED DOCUMENTATION\n\n")
                f.write("PYTHON FILE\n\n")
                f.write(code)
            return {"file": file_name, "type": "python"}
        else:
            return {"error": "Unsupported file type"}

        # ---------- STEP 5: PREVIEW ----------
        st.subheader("Step 5: File Preview")
        st.write(f"Detected file type: {ext}")
        st.write("First 10 rows:")
        st.dataframe(df.head(10))
        st.write("Columns:")
        st.write(list(df.columns))

        # ---------- BASIC SUMMARY ----------
        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns)
        }

        # ---------- INIT README ----------
        readme_path = "output/README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("AUTO GENERATED DOCUMENTATION\n\n")
            f.write(f"File Name: {file_name}\n\n")
            f.write(f"Total Rows: {summary['rows']}\n")
            f.write(f"Total Columns: {summary['columns']}\n\n")
            f.write("COLUMN INSIGHTS\n\n")

        # ---------- INIT PDF ----------
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "AUTO GENERATED DOCUMENTATION", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.ln(4)
        pdf.cell(0, 8, f"File Name: {file_name}", ln=True)
        pdf.cell(0, 8, f"Total Rows: {summary['rows']}", ln=True)
        pdf.cell(0, 8, f"Total Columns: {summary['columns']}", ln=True)
        pdf.ln(6)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "COLUMN INSIGHTS", ln=True)
        pdf.set_font("Arial", "", 11)

        # ---------- GRAPH GENERATION + TEXT ----------
        numeric_cols = df.select_dtypes(include=['number']).columns
        graph_paths = []

        for col in df.columns:
            total = len(df[col])
            missing = df[col].isna().sum()
            missing_pct = round((missing / total) * 100, 2)
            unique = df[col].nunique(dropna=True)
            samples = df[col].dropna().unique()[:5]

            # Write column insights to README
            with open(readme_path, "a", encoding="utf-8") as f:
                f.write(f"Column Name: {col}\n")
                f.write(f"Data Type: {df[col].dtype}\n")
                f.write(f"Total Values: {total}\n")
                f.write(f"Missing Values: {missing}\n")
                f.write(f"Missing Percentage: {missing_pct}%\n")
                f.write(f"Unique Values: {unique}\n")
                f.write(f"Sample Values: {', '.join(map(str, samples))}\n")

            # Write column insights to PDF
            pdf.multi_cell(
                0, 7,
                f"Column Name: {col}\n"
                f"Data Type: {df[col].dtype}\n"
                f"Total Values: {total}\n"
                f"Missing Values: {missing}\n"
                f"Missing Percentage: {missing_pct}%\n"
                f"Unique Values: {unique}\n"
                f"Sample Values: {', '.join(map(str, samples))}\n"
                + "-" * 40
            )
            pdf.ln(2)

            # If numeric column, add graph + min/max
            if col in numeric_cols:
                series = df[col]
                min_value = series.min()
                max_value = series.max()

                # ---------- Graph ----------
                plt.figure(figsize=(8, 4))
                plt.plot(series, marker='o', label=col)
                plt.axhline(min_value, color='red', linestyle='--', label=f'Min: {min_value}')
                plt.axhline(max_value, color='green', linestyle='--', label=f'Max: {max_value}')
                plt.title(f"{col} with Min & Max")
                plt.xlabel("Index")
                plt.ylabel(col)
                plt.legend()
                plt.grid(True)
                plt.tight_layout()

                graph_file = f"output/{col}.png"
                plt.savefig(graph_file)
                plt.close()
                graph_paths.append(graph_file)

                # ---------- Add min/max to README ----------
                with open(readme_path, "a", encoding="utf-8") as f:
                    f.write(f"Minimum Value: {min_value}\n")
                    f.write(f"Maximum Value: {max_value}\n")
                    f.write(f"![{col}]({graph_file})\n\n")

                # ---------- Add min/max + graph to PDF ----------
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, f"{col} Min & Max", ln=True)
                pdf.set_font("Arial", "", 11)
                pdf.cell(0, 7, f"Minimum Value: {min_value}", ln=True)
                pdf.cell(0, 7, f"Maximum Value: {max_value}", ln=True)
                pdf.ln(2)
                pdf.image(graph_file, x=10, y=None, w=180)
                pdf.ln(5)

        # ---------- SAVE PDF ----------
        pdf.output("output/report.pdf")

        return {"summary": summary, "graphs": graph_paths}

    except Exception as e:
        return {"error": str(e)}
