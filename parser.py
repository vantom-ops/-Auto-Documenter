import os
import pandas as pd
import json
import matplotlib.pyplot as plt
from fpdf import FPDF
from zipfile import ZipFile
import streamlit as st

# ---------- ANALYSIS FUNCTION ----------
def analyze_file(file_path, file_name):
    os.makedirs("output", exist_ok=True)

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
            readme_path = os.path.join("output", "README.md")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write("AUTO GENERATED DOCUMENTATION\n\n")
                f.write("PYTHON FILE\n\n")
                f.write(code)
            return {"file": file_name, "type": "python"}
        else:
            return {"error": "Unsupported file type"}

        # ---------- COLUMN TYPES ----------
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(exclude=['number']).columns
        numeric_count = len(numeric_cols)
        categorical_count = len(categorical_cols)
        numeric_ratio = round((numeric_count / len(df.columns)) * 100, 2)
        categorical_ratio = round((categorical_count / len(df.columns)) * 100, 2)

        # ---------- BASIC SUMMARY ----------
        total_cells = df.size
        total_missing = df.isna().sum().sum()
        completeness = round(((total_cells - total_missing) / total_cells) * 100, 2)

        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "numeric_count": numeric_count,
            "categorical_count": categorical_count,
            "numeric_ratio": numeric_ratio,
            "categorical_ratio": categorical_ratio,
            "completeness": completeness
        }

        # ---------- WARNINGS ----------
        warnings = []
        high_missing_cols = df.columns[df.isna().mean() > 0.5].tolist()
        many_unique_cols = df.columns[df.nunique() > 50].tolist()
        if high_missing_cols:
            warnings.append(f"High missing data in columns: {', '.join(high_missing_cols)}")
        if many_unique_cols:
            warnings.append(f"Columns with >50 unique values: {', '.join(many_unique_cols)}")
        if not warnings:
            warnings.append("No major warnings detected.")

        # ---------- INIT README ----------
        readme_path = os.path.join("output", "README.md")
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

        # ---------- CREATE GRAPH FOLDER ----------
        graph_folder = os.path.join("output", "numeric_charts")
        os.makedirs(graph_folder, exist_ok=True)
        graph_paths = []

        # ---------- COLUMN INSIGHTS + GRAPHS ----------
        for col in df.columns:
            total = len(df[col])
            missing = df[col].isna().sum()
            missing_pct = round((missing / total) * 100, 2)
            unique = df[col].nunique(dropna=True)
            samples = df[col].dropna().unique()[:5]

            # ---------- README ----------
            with open(readme_path, "a", encoding="utf-8") as f:
                f.write(f"Column Name: {col}\n")
                f.write(f"Data Type: {df[col].dtype}\n")
                f.write(f"Total Values: {total}\n")
                f.write(f"Missing Values: {missing}\n")
                f.write(f"Missing Percentage: {missing_pct}%\n")
                f.write(f"Unique Values: {unique}\n")
                f.write(f"Sample Values: {', '.join(map(str, samples))}\n")

            # ---------- PDF ----------
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

            # ---------- NUMERIC COLUMN GRAPHS + MIN/MAX ----------
            if col in numeric_cols:
                series = df[col]
                min_value = series.min()
                max_value = series.max()

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

                graph_file = os.path.join(graph_folder, f"{col}.png")
                plt.savefig(graph_file)
                plt.close()
                graph_paths.append(graph_file)

                # Add min/max to README
                with open(readme_path, "a", encoding="utf-8") as f:
                    f.write(f"Minimum Value: {min_value}\n")
                    f.write(f"Maximum Value: {max_value}\n")
                    f.write(f"![{col}]({graph_file})\n\n")

                # Add min/max + graph to PDF
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, f"{col} Min & Max", ln=True)
                pdf.set_font("Arial", "", 11)
                pdf.cell(0, 7, f"Minimum Value: {min_value}", ln=True)
                pdf.cell(0, 7, f"Maximum Value: {max_value}", ln=True)
                pdf.ln(2)
                pdf.image(graph_file, x=10, y=None, w=180)
                pdf.ln(5)

        # ---------- STEP 3: DATASET HEALTH SCORE ----------
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write("\nDATASET HEALTH SCORE\n\n")
            f.write(f"Completeness Score: {summary['completeness']}%\n")
            f.write(f"Numeric Columns: {summary['numeric_count']} ({summary['numeric_ratio']}%)\n")
            f.write(f"Categorical Columns: {summary['categorical_count']} ({summary['categorical_ratio']}%)\n")
            f.write("Warnings:\n")
            for w in warnings:
                f.write(f"- {w}\n")

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "DATASET HEALTH SCORE", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"Completeness Score: {summary['completeness']}%", ln=True)
        pdf.cell(0, 8, f"Numeric Columns: {summary['numeric_count']} ({summary['numeric_ratio']}%)", ln=True)
        pdf.cell(0, 8, f"Categorical Columns: {summary['categorical_count']} ({summary['categorical_ratio']}%)", ln=True)
        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Warnings:", ln=True)
        pdf.set_font("Arial", "", 11)
        for w in warnings:
            pdf.multi_cell(0, 7, f"- {w}")
        pdf.ln(5)

        # ---------- SAVE PDF ----------
        pdf_file_path = os.path.join("output", "report.pdf")
        pdf.output(pdf_file_path)

        # ---------- STEP 4: CREATE ZIP ----------
        zip_path = os.path.join("output", "Auto_Documenter_Output.zip")
        with ZipFile(zip_path, 'w') as zipf:
            zipf.write(readme_path, arcname="README.md")
            zipf.write(pdf_file_path, arcname="report.pdf")
            for g in graph_paths:
                zipf.write(g, arcname=os.path.join("numeric_charts", os.path.basename(g)))

        return {"summary": summary, "graphs": graph_paths, "warnings": warnings, "zip_file": zip_path}

    except Exception as e:
        return {"error": str(e)}


# ---------- STREAMLIT APP ----------
st.title("📄 Auto-Documenter")
st.write("Upload a CSV, Excel, JSON, or Python file to automatically generate documentation.")

# Single uploader with unique key to avoid duplicate ID error
uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls", "json", "py"],
    key="unique_file_uploader"
)

if uploaded_file:
    st.info("Processing file... ⏳")

    # Save uploaded file temporarily
    os.makedirs("output", exist_ok=True)
    temp_path = os.path.join("output", uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Run analysis
    result = analyze_file(temp_path, uploaded_file.name)

    if "error" in result:
        st.error(result["error"])
    else:
        st.success("✅ File processed successfully!")
        st.json(result)

        # ---------- ZIP DOWNLOAD ----------
        zip_file = result.get("zip_file")
        if zip_file and os.path.exists(zip_file):
            with open(zip_file, "rb") as f:
                st.download_button(
                    label="Download All Outputs (ZIP)",
                    data=f,
                    file_name="Auto_Documenter_Output.zip",
                    mime="application/zip"
                )
