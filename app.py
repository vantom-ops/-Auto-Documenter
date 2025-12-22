import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from parser import analyze_file
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, JSON, or Python file to automatically generate documentation.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.number_input(
        "Preview Rows",
        min_value=5,
        max_value=50,
        value=10
    )
    show_graphs = st.checkbox("Show Column Graphs", value=True)
    show_corr = st.checkbox("Show Correlation Heatmap", value=True)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls", "json", "py"]
)

if uploaded_file:

    # ---------- FILE PREVIEW ----------
    if uploaded_file.name.endswith(".csv"):
        df_preview = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df_preview = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df_preview = pd.read_json(uploaded_file)
    else:
        df_preview = pd.DataFrame()

    if not df_preview.empty:
        st.markdown("### 🔍 File Preview")
        st.dataframe(df_preview.head(preview_rows))

    # ---------- GENERATE BUTTON ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file... ⏳"):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = analyze_file(temp_path)

        if "error" in result:
            st.error(result["error"])
            st.stop()

        st.success("✅ Documentation generated successfully!")

        # ---------- BASIC STATS ----------
        rows = df_preview.shape[0]
        cols = df_preview.shape[1]
        numeric_cols = df_preview.select_dtypes(include="number").columns
        categorical_cols = df_preview.select_dtypes(exclude="number").columns

        completeness = round(
            (df_preview.notna().sum().sum() / (rows * cols)) * 100, 2
        ) if rows and cols else 0

        # ---------- METRICS ----------
        st.markdown("### 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📝 Rows", rows)
        c2.metric("📂 Columns", cols)
        c3.metric("🔢 Numeric", len(numeric_cols))
        c4.metric("🗂 Categorical", len(categorical_cols))

        # ---------- COMPLETENESS BAR ----------
        st.markdown("### ✅ Completeness (%)")
        st.markdown(
            f"""
            <div style="background:#eee;width:100%;height:26px;border-radius:6px;overflow:hidden;">
                <div style="height:26px;width:{completeness}%;
                background:linear-gradient(90deg, red, yellow, green);"></div>
            </div>
            <p style="text-align:center;font-weight:bold;">{completeness}% Complete</p>
            """,
            unsafe_allow_html=True
        )

        # ---------- WARNINGS ----------
        warnings = []
        for col in df_preview.columns:
            if df_preview[col].isna().mean() * 100 > 50:
                warnings.append(f"{col}: >50% missing values")
            if df_preview[col].nunique() > 50:
                warnings.append(f"{col}: too many unique values")

        if warnings:
            st.markdown("### ⚠ Warnings")
            for w in warnings:
                st.markdown(
                    f"<span style='color:red;font-weight:600;'>⚠ {w}</span>",
                    unsafe_allow_html=True
                )
        else:
            st.success("No major warnings detected ✅")

        # ---------- MIN / MAX VISUAL ----------
        st.markdown("### 📌 Column Min / Max Overview")
        for col in numeric_cols:
            series = df_preview[col].dropna()
            min_v, max_v, mean_v = series.min(), series.max(), series.mean()
            mean_pos = ((mean_v - min_v) / (max_v - min_v)) * 100 if max_v != min_v else 50

            st.markdown(f"**{col}**")
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="color:#1f77b4;">{min_v}</span>
                    <div style="position:relative;width:100%;height:16px;
                        background:#ddd;border-radius:8px;">
                        <div style="position:absolute;height:16px;width:100%;
                        background:linear-gradient(to right,#1f77b4,#2ca02c);
                        border-radius:8px;"></div>
                        <div style="position:absolute;left:{mean_pos}%;
                        height:16px;border-left:3px solid gold;"></div>
                    </div>
                    <span style="color:#2ca02c;">{max_v}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ---------- COLUMN GRAPHS ----------
        if show_graphs:
            with st.expander("📊 Column Graphs", expanded=True):
                for col in numeric_cols:
                    fig = px.line(df_preview, y=col, title=f"{col} Trend")
                    fig.add_hline(y=df_preview[col].min(), line_dash="dash", line_color="red")
                    fig.add_hline(y=df_preview[col].max(), line_dash="dash", line_color="green")
                    st.plotly_chart(fig, use_container_width=True)

        # ---------- CORRELATION ----------
        if show_corr and len(numeric_cols) > 1:
            with st.expander("🔥 Correlation Heatmap", expanded=True):
                corr = df_preview[numeric_cols].corr()
                st.markdown("#### Correlation Table")
                st.dataframe(
                    corr.style.background_gradient(cmap="coolwarm").format("{:.2f}")
                )

                st.markdown("#### Heatmap")
                plt.figure(figsize=(10, 6))
                sns.heatmap(corr, annot=True, cmap="coolwarm", linewidths=0.5)
                st.pyplot(plt)
                plt.close()

        # ---------- PDF DOWNLOAD ----------
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            st.download_button(
                "📥 Download PDF",
                data=open(pdf_path, "rb").read(),
                file_name="Auto_Documentation_Report.pdf",
                mime="application/pdf"
            )
