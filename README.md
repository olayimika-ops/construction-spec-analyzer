# 📄 Construction Specification Analyzer

An offline AI-enhanced tool to analyze construction specification documents (PDF or DOCX) and extract role-based responsibilities.

## 🔧 Features
- Upload specs in PDF or DOCX format
- Automatically extracts installation and material responsibilities
- Groups output by:
  - 👷 Subcontractor
  - 🏗️ General Contractor
  - 🧑‍💼 Client / Owner
- Download clean CSV summary
- Mobile-friendly, browser-based UI
- Optional light/dark theme and walkthrough guide
Upload spec files (PDF/DOCX) and extract key responsibilities and submittal requirements.

🔍 Chat interface for intelligent querying of saved analyses.  
⚙️ Built with Python, Streamlit, and SentenceTransformer.  

## 🛠️ Tech Stack
- Python
- Streamlit
- PyMuPDF
- python-docx
- pandas

## 🚀 How to Run (Locally)

1. Clone this repository:
```bash
git clone https://github.com/yourusername/construction-spec-analyzer.git
cd construction-spec-analyzer
