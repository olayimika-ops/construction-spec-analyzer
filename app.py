import streamlit as st
from datetime import datetime
import pandas as pd
import fitz  # PyMuPDF
import docx
import re
import os
from pathlib import Path
import platform

# ===== 1. Get the Downloads folder path =====
def get_download_path():
    system = platform.system()
    if system == "Windows":
        return str(Path.home() / "Downloads")
    elif system == "Darwin":  # macOS
        return str(Path.home() / "Downloads")
    elif system == "Linux":
        return str(Path.home() / "Downloads")
    else:
        return "results"  # fallback

DOWNLOAD_DIR = get_download_path()
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===== 2. Analyze the spec document =====
def analyze_spec(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        full_text = " ".join([page.get_text() for page in doc])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        full_text = " ".join([para.text for para in doc.paragraphs])
    else:
        return {"error": "Unsupported file type"}

    full_text = full_text.replace('\n', ' ').replace('  ', ' ').strip()
    sentences = re.split(r'(?<=[\.\?!])\s+', full_text)

    result = {
        "subcontractor": {"install": [], "material": []},
        "gc": {"install": [], "material": []},
        "client": {"install": [], "material": []}
    }

    install_keywords = ["install", "erect", "set", "place", "apply"]
    material_keywords = ["supply", "furnish", "provide", "deliver"]
    role_keywords = {
        "subcontractor": ["subcontractor", "trade contractor"],
        "gc": ["general contractor", "gc", "builder"],
        "client": ["owner", "client", "developer"]
    }

    for sentence in sentences:
        lowered = sentence.lower()
        for role_key, role_terms in role_keywords.items():
            if any(term in lowered for term in role_terms):
                if any(word in lowered for word in install_keywords):
                    result[role_key]["install"].append(sentence.strip())
                elif any(word in lowered for word in material_keywords):
                    result[role_key]["material"].append(sentence.strip())

    return result

# ===== 3. UI Setup =====
st.set_page_config(page_title="Construction Spec Analyzer", layout="wide")
st.title("📄 Construction Spec Analyzer")

# Theme toggle
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("""
        <style> body { background-color: #0e1117; color: white; } .stApp { background-color: #0e1117; } </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style> body { background-color: white; color: black; } .stApp { background-color: white; } </style>
    """, unsafe_allow_html=True)

# ===== 4. Upload and Analyze Section =====
uploaded_file = st.file_uploader("Upload a PDF or DOCX construction spec file", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Processing document..."):
        results = analyze_spec(uploaded_file)

        display_rows = []
        for role, duties in results.items():
            for category, entries in duties.items():
                for entry in entries:
                    display_rows.append({
                        "Role": role.title(),
                        "Category": category.title(),
                        "Responsibility": entry
                    })

        if not display_rows:
            st.warning("No assignable responsibilities found in the uploaded document.")
        else:
            df = pd.DataFrame(display_rows)
            st.subheader("🔍 Extracted Responsibilities")
            grouped = df.groupby(['Role', 'Category'])

            for (role, category), group in grouped:
                with st.expander(f"{role} - {category} ({len(group)})"):
                    st.table(group[['Responsibility']].reset_index(drop=True))

            # Save to Downloads with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_base = uploaded_file.name.split(".")[0]
            save_path = os.path.join(DOWNLOAD_DIR, f"{filename_base}_{timestamp}.csv")
            df.to_csv(save_path, index=False)

            # Offer CSV download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="extracted_responsibilities.csv",
                mime="text/csv"
            )

# ===== 5. History Viewer =====
st.sidebar.markdown("---")
st.sidebar.subheader("📂 View Saved Analyses")

csv_files = sorted([f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".csv")])
if csv_files:
    selected = st.sidebar.selectbox("Select file to preview", csv_files)
    file_path = os.path.join(DOWNLOAD_DIR, selected)
    df_preview = pd.read_csv(file_path)
    st.sidebar.write("Preview of selected result:")
    st.sidebar.dataframe(df_preview.head())
else:
    st.sidebar.info("No analysis files found in Downloads folder.")

# ===== 6. Footer =====
st.markdown("---")
st.markdown(
    "📲 **Try this app online:** [Launch App](https://construction-specs-analyzer.streamlit.app)",
    unsafe_allow_html=True
)
st.caption(f"Built by Olayinka E. Adedoyin · Auburn University · Last updated: {datetime.now():%B %d, %Y}")
