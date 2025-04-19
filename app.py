import streamlit as st
import os
import docx
import fitz  # PyMuPDF
import pandas as pd

from io import StringIO
from datetime import datetime

st.set_page_config(page_title="Construction Spec Analyzer", layout="wide")

# --- HEADER ---
st.title("📄 Construction Spec Analyzer")
st.caption("Extract stakeholder responsibilities for materials and installation tasks.")

# --- UPLOAD ---
uploaded_file = st.file_uploader("Upload a construction spec file (.pdf or .docx)", type=["pdf", "docx"])

# --- FUNCTIONS ---
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip() != ""])

def analyze_spec(text):
    results = {
        "Subcontractor": {"Installation": [], "Materials": []},
        "General Contractor": {"Installation": [], "Materials": []},
        "Client": {"Installation": [], "Materials": []}
    }

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        lower = line.lower()

        # Installation phrases
        if any(x in lower for x in ["install", "set", "erect", "place"]):
            if "subcontractor" in lower:
                results["Subcontractor"]["Installation"].append(line)
            elif "general contractor" in lower or "gc" in lower:
                results["General Contractor"]["Installation"].append(line)
            elif "client" in lower or "owner" in lower:
                results["Client"]["Installation"].append(line)

        # Material phrases
        if any(x in lower for x in ["supply", "furnish", "provide", "deliver"]):
            if "subcontractor" in lower:
                results["Subcontractor"]["Materials"].append(line)
            elif "general contractor" in lower or "gc" in lower:
                results["General Contractor"]["Materials"].append(line)
            elif "client" in lower or "owner" in lower:
                results["Client"]["Materials"].append(line)

    return results

def flatten_results(results_dict):
    rows = []
    for role, categories in results_dict.items():
        for cat, lines in categories.items():
            for line in lines:
                rows.append({"Role": role, "Category": cat, "Responsibility": line})
    return pd.DataFrame(rows)

# --- MAIN LOGIC ---
if uploaded_file:
    with st.spinner("Analyzing document..."):
        ext = uploaded_file.name.split(".")[-1].lower()
        if ext == "pdf":
            raw_text = extract_text_from_pdf(uploaded_file)
        elif ext == "docx":
            raw_text = extract_text_from_docx(uploaded_file)
        else:
            st.error("Unsupported file type.")
            st.stop()

        results = analyze_spec(raw_text)
        df = flatten_results(results)

        st.success("✅ Responsibilities extracted successfully!")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download Result as CSV", csv, file_name="spec_analysis.csv", mime="text/csv")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "📲 **Try this app on the web:** [Launch Construction Spec Analyzer](https://construction-spec-analyzer-mcsc3x5gpcthq6i4nhbvmu.streamlit.app/)",
    unsafe_allow_html=True
)
st.caption(f"Built by Olayinka E. Adedoyin · Auburn University · {datetime.now():%B %Y}")
