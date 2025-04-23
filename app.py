import streamlit as st
from datetime import datetime
import pandas as pd
import fitz  # PyMuPDF
import docx
import re
import os
import glob
from sentence_transformers import SentenceTransformer, util

# === APP SETUP ===
st.set_page_config(page_title="Construction Spec Analyzer", layout="wide")
st.title("📄 Construction Spec Analyzer")

DOWNLOAD_DIR = "saved_specs"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === THEME TOGGLE ===
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("""
        <style>body, .stApp { background-color: #0e1117; color: white; }</style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>body, .stApp { background-color: white; color: black; }</style>
    """, unsafe_allow_html=True)

# === NLP FUNCTION ===
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
        "client": {"install": [], "material": []},
        "submittal": {"materials": [], "installation": [], "other": []}
    }

    install_keywords = ["install", "erect", "set", "place", "apply"]
    material_keywords = ["supply", "furnish", "provide", "deliver"]
    role_keywords = {
        "subcontractor": ["subcontractor", "trade contractor"],
        "gc": ["general contractor", "gc", "builder"],
        "client": ["owner", "client", "developer"]
    }
    submittal_keywords = ["submit", "submittal", "shop drawing", "samples", "certificates"]

    for sentence in sentences:
        lowered = sentence.lower()

        # Role Responsibilities
        for role_key, role_terms in role_keywords.items():
            if any(term in lowered for term in role_terms):
                if any(word in lowered for word in install_keywords):
                    result[role_key]["install"].append(sentence.strip())
                elif any(word in lowered for word in material_keywords):
                    result[role_key]["material"].append(sentence.strip())

        # Submittals
        if any(word in lowered for word in submittal_keywords):
            if "material" in lowered or "product" in lowered:
                result["submittal"]["materials"].append(sentence.strip())
            elif "installation" in lowered or "method" in lowered:
                result["submittal"]["installation"].append(sentence.strip())
            else:
                result["submittal"]["other"].append(sentence.strip())

    return result

# === UPLOAD & ANALYZE ===
uploaded_file = st.file_uploader("Upload a PDF or DOCX spec file", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Analyzing specification..."):
        results = analyze_spec(uploaded_file)

        display_rows = []
        for role, duties in results.items():
            if role == "submittal":
                continue
            for category, entries in duties.items():
                for entry in entries:
                    display_rows.append({"Role": role.title(), "Category": category.title(), "Responsibility": entry})

        if not display_rows and not any(results["submittal"].values()):
            st.warning("No responsibilities or submittal requirements found.")
        else:
            df = pd.DataFrame(display_rows)

            # SAVE OUTPUT
            base_name = os.path.splitext(uploaded_file.name)[0].replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{base_name}_analysis_{timestamp}.csv"
            csv_path = os.path.join(DOWNLOAD_DIR, csv_filename)
            df.to_csv(csv_path, index=False)

            st.success(f"✅ Results saved to: {csv_path}")
            st.download_button("📥 Download CSV", data=df.to_csv(index=False).encode("utf-8"),
                               file_name=csv_filename, mime="text/csv")

            st.subheader("🔍 Extracted Responsibilities")
            grouped = df.groupby(['Role', 'Category'])
            for (role, category), group in grouped:
                with st.expander(f"{role} - {category} ({len(group)})"):
                    st.table(group[['Responsibility']].reset_index(drop=True))

            st.subheader("📋 Required Submittals")
            for category, entries in results["submittal"].items():
                if entries:
                    with st.expander(f"{category.title()} Submittals ({len(entries)})"):
                        st.table(pd.DataFrame(entries, columns=["Requirement"]))

# === SIDEBAR HISTORY ===
st.sidebar.markdown("---")
st.sidebar.subheader("📂 View Saved Analyses")
csv_paths = sorted(glob.glob(os.path.join(DOWNLOAD_DIR, "*_analysis_*.csv")), reverse=True)
csv_files = [os.path.basename(p) for p in csv_paths]
selected_file = st.sidebar.selectbox("Select file for chat search", csv_files if csv_files else ["None"])

# === CHAT SEARCH ENGINE ===
if selected_file != "None":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔎 Ask the Analyzer")

    selected_df = pd.read_csv(os.path.join(DOWNLOAD_DIR, selected_file))
    corpus = selected_df["Responsibility"].tolist()
    if corpus:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        corpus_embeddings = model.encode(corpus, convert_to_tensor=True)

        user_query = st.sidebar.text_input("Ask a question about this spec:")

        if user_query:
            query_embedding = model.encode(user_query, convert_to_tensor=True)
            scores = util.pytorch_cos_sim(query_embedding, corpus_embeddings)[0]
            top_idx = scores.argmax().item()

            st.sidebar.markdown("**📌 Best Match:**")
            st.sidebar.write(corpus[top_idx])

            st.sidebar.markdown("**🔍 Related Matches:**")
            top_k = scores.argsort(descending=True)[:3]
            for idx in top_k:
                if idx != top_idx:
                    st.sidebar.write("-", corpus[idx])

# === FOOTER ===
st.markdown("---")
st.markdown("📲 **Try this app online:** [Launch App](https://construction-spec-analyzer.streamlit.app)", unsafe_allow_html=True)
st.caption(f"Built by Olayinka E. Adedoyin · Auburn University · Last updated: {datetime.now():%B %d, %Y}")



