import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from parser import analyze_file
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="📄 Auto-Documenter", page_icon="📊", layout="wide")

# ---------- THEME ----------
theme = st.sidebar.radio("🌗 Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("<style>body{background-color:#222;color:white;}</style>", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, JSON, or Python file to automatically generate documentation.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.number_input("Preview Rows", min_value=5, max_value=50, value=10)
    show_graphs = st.checkbox("Show Column Graphs", value=True)
    show_corr = st.checkbox("Show Correlation Heatmap & Table", value=True)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json", "py"])

if uploaded_file:
    # ---------- FILE PREVIEW ----------
    if uploaded_file.name.endswith('.csv'):
        df_preview = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xlsx', '.xls')):
        df_preview = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith('.json'):
        df_preview = pd.read_json(uploaded_file)
    else:
        df_preview = pd.DataFrame()  # Python file

    if not df_preview.empty:
        st.markdown("### 🔍 File Preview")
        st.dataframe(df_preview.head(preview_rows))

    # ---------- GENERATE DOCUMENTATION ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file... ⏳"):
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            os.makedirs("temp_upload", exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)

        if "error" in result:
            st.error(result["error"])
        else:
            st.success("✅ Documentation generated successfully!")

            summary = result.get("summary", {})
            rows = summary.get("rows", 0)
            cols = summary.get("columns", 0)
            numeric_cols = df_preview.select_dtypes(include='number').columns
            numeric_count = len(numeric_cols)
            categorical_count = len(df_preview.select_dtypes(exclude='number').columns)
            completeness = round(df_preview.notna().sum().sum() / (rows*cols) * 100, 2) if rows and cols else 0

            # ---------- METRIC CARDS ----------
            st.markdown("### 📊 Dataset Metrics")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📝 Rows", rows)
            col2.metric("📂 Columns", cols)
            col3.metric("🔢 Numeric Columns", numeric_count)
            col4.metric("🗂 Categorical Columns", categorical_count)
            st.metric("✅ Completeness (%)", completeness)

            # ---------- WARNINGS ----------
            warnings = []
            warning_data = []
            for col in df_preview.columns:
                missing_pct = df_preview[col].isna().sum() / rows * 100
                if df_preview[col].nunique() > 50:
                    warnings.append(f"{col} has >50 unique values")
                    warning_data.append({"Column": col, "Type": "High Unique Values", "Percentage": 100})
                if missing_pct > 50:
                    warnings.append(f"{col} has >50% missing values")
                    warning_data.append({"Column": col, "Type": "High Missing Values", "Percentage": missing_pct})

            if warnings:
                st.markdown("### ⚠ Warnings (Percentage Bar)")
                for w in warning_data:
                    st.markdown(f"""
                        <div style="margin-bottom:5px; font-weight:bold">{w['Column']} - {w['Type']}</div>
                        <div style="background-color:#ddd; border-radius:5px; height:20px; width:100%;">
                            <div style="background-color:#ff4c4c; width:{w['Percentage']}%; height:100%; border-radius:5px;"></div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No major warnings detected ✅")

            # ---------- WARNINGS ----------
warnings = []
warning_data = []
for col in df_preview.columns:
    missing_pct = df_preview[col].isna().sum() / rows * 100
    if df_preview[col].nunique() > 50:
        warnings.append(f"{col} has >50 unique values")
        warning_data.append({"Column": col, "Type": "High Unique Values", "Percentage": 100})
    if missing_pct > 50:
        warnings.append(f"{col} has >50% missing values")
        warning_data.append({"Column": col, "Type": "High Missing Values", "Percentage": missing_pct})

if warnings:
    st.markdown("### ⚠ Warnings (Percentage Bar with Severity)")
    for w in warning_data:
        # Determine color based on percentage
        pct = w['Percentage']
        if pct < 50:
            color = "#ffeb3b"  # yellow
        elif pct < 75:
            color = "#ff9800"  # orange
        else:
            color = "#ff4c4c"  # red

        st.markdown(f"""
            <div style="margin-bottom:5px; font-weight:bold">{w['Column']} - {w['Type']}</div>
            <div style="background-color:#ddd; border-radius:5px; height:20px; width:100%;">
                <div style="background-color:{color}; width:{pct}%; height:100%; border-radius:5px;"></div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.success("No major warnings detected ✅")


            # ---------- COLUMN GRAPHS ----------
            if show_graphs and result.get("graphs"):
                with st.expander("📊 Column Graphs", expanded=True):
                    for col in numeric_cols:
                        fig = px.line(df_preview, y=col, title=f"{col} Interactive Graph", labels={"index": "Index"})
                        st.plotly_chart(fig, use_container_width=True)

            # ---------- CORRELATION HEATMAP + TABLE ----------
            if show_corr and numeric_count > 1:
                with st.expander("🔥 Correlation Heatmap & Table", expanded=True):
                    plt.figure(figsize=(10, 6))
                    corr = df_preview[numeric_cols].corr()
                    sns.heatmap(corr, annot=True, cmap="coolwarm", linewidths=0.5)
                    st.pyplot(plt)
                    plt.close()

                    st.markdown("#### 🔢 Correlation Table")
                    st.dataframe(corr.style.background_gradient(cmap="coolwarm"))

            # ---------- DOWNLOAD PDF ----------
            pdf_path = "output/report.pdf"
            if os.path.exists(pdf_path):
                st.download_button(
                    label="📥 Download PDF",
                    data=open(pdf_path, "rb").read(),
                    file_name="report.pdf",
                    mime="application/pdf"
                )

