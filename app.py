import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from parser import analyze_file
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import r2_score, accuracy_score

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="📄 Auto-Documenter",
    page_icon="📊",
    layout="wide"
)

st.title("📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, or JSON file to generate **interactive documentation**.")
st.divider()

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
    else:
        df = pd.read_json(uploaded_file)

    st.subheader("🔍 File Preview")
    st.dataframe(df.head(preview_rows), use_container_width=True)

    if st.button("🚀 Generate Documentation"):
        with st.spinner("Analyzing dataset..."):
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            analyze_file(temp_path)

        st.success("✅ Documentation generated")

        # ================================
        # 📅 SMART DATE DETECTION (NEW)
        # ================================
        detected_dates = []

        for col in df.columns:
            series = df[col].dropna().astype(str)

            if series.str.match(r"^\d{4}$").mean() > 0.8:
                df[col] = pd.to_datetime(df[col], format="%Y")
                detected_dates.append(f"{col} (Year)")

            elif series.str.match(r"^\d{4}\.\d{1,2}$").mean() > 0.8:
                df[col] = pd.to_datetime(series, format="%Y.%m")
                detected_dates.append(f"{col} (Year-Month)")

            elif series.str.contains("Q").mean() > 0.8:
                df[col] = pd.PeriodIndex(series, freq="Q").to_timestamp()
                detected_dates.append(f"{col} (Quarter)")

        if detected_dates:
            st.subheader("📅 Detected Date Columns")
            for d in detected_dates:
                st.write("•", d)

        # ---------- NUMERIC FILTER ----------
        numeric_cols = [
            c for c in df.select_dtypes(include=np.number).columns
            if df[c].nunique() > 1 and df[c].isna().mean() < 0.9
        ]

        # ================================
        # 📊 AUTOMATIC TARGET SUGGESTION
        # ================================
        st.subheader("🎯 Automatic Target Variable Suggestion")

        target_scores = {}

        for col in numeric_cols:
            score = (
                df[col].var() * 0.4 +
                (1 - df[col].isna().mean()) * 100 * 0.4 +
                df[col].nunique() * 0.2
            )
            target_scores[col] = score

        if target_scores:
            best_target = max(target_scores, key=target_scores.get)
            st.success(f"Suggested Target Variable: **{best_target}**")

            st.markdown(
                f"""
                **Why this column?**
                - High variance  
                - Low missing values  
                - Good predictive potential  
                """
            )
        else:
            st.warning("No suitable numeric target detected.")
            best_target = None

        # ================================
        # 🧠 REAL ML MODEL PREVIEW
        # ================================
        st.subheader("🧠 ML Model Fit Preview")

        if best_target:
            features = [c for c in numeric_cols if c != best_target]

            if len(features) >= 1:
                df_ml = df[features + [best_target]].dropna()

                X = df_ml[features]
                y = df_ml[best_target]

                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.25, random_state=42
                )

                model = LinearRegression()
                model.fit(X_train, y_train)

                preds = model.predict(X_test)
                score = r2_score(y_test, preds)

                st.metric("Model Type", "Linear Regression")
                st.metric("R² Score", round(score, 3))

                preview_df = pd.DataFrame({
                    "Actual": y_test.head(5).values,
                    "Predicted": preds[:5]
                })

                st.markdown("**Sample Predictions**")
                st.dataframe(preview_df, use_container_width=True)

            else:
                st.warning("Not enough features for ML preview.")
