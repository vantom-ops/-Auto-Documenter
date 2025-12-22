import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="📄 Auto-Documenter", page_icon="📊", layout="wide")

# ---------- HEADER ----------
st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload CSV, Excel, or JSON to generate interactive dataset insights.")
st.markdown("---")

# ---------- SIDEBAR ----------
with st.sidebar:
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------- FILE UPLOADER ----------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

if uploaded_file:
    # Load dataframe
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file type!")
        st.stop()

    # ---------- FILE PREVIEW ----------
    st.markdown("## 🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    # ---------- DATASET METRICS ----------
    st.markdown("## 📊 Dataset Metrics")
    rows, cols = df.shape
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", rows)
    c2.metric("Columns", cols)
    c3.metric("Numeric Columns", len(numeric_cols))
    c4.metric("Categorical Columns", len(categorical_cols))

    # ---------- COLUMN DATATYPES ----------
    st.markdown("## 📌 Column Datatypes")
    col_types_df = pd.DataFrame({'Column': df.columns, 'Type': df.dtypes.astype(str)})
    st.dataframe(col_types_df.T, use_container_width=True)  # Transpose for side-by-side view

    # ---------- MISSING VALUES ----------
    st.markdown("## ⚠ Missing Values % per Column")
    missing_pct = (df.isna().sum() / len(df) * 100).round(2)
    st.dataframe(missing_pct, use_container_width=True)

    # ---------- COLUMN GRAPHS ----------
    with st.expander("📈 Column Graphs"):
        for col in numeric_cols:
            col_min = df[col].min()
            col_max = df[col].max()
            col_avg = round(df[col].mean(), 2)

            with st.expander(f"{col} (Min/Avg/Max & Trend Graph)"):
                st.markdown(f"**Min:** {col_min} | **Avg:** {col_avg} | **Max:** {col_max}")

                # Gradient horizontal bar for Min → Avg → Max
                bar_fig = go.Figure(go.Bar(
                    x=[col_avg],
                    y=[col],
                    orientation='h',
                    marker=dict(
                        color=[col_avg],
                        colorscale=[[0, 'red'], [0.5, 'yellow'], [1, 'green']],
                        cmin=col_min,
                        cmax=col_max,
                        colorbar=dict(title="Value")
                    )
                ))
                bar_fig.update_layout(xaxis_title="Value", yaxis_title="", height=100, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(bar_fig, use_container_width=True)

                # Full line graph
                line_fig = px.line(df, y=col, title=f"{col} Trend", markers=True)
                line_fig.add_hline(y=col_min, line_dash="dash", line_color="red", annotation_text="Min")
                line_fig.add_hline(y=col_max, line_dash="dash", line_color="green", annotation_text="Max")
                line_fig.add_hline(y=col_avg, line_dash="dot", line_color="yellow", annotation_text="Avg")
                st.plotly_chart(line_fig, use_container_width=True)

    # ---------- CORRELATION HEATMAP ----------
    if len(numeric_cols) > 1:
        with st.expander("🔗 Correlation Heatmap"):
            corr = df[numeric_cols].corr().round(2)
            st.dataframe(corr, use_container_width=True)

            fig = px.imshow(
                corr,
                text_auto=True,
                color_continuous_scale='RdBu_r',
                zmin=-1, zmax=1,
                labels=dict(color="Correlation")
            )
            fig.update_layout(height=500, width=800)
            st.plotly_chart(fig, use_container_width=True)

    # ---------- ML READINESS SCORE ----------
    st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")
    completeness = round(100 - missing_pct.mean(), 2)
    duplicate_pct = round(df.duplicated().mean() * 100, 2)
    ml_ready_score = round(
        (completeness * 0.4) + ((100 - duplicate_pct) * 0.3) +
        (min(len(numeric_cols)/df.shape[1], 1) * 100 * 0.15) +
        (min(len(categorical_cols)/df.shape[1], 1) * 100 * 0.15),
        2
    )

    # Gradient bar for ML score
    score_fig = go.Figure(go.Bar(
        x=[ml_ready_score],
        y=["ML Readiness"],
        orientation='h',
        marker=dict(
            color=[ml_ready_score],
            colorscale=[[0, 'red'], [0.5, 'yellow'], [1, 'green']],
            cmin=0,
            cmax=100,
            colorbar=dict(title="Score")
        )
    ))
    score_fig.update_layout(xaxis_title="Score /100", yaxis_title="", height=100, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(score_fig, use_container_width=True)

    # Suggested algorithms
    st.markdown("**Suggested Algorithms:**")
    if numeric_cols and len(numeric_cols) > 1:
        st.write("- Regression: Linear Regression, Random Forest Regressor, Gradient Boosting")
    if categorical_cols:
        st.write("- Classification: Decision Tree, Random Forest, XGBoost, Logistic Regression")
    if numeric_cols and not categorical_cols:
        st.write("- Clustering: KMeans, DBSCAN, Hierarchical Clustering")
