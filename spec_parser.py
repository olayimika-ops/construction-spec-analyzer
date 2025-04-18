import fitz  # PyMuPDF
import docx
import re

def extract_text(file):
    text = ""
    if file.name.endswith(".pdf"):
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file type.")
    return text

def find_matches(text, role_keywords, action_keywords):
    pattern = rf"(?i)(?:{'|'.join(role_keywords)}).*?(?:{'|'.join(action_keywords)}).*?[.\n]"
    return re.findall(pattern, text)

def analyze_spec(file):
    text = extract_text(file)

    install_kw = ["install", "installation", "place", "set", "erect", "apply"]
    material_kw = ["material", "supply", "provide", "deliver", "furnish"]

    subs_kw = ["subcontractor", "trade contractor"]
    gc_kw = ["contractor", "general contractor", "GC"]
    client_kw = ["owner", "client", "employer", "authority"]

    return {
        "subcontractor": {
            "install": find_matches(text, subs_kw, install_kw),
            "material": find_matches(text, subs_kw, material_kw)
        },
        "gc": {
            "install": find_matches(text, gc_kw, install_kw),
            "material": find_matches(text, gc_kw, material_kw)
        },
        "client": {
            "install": find_matches(text, client_kw, install_kw),
            "material": find_matches(text, client_kw, material_kw)
        }
    }
