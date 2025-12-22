import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate documentation with metrics, insights, and PDF report.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)
    show_graphs = st.checkbox("Show Column Graphs", True)
    show_corr = st.checkbox("Show Correlation Analysis", True)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:

    # ---------- LOAD FILE ----------
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

    # ---------- METRICS ----------
    rows, cols = df.shape
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()
    col_types = df.dtypes.astype(str)

    completeness = round(df.notna().sum().sum() / (rows * cols) * 100, 2)
    duplicate_pct = round(df.duplicated().sum() / rows * 100, 2)

    st.markdown("## 📊 Dataset Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", rows)
    c2.metric("Columns", cols)
    c3.metric("Numeric", len(numeric_cols))
    c4.metric("Categorical", len(categorical_cols))

    # ---------- COLUMN STATISTICS ----------
    st.markdown("## 📌 Column Statistics (Min, Max, Avg, Datatype)")
    for col in df.columns:
        if col in numeric_cols:
            st.write(f"- **{col}** ({col_types[col]}): Min={df[col].min()}, Max={df[col].max()}, Avg={round(df[col].mean(),2)}")
        else:
            st.write(f"- **{col}** ({col_types[col]}): Non-numeric column")

    # ---------- CORRELATION ----------
    if show_corr and len(numeric_cols) > 1:
        st.markdown("## 🔥 Correlation Analysis")
        corr = df[numeric_cols].corr().round(3)
        fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
        st.plotly_chart(fig_corr, use_container_width=True)
        st.markdown("### 📋 Correlation Table")
        st.dataframe(corr, use_container_width=True)

    # ---------- ML READINESS SCORE & ALGORITHM SUGGESTIONS ----------
    st.markdown("## 🤖 ML Readiness Score + Algorithm Suggestions")
    ml_score = round(
        (completeness*0.4) + ((100-duplicate_pct)*0.3) +
        (min(len(numeric_cols)/cols,1)*100*0.15) +
        (min(len(categorical_cols)/cols,1)*100*0.15),2
    )
    st.metric("ML Readiness Score", f"{ml_score} / 100")

    st.markdown("### Suggested Algorithms")
    if numeric_cols and len(numeric_cols) > 1:
        st.write("- Regression: Linear Regression, Random Forest Regressor, Gradient Boosting")
    if categorical_cols:
        st.write("- Classification: Decision Tree, Random Forest Classifier, XGBoost, Logistic Regression")
    if numeric_cols and not categorical_cols:
        st.write("- Clustering: KMeans, DBSCAN, Hierarchical Clustering")

    # ---------- PDF REPORT ----------
    st.markdown("## 📝 Generate Full PDF Report")

    def generate_pdf(df, numeric_cols, categorical_cols, col_types, ml_score):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Auto-Documenter Report", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, f"Rows: {df.shape[0]}\nColumns: {df.shape[1]}\nNumeric Columns: {len(numeric_cols)}\nCategorical Columns: {len(categorical_cols)}")
        pdf.ln(2)
        pdf.multi_cell(0, 6, f"ML Readiness Score: {ml_score} / 100")
        pdf.ln(2)

        pdf.multi_cell(0, 6, "Column Statistics (Min/Max/Avg/Datatype):")
        for col in df.columns:
            if col in numeric_cols:
                text = f"- {col} ({col_types[col]}): Min={df[col].min()}, Max={df[col].max()}, Avg={round(df[col].mean(),2)}"
            else:
                text = f"- {col} ({col_types[col]}): Non-numeric column"
            pdf.multi_cell(0, 6, text)

        if len(numeric_cols) > 1:
            pdf.ln(2)
            pdf.multi_cell(0, 6, "Correlation Table (numeric columns):")
            corr = df[numeric_cols].corr().round(3)
            pdf.multi_cell(0, 6, corr.to_string())

        return pdf

    pdf = generate_pdf(df, numeric_cols, categorical_cols, col_types, ml_score)
    pdf_bytes = io.BytesIO()
    pdf.output(pdf_bytes)
    pdf_bytes.seek(0)

    st.download_button(
        label="📥 Download Full PDF Report",
        data=pdf_bytes,
        file_name="Auto_Documenter_Report.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="download_pdf"
    )
