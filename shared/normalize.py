from shared.doc_intelligence import analyze_document

def extract_medical_facts(document_base64: str):
    raw_text = analyze_document(document_base64)

    return {
        "raw_text": raw_text,
        "conditions": [],
        "medications": [],
        "labs": [],
        "meta": {}
    }
