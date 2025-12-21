import streamlit as st
import requests

st.set_page_config(page_title="Auto-Documenter", layout="centered")

st.title("📄 Auto-Documenter")
st.write("Upload a Python or CSV file to auto-generate documentation.")

uploaded_file = st.file_uploader("Choose a file", type=["py", "csv"])

if uploaded_file:
    with st.spinner("Processing file..."):
        response = requests.post(
            "http://127.0.0.1:8000/upload",
            files={"file": uploaded_file}
        )

    if response.status_code == 200:
        st.success("File processed successfully ✅")
        st.json(response.json())
    else:
        st.error("Something went wrong ❌")
