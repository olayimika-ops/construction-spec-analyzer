import streamlit as st
import os
from spec_parser import analyze_spec
import pandas as pd

st.set_page_config(page_title="Construction Spec Analyzer", layout="wide")

# STEP 1: Theme toggle radio button in sidebar
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])

# STEP 2: Apply CSS based on theme selection
if theme == "Dark":
    st.markdown(
        """
        <style>
        body {
            background-color: #0e1117;
            color: white;
        }
        .stApp {
            background-color: #0e1117;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        body {
            background-color: white;
            color: black;
        }
        .stApp {
            background-color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# App Header
st.title("📄 Construction Spec Analyzer")

# Upload file section
uploaded_file = st.file_uploader("Upload a PDF or DOCX construction spec file", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Processing document..."):
        results = analyze_spec(uploaded_file)

        # Prepare results for display
        display_rows = []
        for role, duties in results.items():
            for category, entries in duties.items():
                for entry in entries:
                    display_rows.append({"Role": role.title(), "Category": category.title(), "Responsibility": entry})

        if not display_rows:
            st.warning("No assignable responsibilities found in the uploaded document.")
        else:
            df = pd.DataFrame(display_rows)
            grouped = df.groupby(['Role', 'Category'])

            # Display grouped data
            st.subheader("🔍 Extracted Responsibilities")
            for (role, category), group in grouped:
                with st.expander(f"{role} - {category} ({len(group)})"):
                    st.table(group[['Responsibility']].reset_index(drop=True))

            # Download CSV button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name='extracted_responsibilities.csv',
                mime='text/csv'
            )
# Footer
st.markdown("---")
st.markdown(
    "📲 **Try this app online:** [Launch App](https://construction-spec-analyzer.streamlit.app)",
    unsafe_allow_html=True
)
st.caption(f"Built by Olayinka E. Adedoyin · Auburn University · Last updated: {datetime.now():%B %d, %Y}")
