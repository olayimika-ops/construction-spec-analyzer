import streamlit as st
from datetime import datetime
import pandas as pd
import fitz  # PyMuPDF
import docx
import re
import os
import glob

# === CONFIGURATION ===
st.set_page_config(page_title="Construction Spec Analyzer", layout="wide")
DOWNLOAD_DIR = "saved_specs"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === SIDEBAR: THEME TOGGLE ===
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #0e1117; color: white; }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        body, .stApp { background-color: white; color: black; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# === NLP FUNCTION FOR ANALYSIS ===
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

# === MAIN INTERFACE ===
st.title("📄 Construction Spec Analyzer")
uploaded_file = st.file_uploader("Upload a PDF or DOCX construction spec file", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Processing document..."):
        results = analyze_spec(uploaded_file)

        # Format output
        display_rows = []
        for role, duties in results.items():
            for category, entries in duties.items():
                for entry in entries:
                    display_rows.append({"Role": role.title(), "Category": category.title(), "Responsibility": entry})

        if not display_rows:
            st.warning("No assignable responsibilities found in the uploaded document.")
        else:
            df = pd.DataFrame(display_rows)

            # Save file to disk with timestamp + filename
            base_name = os.path.splitext(uploaded_file.name)[0].replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{base_name}_analysis_{timestamp}.csv"
            csv_path = os.path.join(DOWNLOAD_DIR, csv_filename)
            df.to_csv(csv_path, index=False)

            st.success(f"✅ Results saved to: {csv_path}")
            st.download_button(
                label="📥 Download This Analysis as CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=csv_filename,
                mime="text/csv"
            )

            st.subheader("🔍 Extracted Responsibilities")
            grouped = df.groupby(['Role', 'Category'])
            for (role, category), group in grouped:
                with st.expander(f"{role} - {category} ({len(group)})"):
                    st.table(group[['Responsibility']].reset_index(drop=True))

# === VIEW SAVED ANALYSES ===
st.sidebar.markdown("---")
st.sidebar.subheader("📂 View Saved Analyses")

csv_paths = sorted(glob.glob(os.path.join(DOWNLOAD_DIR, "*_analysis_*.csv")), reverse=True)
csv_files = [os.path.basename(p) for p in csv_paths]

if csv_files:
    selected_file = st.sidebar.selectbox("Select file to preview", csv_files)
    # No preview content is shown, just selection.
else:
    st.sidebar.info("No saved analysis files yet.")

# === FOOTER ===
st.markdown("---")
st.markdown(
    "📲 **Try this app online:** [Launch App](https://construction-spec-analyzer.streamlit.app)",
    unsafe_allow_html=True
)
st.caption(f"Built by Olayinka E. Adedoyin · Auburn University · Last updated: {datetime.now():%B %d, %Y}")
