import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
st.markdown("Upload a CSV, Excel, or JSON file to generate interactive documentation.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # 1. Read the file for the preview
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type!")
        st.stop()

    st.markdown("## 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    # ---------- GENERATE METRICS ----------
    if st.button("🚀 Generate Documentation"):
        with st.spinner("Processing file and creating PDF..."):
            # Ensure temp directory exists
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Call your parser.py function
            result = analyze_file(temp_path)

        if "error" in result:
            st.error(f"Error: {result['error']}")
            st.stop()

        # Save result to session state so it persists after download clicks
        st.session_state['analysis_result'] = result
        st.success("✅ Documentation generated successfully!")

    # Check if we have results to display
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']

        # ---------- DOWNLOAD SECTION ----------
        st.markdown("## 📥 Export Report")
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📩 Download Full PDF Report",
                    data=f,
                    file_name=f"Documentation_Report_{uploaded_file.name}.pdf",
                    mime="application/pdf"
                )

        # ---------- DISPLAY METRICS ----------
        st.markdown("## 📊 Dataset Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", result['summary']['rows'])
        c2.metric("Columns", result['summary']['columns'])
        c3.metric("Numeric Columns", result['numeric_count'])
        c4.metric("Categorical Columns", result['categorical_count'])

        # ---------- COLUMN DATATYPES ----------
        st.markdown("## 📌 Column Datatypes")
        col_types = pd.Series(df.dtypes).astype(str)
        type_df = pd.DataFrame(list(col_types.items()), columns=["Column", "Data Type"])
        st.dataframe(type_df, use_container_width=True)

        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        # ---------- MIN / AVG / MAX GRADIENT BAR ----------
        st.markdown("## 📈 Column Statistics")
        for col in numeric_cols:
            min_val = df[col].min()
            avg_val = round(df[col].mean(), 2)
            max_val = df[col].max()

            st.markdown(f"**{col}**")
            st.markdown(f"""
            <div style="display:flex; gap:4px; margin-bottom:4px;">
                <div style="flex:1; background:linear-gradient(to right, #ff4b4b, #ff9999); height:20px;"></div>
                <div style="flex:1; background:linear-gradient(to right, #ffea00, #ffd700); height:20px;"></div>
                <div style="flex:1; background:linear-gradient(to right, #00ff4b, #00cc33); height:20px;"></div>
            </div>
            <div style="margin-bottom:10px;">Red: Min ({min_val}) | Yellow: Avg ({avg_val}) | Green: Max ({max_val})</div>
            """, unsafe_allow_html=True)

        # ---------- FIXED COLUMN GRAPHS ----------
        with st.expander("📊 Column Graphs (Interactive)"):
            # FIX 1: Filter out constant columns (like Magnitude)
            valid_graph_cols = [c for c in numeric_cols if df[c].nunique() > 1]
            
            if valid_graph_cols:
                selected_col = st.selectbox("Select column to view trend:", valid_graph_cols)
                
                # FIX 2: Handle Period/Timeline formatting
                temp_df = df.copy()
                x_axis = None
                
                # If 'Period' or 'Year' exists, use it as X-axis and treat as string to avoid decimal gaps
                time_cols = [c for c in df.columns if c.lower() in ['period', 'year', 'date']]
                if time_cols:
                    x_axis = time_cols[0]
                    temp_df[x_axis] = temp_df[x_axis].astype(str)
                
                fig = px.line(temp_df, x=x_axis, y=selected_col, title=f"{selected_col} Trend")
                
                # FIX 3: Clean up Y-axis formatting for years
                if "year" in selected_col.lower():
                    fig.update_layout(yaxis=dict(tickformat="d"))
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No variable numeric columns available for graphing.")

        # ---------- CORRELATION HEATMAP ----------
        if len(numeric_cols) > 1:
            with st.expander("🔥 Correlation Heatmap"):
                corr = df[numeric_cols].corr().round(2)
                # FIX 4: Handle "None" values visually
                fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", aspect="auto")
                st.plotly_chart(fig, use_container_width=True)

        # ---------- WARNINGS ----------
        st.markdown("## ⚠ Missing Values % per Column")
        missing_pct = (df.isna().sum() / len(df) * 100).round(2)
        st.dataframe(missing_pct, use_container_width=True)

        # ---------- ML READINESS SCORE ----------
        completeness = round(100 - missing_pct.mean(), 2)
        duplicate_pct = round(df.duplicated().mean() * 100, 2)
        ml_ready_score = round(
            (completeness * 0.4) + ((100 - duplicate_pct) * 0.3) +
            (min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.15) +
            (min(len(categorical_cols)/df.shape[1], 1) * 100 * 0.15),
            2
        )

        st.markdown("## 🤖 ML Readiness Score")
        st.markdown(f"""
        <div style="background:#e0e0e0; width:100%; height:25px; border-radius:5px;">
            <div style="background:linear-gradient(to right, #ff4b4b, #00ff4b); 
                        width:{ml_ready_score}%; height:25px; border-radius:5px; 
                        display:flex; align-items:center; justify-content:center; color:white; font-weight:bold;">
                {ml_ready_score}/100
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **Suggested Algorithms:**
        * **Regression:** Linear Regression, Random Forest Regressor
        * **Classification:** XGBoost, Random Forest, Logistic Regression
        * **Unsupervised:** KMeans, DBSCAN
        """)
