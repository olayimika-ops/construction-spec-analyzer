import streamlit as st
from datetime import datetime
import pandas as pd
import fitz  # PyMuPDF
import docx
import os
import re
import glob

# Setup download directory in user's Downloads folder
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "spec_outputs")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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

# Streamlit page setup
st.set_page_config(page_title="Construction Spec Analyzer", layout="wide")

# Theme toggle
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])

if theme == "Dark":
    st.markdown(
        """
        <style>
        body { background-color: #0e1117; color: white; }
        .stApp { background-color: #0e1117; }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        body { background-color: white; color: black; }
        .stApp { background-color: white; }
        </style>
        """,
        unsafe_allow_html=True
    )

st.title("📄 Construction Spec Analyzer")
uploaded_file = st.file_uploader("Upload a PDF or DOCX construction spec file", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Analyzing specification..."):
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
            st.warning("No responsibilities extracted.")
        else:
            df = pd.DataFrame(display_rows)
            grouped = df.groupby(['Role', 'Category'])

            st.subheader("🔍 Extracted Responsibilities")
            for (role, category), group in grouped:
                with st.expander(f"{role} - {category} ({len(group)})"):
                    st.table(group[['Responsibility']].reset_index(drop=True))

            # Save CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"spec_analysis_{timestamp}.csv"
            csv_path = os.path.join(DOWNLOAD_DIR, csv_filename)
            df.to_csv(csv_path, index=False)

            st.success(f"✅ Results saved to: {csv_path}")
            st.download_button(
                label="📥 Download This Analysis as CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=csv_filename,
                mime="text/csv"
            )

# View saved analyses
st.sidebar.markdown("---")
st.sidebar.subheader("📂 View Saved Analyses")

csv_paths = sorted(glob.glob(os.path.join(DOWNLOAD_DIR, "*.csv")), reverse=True)
csv_files = [os.path.basename(p) for p in csv_paths]

if csv_files:
    selected_file = st.sidebar.selectbox("Select file to preview", csv_files)
else:
    st.sidebar.info("No analysis files found in Downloads/spec_outputs.")

# Footer
st.markdown("---")
st.markdown(
    "📲 **Try this app online:** [Launch App](https://construction-spec-analyzer.streamlit.app)",
    unsafe_allow_html=True
)
st.caption(f"Built by Olayinka E. Adedoyin · Auburn University · Last updated: {datetime.now():%B %d, %Y}")
