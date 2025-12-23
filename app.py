import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

st.markdown("# 📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate interactive documentation.")
st.markdown("---")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙ Settings")
    preview_rows = st.slider("Preview Rows", 5, 50, 10)

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])

if not uploaded_file:
    st.stop()

# ---------------- LOAD DATA ----------------
if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
elif uploaded_file.name.endswith((".xlsx", ".xls")):
    df = pd.read_excel(uploaded_file)
elif uploaded_file.name.endswith(".json"):
    df = pd.read_json(uploaded_file)
else:
    st.error("Unsupported file type")
    st.stop()

st.markdown("## 🔍 File Preview")
st.dataframe(df.head(preview_rows), use_container_width=True)

# ---------------- HELPERS ----------------
def detect_date_column(series):
    s = series.dropna().astype(str)

    if s.str.fullmatch(r"\d{4}").mean() > 0.8:
        return pd.to_datetime(s, format="%Y", errors="coerce")

    if s.str.fullmatch(r"\d{4}\.\d{1,2}").mean() > 0.8:
        return pd.to_datetime(s, format="%Y.%m", errors="coerce")

    if s.str.contains(r"Q").mean() > 0.8:
        return pd.PeriodIndex(s, freq="Q").to_timestamp()

    try:
        parsed = pd.to_datetime(s, errors="coerce")
        if parsed.notna().mean() > 0.8:
            return parsed
    except:
        pass

    return None

# ---------------- METRICS ----------------
rows, cols = df.shape
numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

st.markdown("## 📊 Dataset Metrics")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", rows)
c2.metric("Columns", cols)
c3.metric("Numeric", len(numeric_cols))
c4.metric("Categorical", len(categorical_cols))

# ---------------- COLUMN DATATYPES ----------------
st.markdown("## 📌 Column Datatypes")
dtype_df = pd.DataFrame({
    "Column": df.columns,
    "Data Type": df.dtypes.astype(str)
})
st.dataframe(dtype_df, use_container_width=True)

# ---------------- MIN / AVG / MAX ----------------
st.markdown("## 📈 Column Statistics (Min / Avg / Max)")
for col in numeric_cols:
    if df[col].nunique() <= 1:
        continue

    mn, av, mx = df[col].min(), round(df[col].mean(), 2), df[col].max()

    st.markdown(f"**{col}**")
    st.markdown(f"""
    <div style="display:flex;height:18px;border-radius:4px;overflow:hidden;">
        <div style="flex:1;background:#ff4b4b;"></div>
        <div style="flex:1;background:#ffd700;"></div>
        <div style="flex:1;background:#00cc66;"></div>
    </div>
    <small>Min: {mn} | Avg: {av} | Max: {mx}</small>
    """, unsafe_allow_html=True)

# ---------------- COLUMN GRAPHS ----------------
with st.expander("📊 Column Graphs"):
    for col in numeric_cols:
        if df[col].nunique() <= 1:
            continue
        if df[col].isna().mean() > 0.9:
            continue

        plot_df = df.copy()
        x_axis = None

        for c in df.columns:
            detected = detect_date_column(df[c])
            if detected is not None:
                plot_df[c] = detected
                x_axis = c
                break

        fig = px.line(
            plot_df,
            x=x_axis,
            y=col,
            title=f"{col} Trend"
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------- CORRELATION ----------------
usable_numeric = [
    c for c in numeric_cols
    if df[c].nunique() > 1 and df[c].isna().mean() < 0.9
]

if len(usable_numeric) > 1:
    st.markdown("## 🔥 Correlation Analysis")
    corr = df[usable_numeric].corr().round(2)

    st.dataframe(corr, use_container_width=True)

    fig = px.imshow(
        corr,
        color_continuous_scale="RdBu_r",
        text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------- ML READINESS ----------------
missing_pct = df.isna().mean() * 100
duplicate_pct = df.duplicated().mean() * 100

ml_score = round(
    (100 - missing_pct.mean()) * 0.4 +
    (100 - duplicate_pct) * 0.3 +
    min(len(usable_numeric)/cols, 1) * 100 * 0.3,
    2
)

st.markdown("## 🤖 ML Readiness Score & Suggested Algorithms")

st.markdown(f"""
<div style="background:linear-gradient(to right,#ff4b4b,#ffd700,#00cc66);
height:26px;border-radius:6px;position:relative;">
    <div style="position:absolute;left:{ml_score}%;transform:translateX(-50%);
    font-weight:bold;color:black;">{ml_score}/100</div>
</div>
""", unsafe_allow_html=True)

# ---------------- TARGET SUGGESTION ----------------
target = None
for col in usable_numeric:
    if not detect_date_column(df[col]):
        target = col
        break

if target:
    st.markdown(f"**🎯 Suggested Target Variable:** `{target}`")

# ---------------- ML PREVIEW ----------------
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split

    features = [c for c in usable_numeric if c != target]

    if target and features:
        X = df[features].fillna(0)
        y = df[target].fillna(0)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42
        )

        model = LinearRegression()
        model.fit(X_train, y_train)
        score = round(model.score(X_test, y_test), 3)

        st.success(f"🧠 ML Preview: Linear Regression R² = {score}")

except Exception as e:
    st.warning("⚠ ML preview skipped (scikit-learn not available)")
