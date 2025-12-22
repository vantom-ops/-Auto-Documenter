import streamlit as st
import os
from parser import analyze_file

st.title("📄 Auto-Documenter")

uploaded_file = st.file_uploader(
    "Upload a CSV, Excel, JSON, or Python file",
    type=["csv", "xlsx", "xls", "json", "py"]
)

if uploaded_file is not None:
    # Save uploaded file temporarily
    os.makedirs("temp", exist_ok=True)
    temp_path = os.path.join("temp", uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Generate README & PDF
    result = analyze_file(temp_path)

    if "error" in result:
        st.error(result["error"])
    else:
        st.success("✅ File processed successfully!")
        
        # ---------- Step 5: Only Table Preview ----------
        st.subheader("📋 File Preview (First 10 Rows)")
        df = result["dataframe"]
        st.dataframe(df.head(10))
