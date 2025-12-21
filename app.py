import streamlit as st
import os
import sys

# Add backend folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))
from parser import analyze_file  # now works on Streamlit Cloud

st.set_page_config(page_title="📄 Auto-Documenter", layout="wide")

st.title("📄 Auto-Documenter")
st.markdown("Upload a CSV, Excel, JSON, or Python file to automatically generate documentation.")

# File uploader
uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls", "json", "py"]
)

if uploaded_file:
    # Ensure output folder exists
    os.makedirs("output", exist_ok=True)

    # Save uploaded file temporarily
    temp_path = os.path.join("output", uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info("Processing file... ⏳")

    # Analyze file directly
    result = analyze_file(temp_path)

    if "error" in result:
        st.error(f"❌ Error: {result['error']}")
    else:
        st.success("✅ File processed successfully!")
        st.json(result)

        # Download buttons
        readme_path = "output/README.md"
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                st.download_button("📄 Download README.md", f, "README.md")

        pdf_path = "output/report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("📄 Download PDF Report", f, "report.pdf")

        readme_pdf_path = "output/README.pdf"
        if os.path.exists(readme_pdf_path):
            with open(readme_pdf_path, "rb") as f:
                st.download_button("📄 Download README PDF", f, "README.pdf")
