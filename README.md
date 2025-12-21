# -Auto-Documenter 
Auto-Documenter is a Python tool that automatically generates documentation from CSV, Excel, JSON, and Python files. It produces a README.md and a PDF report with columns, example values, and optional charts.

🚀 Features

Reads CSV, Excel (.xls/.xlsx), JSON, Python (.py) files

Generates README.md with column overviews or Python code summaries

Generates PDF report in plain text with bold headings

Supports optional column descriptions

Generates charts for numeric and categorical columns (optional)

📂 Project Structure
auto_documenter/
│
├─ backend/
│   ├─ parser.py       # analyze_file function
│   └─ main.py         # optional FastAPI backend
│
├─ frontend/
│   └─ app.py          # Streamlit frontend
│
├─ sample_files/       # Example Excel, JSON, Python files
│
├─ output/             # README.md and PDF outputs
│
├─ requirements.txt    # Python dependencies
└─ LICENSE             # Apache 2.0 License

⚡ Setup Instructions
1. Clone Repository
git clone https://github.com/<your-username>/auto_documenter.git
cd auto_documenter

2. Create Virtual Environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt


Dependencies include:

pandas – data processing

matplotlib – charts

fpdf – PDF generation

openpyxl – Excel support

streamlit – frontend

📂 Usage
Streamlit Frontend
cd frontend
streamlit run app.py


Upload CSV, Excel, JSON, or Python file

Download README.md and report.pdf

Python Script Usage
from backend.parser import analyze_file

summary = analyze_file("sample_files/example.csv")
print(summary)


Optional: pass column_descriptions as a dictionary for additional details.

📦 Sample Files

example.xlsx – Name, Age, Salary

example.json – Name, Age, Department

example.py – Python classes and functions



📄 Output

output/README.md – Markdown documentation

output/report.pdf – Plain text PDF report

output/README.pdf – PDF version of README.md

📝 License

This project is licensed under the Apache 2.0 License. See LICENSE file for details.
