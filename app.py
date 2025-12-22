import streamlit as st
import pandas as pd
import numpy as np
from parser import analyze_file  # your phraiser.py or parser.py
import io
import os
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import seaborn as sns

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate documentation and PDF report.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type!")
        st.stop()

    st.markdown("## 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    # ---------- GENERATE METRICS & PDF ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file..."):
            # Save temp file for parser
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Call parser
            result = analyze_file(temp_path)

        if "error" in result:
            st.error(f"Error: {result['error']}")
            st.stop()

        # ---------- DISPLAY METRICS ----------
        st.success("✅ Documentation generated successfully!")

        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric Columns", result['numeric_count'])
        c4.metric("Categorical Columns", result['categorical_count'])

        st.markdown("## 📌 Column Datatypes")
        col_types = pd.Series(df.dtypes).astype(str)
        for col, dtype in col_types.items():
            st.write(f"- **{col}**: {dtype}")

        # ---------- CALCULATE ADDITIONAL METRICS ----------
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        # Column min, max, avg
        st.markdown("## 📈 Column Statistics (Min, Max, Avg)")
        col_stats = pd.DataFrame(columns=["Column", "Min", "Max", "Avg"])
        for col in numeric_cols:
            col_min = df[col].min()
            col_max = df[col].max()
            col_avg = round(df[col].mean(), 2)
            col_stats = pd.concat([col_stats, pd.DataFrame([[col, col_min, col_max, col_avg]], columns=col_stats.columns)])
        st.dataframe(col_stats, use_container_width=True)

        # Correlation table
        st.markdown("## 🔗 Correlation Table")
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr().round(2)
            st.dataframe(corr, use_container_width=True)

            # Correlation heatmap
            fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
            st.plotly_chart(fig, use_container_width=True)

        # Warnings: % missing values per column
        st.markdown("## ⚠ Missing Values % per Column")
        missing_pct = (df.isna().sum() / len(df) * 100).round(2)
        st.dataframe(missing_pct, use_container_width=True)

        # ML readiness score (example formula)
        completeness = round(100 - missing_pct.mean(), 2)
        duplicate_pct = round(df.duplicated().mean() * 100, 2)
        ml_ready_score = round(
            (completeness * 0.4) + ((100 - duplicate_pct) * 0.3) +
            (min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.15) +
            (min(len(categorical_cols)/df.shape[1], 1) * 100 * 0.15),
            2
        )

        st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")
        st.metric("ML Readiness Score", f"{ml_ready_score}/100")
        if numeric_cols and len(numeric_cols) > 1:
            st.write("- Regression Algorithms: Linear Regression, Random Forest Regressor, Gradient Boosting")
        if categorical_cols:
            st.write("- Classification Algorithms: Decision Tree, Random Forest, XGBoost, Logistic Regression")
        if numeric_cols and not categorical_cols:
            st.write("- Unsupervised/Clustering: KMeans, DBSCAN, Hierarchical Clustering")

        # ---------- PDF REPORT ----------
        st.markdown("## 📝 PDF Report")
        os.makedirs("output", exist_ok=True)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Auto-Documenter Report", ln=True, align="C")
        pdf.ln(5)

        # Dataset metrics
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, f"Rows: {result['summary']['rows']}\nColumns: {result['summary']['columns']}\nNumeric: {result['numeric_count']}\nCategorical: {result['categorical_count']}\n")
        pdf.ln(2)

        # Column stats
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Column Statistics (Min, Max, Avg)", ln=True)
        pdf.set_font("Arial", "", 12)
        for _, row in col_stats.iterrows():
            pdf.multi_cell(0, 6, f"{row['Column']}: Min={row['Min']}, Max={row['Max']}, Avg={row['Avg']}")

        # Correlation table
        if len(numeric_cols) > 1:
            pdf.ln(2)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 8, "Correlation Table", ln=True)
            pdf.set_font("Arial", "", 12)
            for i in corr.index:
                line = ", ".join([f"{j}: {corr.loc[i,j]}" for j in corr.columns])
                pdf.multi_cell(0, 6, f"{i}: {line}")

        # Warnings
        pdf.ln(2)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Warnings (Missing %)", ln=True)
        pdf.set_font("Arial", "", 12)
        for col, pct in missing_pct.items():
            pdf.multi_cell(0, 6, f"{col}: {pct}%")

        # ML readiness
        pdf.ln(2)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, f"ML Readiness Score: {ml_ready_score}/100", ln=True)
        pdf.set_font("Arial", "", 12)
        if numeric_cols and len(numeric_cols) > 1:
            pdf.multi_cell(0, 6, "Suggested Regression Algorithms: Linear Regression, Random Forest Regressor, Gradient Boosting")
        if categorical_cols:
            pdf.multi_cell(0, 6, "Suggested Classification Algorithms: Decision Tree, Random Forest, XGBoost, Logistic Regression")
        if numeric_cols and not categorical_cols:
            pdf.multi_cell(0, 6, "Suggested Unsupervised/Clustering Algorithms: KMeans, DBSCAN, Hierarchical Clustering")

        # Save PDF
        pdf_path = os.path.join("output", "report.pdf")
        pdf.output(pdf_path)

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Download Full PDF Report",
                data=pdf_bytes,
                file_name="Auto_Documenter_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("PDF not found. Something went wrong in generation.")
