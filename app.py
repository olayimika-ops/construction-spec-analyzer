import os
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import docx
import re
import datetime
from sentence_transformers import SentenceTransformer, util

SAVE_DIR = "saved_specs"
os.makedirs(SAVE_DIR, exist_ok=True)

st.set_page_config(page_title="Spec Analyzer", layout="wide")
st.title("📄 Construction Spec Analyzer with Chat Support")

st.sidebar.header("Upload File")
uploaded_file = st.sidebar.file_uploader("Choose a PDF or DOCX file", type=["pdf", "docx"])

# Chat feature setup
model = SentenceTransformer('all-MiniLM-L6-v2')

if uploaded_file:
    filename = f"spec_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(SAVE_DIR, filename)

    def extract_text(file):
        if file.type == "application/pdf":
            doc = fitz.open(stream=file.read(), filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file)
            return "\n".join([p.text for p in doc.paragraphs])
        return ""

    text = extract_text(uploaded_file)

    install_resps = re.findall(r"(?i)(subcontractor|contractor|client).*?(install|erect|fix|mount|construct).*?\.", text)
    material_resps = re.findall(r"(?i)(subcontractor|contractor|client).*?(furnish|supply|provide).*?\.", text)
    submittals = re.findall(r"(?i)(submit|submittal|shop drawing|product data|installation manual|certificate).*?\.", text)

    df = pd.DataFrame(install_resps, columns=["Role", "Action"])
    df["Category"] = "Installation"

    df2 = pd.DataFrame(material_resps, columns=["Role", "Action"])
    df2["Category"] = "Material"

    df3 = pd.DataFrame(submittals, columns=["Requirement"])
    df3["Role"] = "--"
    df3["Action"] = df3["Requirement"].str.extract(r'(submit|submittal|drawing|certificate)', expand=False)
    df3["Category"] = "Submittal"
    df3 = df3[["Role", "Action", "Category", "Requirement"]]

    final_df = pd.concat([df, df2], ignore_index=True)
    final_df["Requirement"] = "--"
    final_df = pd.concat([final_df, df3], ignore_index=True)

    final_df.to_csv(filepath, index=False)
    st.success(f"File processed and saved as {filename}")
    st.dataframe(final_df)

    with st.expander("💬 Chat with Spec Output"):
        user_query = st.text_input("Enter your question:")
        if user_query:
            corpus = final_df.apply(lambda row: f"{row['Role']} - {row['Action']} - {row['Category']} - {row['Requirement']}", axis=1).tolist()
            embeddings = model.encode(corpus, convert_to_tensor=True)
            q_embed = model.encode(user_query, convert_to_tensor=True)
            scores = util.pytorch_cos_sim(q_embed, embeddings)[0]
            top_idx = scores.argmax()
            st.info(f"🔍 Best Match: {corpus[top_idx]}")

st.sidebar.markdown("---")
st.sidebar.header("📂 View Saved Analyses")
saved_files = sorted(os.listdir(SAVE_DIR))
sel_file = st.sidebar.selectbox("Select file to preview", saved_files if saved_files else ["None"])

if sel_file != "None":
    st.sidebar.write(f"📁 {sel_file}")