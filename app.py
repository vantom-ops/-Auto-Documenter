import streamlit as st
import pandas as pd
from parser import analyze_file  # your existing parser.py
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# ---------- HEADER ----------
st.markdown("""
# 📄 Auto-Documenter
Upload a CSV, Excel, JSON, or Python file to automatically generate documentation.
""")
st.markdown("---")

# ---------- SIDEBAR SETTINGS ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.number_input("Number of preview rows", min_value=5, max_value=50, value=10)
    show_graphs = st.checkbox("Show Column Graphs", value=True)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls", "json", "py"]
)

if uploaded_file:
    # ---------- FILE PREVIEW ----------
    try:
        if uploaded_file.name.endswith('.csv'):
            df_preview = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df_preview = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.json'):
            df_preview = pd.read_json(uploaded_file)
        else:
            df_preview = pd.DataFrame()  # for Python file, skip preview

        if not df_preview.empty:
            st.markdown("### 🔍 File Preview")
            st.dataframe(df_preview.head(preview_rows))
    except Exception as e:
        st.error(f"Error reading file: {e}")

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

            # ---------- FILE HEALTH ----------
            st.markdown("### 🩺 File Health Summary")
            summary = result.get("summary", {})
            cols = summary.get("columns", 0)
            rows = summary.get("rows", 0)
            st.metric("Rows", rows)
            st.metric("Columns", cols)

            numeric_count = len(df_preview.select_dtypes(include='number').columns)
            categorical_count = len(df_preview.select_dtypes(exclude='number').columns)
            st.metric("Numeric Columns", numeric_count)
            st.metric("Categorical Columns", categorical_count)

            completeness = round(df_preview.notna().sum().sum() / (rows*cols) * 100, 2) if rows and cols else 0
            st.metric("Completeness (%)", completeness)

            # ---------- SHOW GRAPHS ----------
            if show_graphs and result.get("graphs"):
                st.markdown("### 📊 Column Graphs")
                for g in result["graphs"]:
                    st.image(g, use_column_width=True)

            # ---------- DOWNLOAD PDF ----------
            pdf_path = "output/report.pdf"
            if os.path.exists(pdf_path):
                st.download_button(
                    label="📥 Download PDF",
                    data=open(pdf_path, "rb").read(),
                    file_name="report.pdf",
                    mime="application/pdf"
                )
