import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Auto-Documenter", layout="wide")

st.title("📄 Auto-Documenter")
st.caption("Stable base version – no blank screen")

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

        # ---- PREVIEW ----
        st.subheader("🔍 File Preview (First 10 Rows)")
        st.dataframe(df.head(10), use_container_width=True)

        # ---- METRICS ----
        rows, cols = df.shape
        completeness = round(df.notna().mean().mean() * 100, 2)

        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", rows)
        c2.metric("Columns", cols)
        c3.metric("Completeness %", completeness)

        # ---- COLUMN STATS ----
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

        if numeric_cols:
            st.subheader("📊 Column Statistics")
            stats = pd.DataFrame({
                "Min": df[numeric_cols].min(),
                "Max": df[numeric_cols].max(),
                "Average": df[numeric_cols].mean().round(2)
            })
            st.dataframe(stats)

        # ---- SIMPLE GRAPH ----
        if numeric_cols:
            st.subheader("📈 Sample Graph")
            fig, ax = plt.subplots()
            ax.plot(df[numeric_cols[0]])
            ax.set_title(numeric_cols[0])
            st.pyplot(fig)

    except Exception as e:
        st.error("❌ App crashed")
        st.exception(e)
