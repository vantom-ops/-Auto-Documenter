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
    preview_rows = st.number_input("Preview Rows", min_value=5, max_value=50, value=10, help="Number of rows to preview in the table")
    show_graphs = st.checkbox("Show Column Graphs", value=True, help="Display interactive graphs for numeric columns")
    show_corr = st.checkbox("Show Correlation Heatmap", value=True, help="Display heatmap of correlations between numeric columns")

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
            for col in df_preview.columns:
                if df_preview[col].nunique() > 50:
                    warnings.append(f"Column '{col}' has >50 unique values")
                if df_preview[col].isna().sum() / rows * 100 > 50:
                    warnings.append(f"Column '{col}' has >50% missing values")
            if warnings:
                st.markdown("### ⚠ Warnings")
                for w in warnings:
                    st.markdown(f"<span style='color:red; font-weight:bold;'>{w}</span>", unsafe_allow_html=True)
            else:
                st.success("No major warnings detected ✅")

            # ---------- COLUMN MIN/MAX (Attractive) ----------
            st.markdown("### 📌 Column Min/Max")
            for col in numeric_cols:
                series = df_preview[col]
                min_val = series.min()
                max_val = series.max()
                
                col1, col2, col3 = st.columns([1, 4, 1])
                col1.markdown(f"**{col}**")
                col2.markdown(
                    f"""
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="color:blue;">Min: {min_val}</span>
                        <div style="background:#eee; width:100%; height:15px; border-radius:5px; overflow:hidden;">
                            <div style="background:linear-gradient(to right, blue 0%, green 100%); height:15px;"></div>
                        </div>
                        <span style="color:green;">Max: {max_val}</span>
                    </div>
                    """, unsafe_allow_html=True
                )
                col3.empty()

            # ---------- COLUMN GRAPHS ----------
            if show_graphs and result.get("graphs"):
                with st.expander("📊 Column Graphs", expanded=True):
                    for col in numeric_cols:
                        fig = px.line(df_preview, y=col, title=f"{col} Interactive Graph", labels={"index": "Index"})
                        st.plotly_chart(fig, use_container_width=True)

            # ---------- CORRELATION HEATMAP ----------
            if show_corr and numeric_count > 1:
                with st.expander("🔥 Correlation Heatmap", expanded=True):
                    corr_df = df_preview[numeric_cols].corr()
                    st.dataframe(corr_df.style.background_gradient(cmap="coolwarm").format("{:.2f}"))

                    plt.figure(figsize=(10, 6))
                    sns.heatmap(corr_df, annot=True, cmap="coolwarm", linewidths=0.5)
                    st.pyplot(plt)
                    plt.close()

            # ---------- DOWNLOAD PDF ----------
            pdf_path = "output/report.pdf"
            if os.path.exists(pdf_path):
                st.download_button(
                    label="📥 Download PDF",
                    data=open(pdf_path, "rb").read(),
                    file_name="report.pdf",
                    mime="application/pdf"
                )
