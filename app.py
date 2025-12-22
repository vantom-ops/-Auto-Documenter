import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="Auto-Documenter", layout="wide")

st.title("📄 Auto-Documenter")
st.caption("Stable build with correlation analysis")

uploaded_file = st.file_uploader(
    "Upload CSV or Excel",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("File loaded successfully")

        # ---------- PREVIEW ----------
        st.subheader("🔍 File Preview (First 10 Rows)")
        st.dataframe(df.head(10), use_container_width=True)

        # ---------- METRICS ----------
        rows, cols = df.shape
        completeness = round(df.notna().mean().mean() * 100, 2)

        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", rows)
        c2.metric("Columns", cols)
        c3.metric("Completeness %", completeness)

        # ---------- NUMERIC COLUMNS ----------
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

        # ---------- COLUMN STATS ----------
        if numeric_cols:
            st.subheader("📊 Column Statistics")
            stats = pd.DataFrame({
                "Min": df[numeric_cols].min(),
                "Max": df[numeric_cols].max(),
                "Average": df[numeric_cols].mean().round(2)
            })
            st.dataframe(stats, use_container_width=True)

        # ---------- CORRELATION ----------
        if len(numeric_cols) > 1:
            st.subheader("🔥 Correlation Analysis")

            corr = df[numeric_cols].corr().round(3)

            # Heatmap
            fig = px.imshow(
                corr,
                text_auto=True,
                color_continuous_scale="RdBu_r",
                title="Correlation Heatmap"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Table
            st.subheader("📋 Correlation Table")
            st.dataframe(corr, use_container_width=True)

            # Strong correlations
            st.subheader("⚠ Strong Correlations (> 0.7)")
            found = False
            for i in corr.columns:
                for j in corr.columns:
                    if i != j and abs(corr.loc[i, j]) > 0.7:
                        st.warning(f"{i} ↔ {j} = {corr.loc[i, j]}")
                        found = True
            if not found:
                st.success("No strong correlations detected")

        # ---------- SIMPLE GRAPH ----------
        if numeric_cols:
            st.subheader("📈 Sample Trend")
            fig2, ax = plt.subplots()
            ax.plot(df[numeric_cols[0]])
            ax.set_title(numeric_cols[0])
            st.pyplot(fig2)

    except Exception as e:
        st.error("❌ App crashed")
        st.exception(e)
