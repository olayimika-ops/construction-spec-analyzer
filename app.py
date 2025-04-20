import streamlit as st
from datetime import datetime
import pandas as pd
import fitz  # PyMuPDF
import docx
import re
import os

# === Utility function to analyze specification content ===
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
    sentences = re.split(r'(?<=[\.\?\!])\s+', full_text)

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

# === Prepare app layout ===
st.set_page_config(page_title="Construction Spec Analyzer", layout="wide")

# === THEME TOGGLE ===
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #0e1117; color: white; }
        </style>
        """, unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        body, .stApp { background-color: white; color: black; }
        </style>
        """, unsafe_allow_html=True
    )

# === TITLE ===
st.title("📄 Construction Spec Analyzer")
st.markdown("Upload your construction specification (.pdf or .docx) to extract material and installation responsibilities.")

# === File uploader ===
uploaded_file = st.file_uploader("Upload a specification file", type=["pdf", "docx"])

# === Create Downloads/spec_outputs folder if it doesn't exist ===
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "spec_outputs")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === PROCESS uploaded spec ===
if uploaded_file:
    with st.spinner("Analyzing document..."):
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
            st.warning("No assignable responsibilities found in this spec.")
        else:
            df = pd.DataFrame(display_rows)
            grouped = df.groupby(['Role', 'Category'])

            st.subheader("🔍 Extracted Responsibilities")
            for (role, category), group in grouped:
                with st.expander(f"{role} - {category} ({len(group)})"):
                    st.table(group[['Responsibility']].reset_index(drop=True))

            # Save analysis to local file system
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"spec_analysis_{timestamp}.csv"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            df.to_csv(filepath, index=False)

            st.success(f"✅ Analysis saved to: `{filepath}`")

            # Also allow user to download instantly
            st.download_button("📥 Download CSV", data=df.to_csv(index=False), file_name=filename, mime="text/csv")

# === 5. View Saved Files (NO preview, as requested) ===
st.sidebar.markdown("---")
st.sidebar.subheader("📂 View Saved Analyses")
csv_files = sorted([f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".csv")])
if csv_files:
    selected_file = st.sidebar.selectbox("Select file to preview", csv_files)
    # No preview shown intentionally
else:
    st.sidebar.info("No analysis files found in Downloads folder.")

# === Footer ===
st.markdown("---")
st.caption(f"Built by Olayinka E. Adedoyin · Auburn University · Last updated: {datetime.now():%B %d, %Y}")

