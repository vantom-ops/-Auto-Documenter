import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
import os
import tempfile

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    layout="wide"
)

st.title("📄 Auto-Documenter")
st.caption("Upload a dataset and get instant data health, insights & ML readiness")

# ---------------- FILE UPLOADER ----------------
uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx", "xls"]
)

# ---------------- HELPERS ----------------
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

def generate_pdf(summary_text, tables):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Auto-Documenter Report", ln=True)

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 8, summary_text)

    for title, df in tables.items():
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Arial", size=8)

        for col in df.columns:
            pdf.cell(40, 8, str(col), border=1)
        pdf.ln()

        for _, row in df.head(10).iterrows():
            for val in row:
                pdf.cell(40, 8, str(val), border=1)
            pdf.ln()

    path = os.path.join(tempfile.gettempdir(), "auto_documenter_report.pdf")
    pdf.output(path)
    return path

# ---------------- MAIN ----------------
if uploaded_file:
    df = load_data(uploaded_file)

    rows, cols = df.shape
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # ---------------- PREVIEW ----------------
    st.subheader("🔍 File Preview (First 10 Rows)")
    st.dataframe(df.head(10), use_container_width=True)

    # ---------------- METRICS ----------------
    completeness = round(df.notna().sum().sum() / (rows * cols) * 100, 2)
    duplicate_pct = round(df.duplicated().mean() * 100, 2)

    st.subheader("📊 Dataset Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", rows)
    c2.metric("Columns", cols)
    c3.metric("Completeness %", completeness)
    c4.metric("Duplicates %", duplicate_pct)

    # ---------------- DATA HEALTH SCORE ----------------
    health_score = int(
        completeness * 0.5 +
        (100 - duplicate_pct) * 0.2 +
        (len(numeric_cols) / max(cols,1)) * 100 * 0.3
    )

    st.subheader("🩺 Overall Data Health Score")
    st.progress(health_score / 100)
    st.success(f"Score: {health_score}/100")

    # ---------------- COLUMN STATS (DROPDOWN) ----------------
    with st.expander("📌 Column Statistics (Min / Max / Avg)"):
        stats = []
        for col in numeric_cols:
            stats.append([
                col,
                df[col].min(),
                df[col].max(),
                round(df[col].mean(), 2)
            ])

        stats_df = pd.DataFrame(
            stats,
            columns=["Column", "Min", "Max", "Average"]
        )
        st.dataframe(stats_df, use_container_width=True)

    # ---------------- COLUMN GRAPHS ----------------
    with st.expander("📈 Column Graphs"):
        for col in numeric_cols[:5]:
            fig, ax = plt.subplots()
            ax.plot(df[col])
            ax.set_title(col)
            st.pyplot(fig)

    # ---------------- CORRELATION ----------------
    strong_corrs = []
    if len(numeric_cols) > 1:
        with st.expander("🔥 Correlation Analysis"):
            corr = df[numeric_cols].corr()

            fig, ax = plt.subplots(figsize=(6,4))
            cax = ax.matshow(corr, cmap="coolwarm")
            plt.colorbar(cax)
            ax.set_xticks(range(len(corr.columns)))
            ax.set_yticks(range(len(corr.columns)))
            ax.set_xticklabels(corr.columns, rotation=90)
            ax.set_yticklabels(corr.columns)
            st.pyplot(fig)

            st.subheader("📋 Correlation Table")
            st.dataframe(corr.round(2))

            for i in corr.columns:
                for j in corr.columns:
                    if i != j and abs(corr.loc[i,j]) > 0.7:
                        strong_corrs.append((i,j,round(corr.loc[i,j],2)))

    if strong_corrs:
        with st.expander("🔗 Strong Correlations (>0.7)"):
            for a,b,v in strong_corrs:
                st.warning(f"{a} ↔ {b} = {v}")

    # ---------------- ML READINESS ----------------
    st.subheader("🤖 ML Readiness Score")
    ml_score = int(
        health_score * 0.6 +
        (len(numeric_cols)/max(cols,1))*100*0.4
    )
    st.progress(ml_score / 100)
    st.info(f"Model Readiness: {ml_score}/100")

    # ---------------- ML SUGGESTIONS ----------------
    st.subheader("🧠 Suggested ML Algorithms")
    if ml_score > 80:
        st.success("Linear Regression, Random Forest, XGBoost")
    elif ml_score > 60:
        st.warning("Decision Trees, Logistic Regression")
    else:
        st.error("Heavy preprocessing needed before ML")

    # ---------------- FEATURE IMPORTANCE (SIMULATED) ----------------
    if numeric_cols:
        st.subheader("⭐ Feature Importance (Simulated)")
        importance = pd.DataFrame({
            "Feature": numeric_cols,
            "Importance": np.random.rand(len(numeric_cols))
        }).sort_values("Importance", ascending=False)

        st.bar_chart(importance.set_index("Feature"))

    # ---------------- AUTO EXECUTIVE SUMMARY ----------------
    summary = f"""
Dataset contains {rows} rows and {cols} columns.
Completeness is {completeness}%.
Overall health score is {health_score}/100.
ML readiness score is {ml_score}/100.
"""

    st.subheader("📘 Auto Executive Summary")
    st.info(summary)

    # ---------------- PDF EXPORT ----------------
    pdf_path = generate_pdf(
        summary,
        {
            "Column Statistics": stats_df,
            "Correlation Table": corr.round(2) if len(numeric_cols)>1 else stats_df
        }
    )

    st.markdown("## 📥 Export Report")
    st.download_button(
        "⬇ DOWNLOAD FULL PDF REPORT",
        data=open(pdf_path,"rb").read(),
        file_name="Auto_Documenter_Report.pdf",
        mime="application/pdf"
    )
