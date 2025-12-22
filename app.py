import streamlit as st
import pandas as pd
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
    preview_rows = st.slider("Preview Rows", 5, 50, 10)
    show_graphs = st.checkbox("Show Column Graphs", True)
    show_corr = st.checkbox("Show Correlation Heatmap", True)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls", "json", "py"],
    key="single_uploader"
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
        st.dataframe(df_preview.head(preview_rows), use_container_width=True)

    # ---------- PROCESS ----------
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

        summary = result["summary"]
        rows = summary["rows"]
        cols = summary["columns"]

        numeric_cols = df_preview.select_dtypes(include="number").columns
        cat_cols = df_preview.select_dtypes(exclude="number").columns

        completeness = round(
            df_preview.notna().sum().sum() / (rows * cols) * 100, 2
        )

        # ---------- METRICS ----------
        st.markdown("### 📊 Dataset Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rows", rows)
        m2.metric("Columns", cols)
        m3.metric("Numeric", len(numeric_cols))
        m4.metric("Categorical", len(cat_cols))

        # ---------- COMPLETENESS BAR ----------
        st.markdown("### ✅ Completeness")
        st.markdown(
            f"""
            <div style="width:100%;background:#ddd;border-radius:12px;">
                <div style="width:{completeness}%;
                background:linear-gradient(90deg,#ff4d4d,#ffa500,#2ecc71);
                padding:8px;border-radius:12px;
                text-align:center;color:black;font-weight:bold;">
                {completeness} %
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ---------- WARNINGS ----------
        st.markdown("### ⚠ Data Warnings")

        for col in df_preview.columns:
            miss_pct = round(df_preview[col].isna().mean() * 100, 2)

            if miss_pct > 30:
                color = "#ff4d4d" if miss_pct > 50 else "#ffa500"
                st.markdown(
                    f"""
                    <div style="margin-bottom:8px;">
                    <b>{col}</b> — Missing {miss_pct}%
                    <div style="width:100%;background:#eee;border-radius:8px;">
                        <div style="width:{miss_pct}%;
                        background:{color};
                        padding:4px;border-radius:8px;">
                        </div>
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # ---------- MIN / AVG / MAX ----------
        st.markdown("### 📌 Column Min / Average / Max")

        for col in numeric_cols:
            s = df_preview[col].dropna()

            min_v = round(s.min(), 3)
            avg_v = round(s.mean(), 3)
            max_v = round(s.max(), 3)

            avg_pos = ((avg_v - min_v) / (max_v - min_v)) * 100 if max_v != min_v else 50

            st.markdown(f"**{col}**")
            a, b, c = st.columns(3)
            a.metric("Min", min_v)
            b.metric("Average", avg_v)
            c.metric("Max", max_v)

            st.markdown(
                f"""
                <div style="position:relative;width:100%;height:18px;
                background:#ddd;border-radius:10px;margin-bottom:20px;">
                    <div style="position:absolute;width:100%;height:18px;
                    background:linear-gradient(to right,#1f77b4,#2ca02c);
                    border-radius:10px;"></div>
                    <div style="position:absolute;left:{avg_pos}%;
                    height:22px;border-left:4px solid gold;top:-2px;"></div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ---------- INTERACTIVE GRAPHS ----------
        if show_graphs:
            st.markdown("### 📈 Interactive Column Graphs")
            for col in numeric_cols:
                fig = px.line(df_preview, y=col, title=col)
                st.plotly_chart(fig, use_container_width=True)

        # ---------- CORRELATION HEATMAP ----------
        if show_corr and len(numeric_cols) > 1:
            st.markdown("### 🔥 Correlation Heatmap")
            corr = df_preview[numeric_cols].corr()
            fig = px.imshow(
                corr,
                text_auto=True,
                color_continuous_scale="RdBu_r"
            )
            st.plotly_chart(fig, use_container_width=True)

        # ---------- DOWNLOAD PDF ----------
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            st.download_button(
                "📥 Download PDF",
                data=open(pdf_path, "rb").read(),
                file_name="Auto_Documenter_Report.pdf",
                mime="application/pdf"
            )
