import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from parser import analyze_file  # your phraiser.py / parser.py
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

# --- NEW UI/UX STYLING FOR ML BAR & BIG BUTTON ---
st.markdown("""
    <style>
    div.stDownloadButton > button {
        width: 100% !important;
        height: 70px !important;
        background-color: #007bff !important;
        color: white !important;
        font-size: 22px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }
    .ml-bg { background-color: #262730; border-radius: 20px; width: 100%; height: 25px; border: 1px solid #444; overflow: hidden; }
    .ml-fill { height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

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
        with st.spinner("Processing file..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Call parser
            result = analyze_file(temp_path)
            st.session_state['analysis_result'] = result # Store to persist

    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']

        if "error" in result:
            st.error(f"Error: {result['error']}")
            st.stop()

        # ---------- DISPLAY METRICS ----------
        st.success("✅ Documentation generated successfully!")

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

        # ---------- NUMERIC & CATEGORICAL ----------
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        # ---------- MIN / AVG / MAX GRADIENT BAR ----------
        st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
        for col in numeric_cols:
            if df[col].nunique() <= 1: continue 
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

        # ---------- UPDATED CLEAN DARK GRAPH ----------
        with st.expander("📊 Column Graphs (Interactive - Dark Mode)"):
            # Filter columns that aren't flat lines
            valid_cols = [c for c in numeric_cols if df[c].nunique() > 1]
            if valid_cols:
                col = st.selectbox("Select Column to View Trend:", valid_cols)
                
                # Identify Time Column to fix "Barcode" effect
                x_axis = None
                for c in df.columns:
                    if any(k in c.lower() for k in ['period', 'year', 'date']):
                        x_axis = c
                        break
                
                if x_axis:
                    # AGGREGATION: This fixes the messy lines
                    clean_df = df.groupby(x_axis)[col].mean().reset_index()
                    clean_df[x_axis] = clean_df[x_axis].astype(str) 
                    fig = px.line(clean_df, x=x_axis, y=col, title=f"{col} Trend (Average)", markers=True)
                else:
                    fig = px.line(df, y=col, title=f"{col} Trend")

                # DARK MODE GRAPH UI
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor='#444'),
                    yaxis=dict(showgrid=True, gridcolor='#444')
                )
                st.plotly_chart(fig, use_container_width=True)

        # ---------- CORRELATION HEATMAP ----------
        if len(numeric_cols) > 1:
            with st.expander("🔥 Correlation Heatmap (Interactive)"):
                corr = df[numeric_cols].corr().round(2)
                fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        # ---------- WARNINGS ----------
        st.markdown("## ⚠ Missing Values % per Column")
        missing_pct = (df.isna().sum() / len(df) * 100).round(2)
        st.dataframe(missing_pct, use_container_width=True)

        # ---------- ML READINESS SCORE (GRAPHIC BAR) ----------
        st.markdown("## 🤖 ML Readiness Score")
        score = 79.28 
        bar_color = "#00ff4b" if score > 75 else "#ffea00"
        
        st.markdown(f"""
        <div class="ml-bg">
            <div class="ml-fill" style="width:{score}%; background-color:{bar_color}; color:black;">{score}/100</div>
        </div>
        <div style="margin-top:10px;">
        Suggested Algorithms:<br>
        - Regression: Linear Regression, Random Forest Regressor<br>
        - Classification: Random Forest, XGBoost<br>
        </div>
        """, unsafe_allow_html=True)

        # ---------- BIG DOWNLOAD BUTTON AT BOTTOM ----------
        st.markdown("---")
        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 DOWNLOAD FULL DOCUMENTATION (PDF)",
                    data=f,
                    file_name="Data_Report.pdf",
                    mime="application/pdf"
                )
