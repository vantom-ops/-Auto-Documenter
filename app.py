import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from fpdf import FPDF
import io

st.set_page_config(page_title="Auto Data Analyzer", layout="wide")

st.title("📊 Auto Data Analyzer")

# ----------------- Upload Data -----------------
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File loaded successfully!")
    st.write("Preview of your data:", df.head())

    # ----------------- 1️⃣ Data Health Score -----------------
    st.header("1️⃣ Data Health Score")
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()
    
    missing_pct = df.isnull().mean() * 100
    unique_pct = df.nunique() / len(df) * 100
    completeness_score = 100 - missing_pct.mean()
    uniqueness_score = unique_pct.mean()
    health_score = (completeness_score + uniqueness_score) / 2

    st.subheader("Radar Chart")
    labels = ['Completeness', 'Uniqueness']
    stats = [completeness_score, uniqueness_score]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats += stats[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(5,5), subplot_kw=dict(polar=True))
    ax.plot(angles, stats, 'o-', linewidth=2)
    ax.fill(angles, stats, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_title(f"Data Health Score: {health_score:.2f}%")
    st.pyplot(fig)

    # ----------------- 2️⃣ Auto AI-style Insights -----------------
    st.header("2️⃣ Auto AI-style Insights (Executive Summary)")
    summary = f"Your dataset has {df.shape[0]} rows and {df.shape[1]} columns.\n\n"
    summary += f"- Numeric columns: {numeric_cols}\n"
    summary += f"- Categorical columns: {categorical_cols}\n"
    summary += f"- Average missing values per column: {missing_pct.mean():.2f}%\n"
    summary += f"- Average uniqueness percentage: {uniqueness_score:.2f}%\n"
    
    # Example of correlation insight
    if numeric_cols:
        corr_matrix = df[numeric_cols].corr()
        high_corr = corr_matrix.abs().unstack().sort_values(ascending=False)
        high_corr = high_corr[high_corr < 1].drop_duplicates()
        top_corr = high_corr.head(3)
        summary += f"- Top correlations:\n{top_corr}\n"

    st.text_area("Executive Summary", summary, height=200)

    # ----------------- 3️⃣ ML Readiness + Algorithm Suggestion -----------------
    st.header("3️⃣ ML Readiness Score + Algorithm Suggestions")
    ml_ready_score = health_score
    st.write(f"ML Readiness Score: {ml_ready_score:.2f}%")
    
    # Suggest algorithms based on column types
    if numeric_cols and len(numeric_cols) > 1:
        st.subheader("Suggested ML Algorithms (Regression / Clustering)")
        st.write("- Linear Regression, Random Forest Regressor (numeric target)")
        st.write("- KMeans, DBSCAN (unsupervised clustering)")
    if categorical_cols:
        st.subheader("Suggested ML Algorithms (Classification)")
        st.write("- Decision Tree, Random Forest Classifier, XGBoost")

    # ----------------- 4️⃣ PDF Export -----------------
    st.header("4️⃣ Export Report as PDF")
    if st.button("Generate PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Auto Data Analyzer Report", ln=True, align="C")
        pdf.set_font("Arial", '', 12)
        pdf.ln(10)
        
        # Add Data Health Score
        pdf.cell(0, 10, f"Data Health Score: {health_score:.2f}%", ln=True)
        pdf.cell(0, 10, f"Completeness: {completeness_score:.2f}%", ln=True)
        pdf.cell(0, 10, f"Uniqueness: {uniqueness_score:.2f}%", ln=True)
        pdf.ln(5)

        # Add Summary
        pdf.multi_cell(0, 6, summary)
        pdf.ln(5)
        pdf.multi_cell(0, 6, "ML Readiness Score: {:.2f}%".format(ml_ready_score))
        
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        st.download_button("📥 Download PDF", data=pdf_output, file_name="data_report.pdf", mime="application/pdf")
