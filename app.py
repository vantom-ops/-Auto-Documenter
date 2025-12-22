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

    # ---------- Generate README & PDF ----------
    result = analyze_file(temp_path)

    if "error" in result:
        st.error(result["error"])
    else:
        st.success("✅ File processed successfully!")
        
        # ---------- Step 5: File Preview ----------
        df = result["dataframe"]
        st.subheader("📋 File Preview")
        st.write("First 10 rows:")
        st.dataframe(df.head(10))

        st.write("Columns & Data Types:")
        col_info = df.dtypes.reset_index()
        col_info.columns = ["Column Name", "Data Type"]
        st.table(col_info)

        st.subheader("🩺 Dataset Health")
        st.write(f"Total Columns: {result['summary']['columns']}")
        st.write(f"Numeric Columns: {result['summary']['numeric_count']}")
        st.write(f"Categorical Columns: {result['summary']['categorical_count']}")
        st.write(f"Completeness: {result['summary']['completeness']}%")

        st.subheader("📊 Generated Graphs")
        for graph in result["graphs"]:
            st.image(graph, caption=os.path.basename(graph))
