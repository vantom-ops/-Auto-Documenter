import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

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
    st.dataframe(col_types_df.T, use_container_width=True)

    # ---------- MISSING VALUES ----------
    st.markdown("## ⚠ Missing Values % per Column")
    missing_pct = (df.isna().sum() / len(df) * 100).round(2)
    st.dataframe(missing_pct, use_container_width=True)

    # ---------- COLUMN MIN/MAX/AVG INTERACTIVE ----------
    st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
    if numeric_cols:
        col_stats = pd.DataFrame({
            'Column': numeric_cols,
            'Min': [df[col].min() for col in numeric_cols],
            'Avg': [df[col].mean() for col in numeric_cols],
            'Max': [df[col].max() for col in numeric_cols]
        })

        # Plot interactive horizontal bars
        fig = go.Figure()
        for idx, row in col_stats.iterrows():
            fig.add_trace(go.Bar(
                y=[row['Column']],
                x=[row['Min']],
                name='Min',
                orientation='h',
                marker=dict(color='red'),
                hovertemplate=f"Min: {row['Min']}"
            ))
            fig.add_trace(go.Bar(
                y=[row['Column']],
                x=[row['Avg']],
                name='Avg',
                orientation='h',
                marker=dict(color='yellow'),
                hovertemplate=f"Avg: {row['Avg']}"
            ))
            fig.add_trace(go.Bar(
                y=[row['Column']],
                x=[row['Max']],
                name='Max',
                orientation='h',
                marker=dict(color='green'),
                hovertemplate=f"Max: {row['Max']}"
            ))

        fig.update_layout(
            barmode='group',
            height=50*len(numeric_cols),
            xaxis_title="Value",
            yaxis_title="Column",
            showlegend=True,
            title="Min / Avg / Max for Numeric Columns",
            margin=dict(l=120, r=20, t=50, b=50)
        )
        st.plotly_chart(fig, use_container_width=True)

    # ---------- COLUMN LINE GRAPHS ----------
    with st.expander("📈 Column Line Graphs"):
        for col in numeric_cols:
            fig_line = px.line(df, y=col, title=f"{col} Trend", markers=True)
            fig_line.add_hline(y=df[col].min(), line_dash="dash", line_color="red", annotation_text="Min")
            fig_line.add_hline(y=df[col].mean(), line_dash="dot", line_color="yellow", annotation_text="Avg")
            fig_line.add_hline(y=df[col].max(), line_dash="dash", line_color="green", annotation_text="Max")
            st.plotly_chart(fig_line, use_container_width=True)

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

    # Interactive gradient bar for ML score
    score_fig = go.Figure(go.Bar(
        x=[ml_ready_score],
        y=["ML Readiness"],
        orientation='h',
        marker=dict(
            color=[ml_ready_score],
            colorscale=[[0, 'red'], [0.5, 'yellow'], [1, 'green']],
            cmin=0,
            cmax=100
        ),
        hovertemplate=f"Score: {ml_ready_score}/100"
    ))
    score_fig.update_layout(
        xaxis_title="Score /100",
        yaxis_title="",
        height=150,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(score_fig, use_container_width=True)

    st.markdown("**Suggested Algorithms:**")
    if numeric_cols and len(numeric_cols) > 1:
        st.write("- Regression: Linear Regression, Random Forest Regressor, Gradient Boosting")
    if categorical_cols:
        st.write("- Classification: Decision Tree, Random Forest, XGBoost, Logistic Regression")
    if numeric_cols and not categorical_cols:
        st.write("- Clustering: KMeans, DBSCAN, Hierarchical Clustering")
