import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file
import os
from fpdf import FPDF
import io
import textwrap

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, JSON, or Python file to automatically generate documentation.")
st.markdown("---")

with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)
    show_corr = st.checkbox("Show Correlation Analysis", True)

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls", "json", "py"]
)

def safe_multicell(pdf, text, width=0, line_height=6):
    safe_text = ""
    for word in text.split(" "):
        if len(word) > 50:
            word = "\u200B".join([word[i:i+50] for i in range(0, len(word), 50)])
        safe_text += word + " "
    pdf.multi_cell(width, line_height, safe_text.strip())

if uploaded_file:
    # ---------- LOAD FILE ----------
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        df = pd.DataFrame()

    if not df.empty:
        st.markdown("## 🔍 File Preview")
        st.dataframe(df.head(preview_rows), use_container_width=True)

        # ---------- COLUMN DATATYPES ----------
        st.markdown("## 🗂 Column Data Types")
        col_types = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str)
        })
        st.dataframe(col_types, use_container_width=True)

        # ---------- BASIC METRICS ----------
        rows, cols = df.shape
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()
        completeness = round(df.notna().sum().sum() / (rows*cols) * 100, 2)
        duplicate_pct = round(df.duplicated().sum()/rows*100,2)

        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", rows)
        c2.metric("Columns", cols)
        c3.metric("Numeric", len(numeric_cols))
        c4.metric("Categorical", len(categorical_cols))

        # ---------- COLUMN STATISTICS ----------
        col_stats = []
        for col in numeric_cols:
            col_stats.append({
                "Column": col,
                "Min": df[col].min(),
                "Max": df[col].max(),
                "Avg": round(df[col].mean(),2)
            })
        st.markdown("## 📌 Column Statistics (Min, Max, Avg)")
        st.dataframe(pd.DataFrame(col_stats), use_container_width=True)

        # ---------- CORRELATION ----------
        if show_corr and len(numeric_cols)>1:
            st.markdown("## 🔥 Correlation Analysis")
            corr = df[numeric_cols].corr().round(3)
            fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📋 Correlation Table")
            st.dataframe(corr, use_container_width=True)

        # ---------- ML READINESS SCORE ----------
        ml_ready_score = round(
            (completeness*0.4)+((100-duplicate_pct)*0.3)+
            (min(len(numeric_cols)/cols,1)*100*0.15)+
            (min(len(categorical_cols)/cols,1)*100*0.15),2
        )
        st.markdown("## 🤖 ML Readiness Score + Algorithm Suggestions")
        st.metric("ML Readiness Score", f"{ml_ready_score}/100")
        if numeric_cols and len(numeric_cols)>1:
            st.write("- Linear Regression, Random Forest Regressor, Gradient Boosting")
        if categorical_cols:
            st.write("- Decision Tree, Random Forest Classifier, XGBoost, Logistic Regression")
        if numeric_cols and not categorical_cols:
            st.write("- KMeans, DBSCAN, Hierarchical Clustering")

        # ---------- PDF REPORT ----------
        st.markdown("## 📝 Download PDF Report")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial","",12)

        safe_multicell(pdf,"Auto-Documenter Report")
        pdf.ln(5)
        safe_multicell(pdf,f"Rows: {rows}\nColumns: {cols}\nNumeric: {len(numeric_cols)}\nCategorical: {len(categorical_cols)}")
        pdf.ln(2)

        safe_multicell(pdf,"Column Data Types:")
        for i,row in col_types.iterrows():
            safe_multicell(pdf,f"- {row['Column']}: {row['Data Type']}")

        pdf.ln(2)
        safe_multicell(pdf,"Column Statistics (Min, Max, Avg):")
        for stat in col_stats:
            safe_multicell(pdf,f"- {stat['Column']}: Min={stat['Min']}, Max={stat['Max']}, Avg={stat['Avg']}")

        if show_corr and len(numeric_cols)>1:
            pdf.ln(2)
            safe_multicell(pdf,"Correlation Table:")
            for i in corr.index:
                row_str = ", ".join([f"{j}:{corr.loc[i,j]}" for j in corr.columns])
                safe_multicell(pdf,f"{i}: {row_str}")

        pdf.ln(2)
        safe_multicell(pdf,f"ML Readiness Score: {ml_ready_score}/100")
        if numeric_cols and len(numeric_cols)>1:
            safe_multicell(pdf,"Suggested Algorithms (Numeric/Regression): Linear Regression, Random Forest Regressor, Gradient Boosting")
        if categorical_cols:
            safe_multicell(pdf,"Suggested Algorithms (Categorical/Classification): Decision Tree, Random Forest Classifier, XGBoost, Logistic Regression")
        if numeric_cols and not categorical_cols:
            safe_multicell(pdf,"Suggested Algorithms (Unsupervised/Clustering): KMeans, DBSCAN, Hierarchical Clustering")

        # Export PDF
        pdf_bytes = io.BytesIO()
        pdf.output(pdf_bytes)
        pdf_bytes.seek(0)

        st.download_button(
            label="⬇️⬇️ Download PDF Report ⬇️⬇️",
            data=pdf_bytes,
            file_name="Auto_Documenter_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
