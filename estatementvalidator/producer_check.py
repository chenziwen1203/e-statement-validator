import fitz

Target_Producer="; modified using iText 2.1.7 by 1T3XT"

def producer_check(file):
    try:
        with fitz.open(file) as doc:
            producer = doc.metadata.get("producer", "").strip()
            return producer == Target_Producer

    except Exception as e:
        print(f"Error: {str(e)}")
        return False


