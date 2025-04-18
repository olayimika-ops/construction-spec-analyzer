import streamlit as st
from spec_parser import analyze_spec
import pandas as pd

# ------------------ Page Setup ------------------
st.set_page_config(page_title="Spec Analyzer", page_icon="📄", layout="wide")

# ------------------ Sidebar Guide ------------------
st.sidebar.title("🧭 Walkthrough")
st.sidebar.markdown("""
**How to Use:**
1. Upload a construction spec (.pdf or .docx)
2. App will extract responsibilities for:
   - Subcontractor
   - General Contractor
   - Client / Owner
3. View results grouped by role
4. Download as a .csv summary file
""")

# ------------------ Theme Switch ------------------
theme = st.sidebar.radio("🌗 Choose Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        "<style>body { background-color: #1E1E1E; color: white; }</style>",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<style>body { background-color: white; color: black; }</style>",
        unsafe_allow_html=True
    )

# ------------------ Title & Upload ------------------
st.title("📄 Construction Specification Analyzer (Offline)")
st.markdown("Quickly identify responsibilities across stakeholders from your spec document.")

uploaded_file = st.file_uploader("📁 Upload a PDF or DOCX spec file", type=["pdf", "docx"])

# ------------------ Main Analysis ------------------
if uploaded_file:
    with st.spinner("⏳ Analyzing the document..."):
        try:
            result = analyze_spec(uploaded_file)
            st.success("✅ Analysis Complete!")

            # ------------------ Grouped Role Display ------------------
            st.subheader("📊 Responsibilities by Role")
            roles = {
                "subcontractor": "👷 Subcontractor",
                "gc": "🏗️ General Contractor",
                "client": "🧑‍💼 Client / Owner"
            }

            data = []  # For CSV download

            for role_key, role_label in roles.items():
                with st.expander(f"{role_label}"):
                    install = result[role_key]["install"]
                    material = result[role_key]["material"]

                    # Install
                    st.markdown("#### 📌 Installation Responsibilities")
                    if install:
                        for item in install:
                            st.markdown(f"- {item.strip()}")
                            data.append({
                                "Role": role_label.replace("👷", "").replace("🏗️", "").replace("🧑‍💼", "").strip(),
                                "Responsibility Type": "Installation",
                                "Responsibility": item.strip()
                            })
                    else:
                        st.markdown("_No installation responsibilities found._")

                    # Material
                    st.markdown("#### 🧱 Material Responsibilities")
                    if material:
                        for item in material:
                            st.markdown(f"- {item.strip()}")
                            data.append({
                                "Role": role_label.replace("👷", "").replace("🏗️", "").replace("🧑‍💼", "").strip(),
                                "Responsibility Type": "Material",
                                "Responsibility": item.strip()
                            })
                    else:
                        st.markdown("_No material responsibilities found._")

            # ------------------ Download Button ------------------
            st.markdown("---")
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Download Responsibility Table (CSV)",
                data=csv,
                file_name="spec_responsibilities_summary.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
else:
    st.info("Upload your spec file above to begin.")
