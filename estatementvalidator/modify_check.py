import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
from collections import defaultdict

# Template formats from the template PDF
TEMPLATE_FORMATS = [
    ('AllAndNone', 4.35, (0.0, 0.0, 0.0)),
    ('AllAndNone', 13.0, (0.0, 0.0, 0.0)),
    ('AllAndNone', 8.0, (0.0, 0.0, 0.0)),
    ('AllAndNone', 11.5, (0.0, 0.0, 0.0)),
    ('AllAndNone', 6.5, (0.0, 0.0, 0.0)),
    ('AllAndNone', 15.0, (0.0, 0.0, 0.0)),
    ('AllAndNone', 10.0, (0.0, 0.0, 0.0)),
    ('AllAndNone', 7.5, (0.0, 0.0, 0.0)),
    ('AllAndNone', 10.5, (0.0, 0.0, 0.0)),
    ('AllAndNone', 11.0, (0.0, 0.0, 0.0)),
    ('AllAndNone', 6.0, (0.0, 0.0, 0.0)),
    ('AllAndNone2', 5.0, (0.0, 0.0, 0.0)),
    ('AllAndNone', 6.0, (0.502, 0.502, 0.502)),
    ('AllAndNone', 13.5, (0.0, 0.0, 0.0))
]

def format_color(color):
    """Standardize color value precision (RGB tuple or single value)"""
    if color is None:
        return None
    if isinstance(color, (list, tuple)):
        return tuple(round(float(c), 3) for c in color)
    return round(float(color), 3)

def find_all_format(file_path):
    format_all=[]

    # Open PDF with both libraries
    doc = fitz.open(file_path)
    pdf_pdfplumber = pdfplumber.open(file_path)

    for page_num in range(len(doc)):
        pdfplumber_page = pdf_pdfplumber.pages[page_num]

        # Get all characters from pdfplumber page
        all_chars = pdfplumber_page.chars

        for c in all_chars:
            format={
                "font": c["fontname"],
                "size": c["size"],
                "color": c["non_stroking_color"]
            }
            format_all.append(format)

    df = pd.DataFrame(format_all)
    unique_df = df.drop_duplicates()

    # Convert back to list of dictionaries
    unique_formats = unique_df.to_dict('records')

    # Close files
    pdf_pdfplumber.close()
    doc.close()

    return unique_formats


def analyze_pdf(file_path, template_formats):
    modify_valid=True
    """
    Analyze target PDF, detect two types of issues:
    1. Characters using formats not in the template format list
    2. Suspicious white overlay rectangles

    :param file_path: Path to the PDF to analyze
    :param template_formats: Template format list (from find_all_format)
    :return: List of abnormal formats and overlay issues
    """
    # Store detection results
    format_violations = []
    overlay_issues = []
    detect_result=[]

    # Open PDF file
    doc = fitz.open(file_path)
    pdf_pdfplumber = pdfplumber.open(file_path)

    # Convert template formats to comparable form (considering float precision)
    template_keys = set()
    for fmt in template_formats:
        color = fmt.get("color")
        norm_color = format_color(color) if color is not None else None
        key = (
            fmt["font"],
            round(fmt["size"], 2),  # Keep 4 decimal places for comparison
            norm_color
        )
        template_keys.add(key)


    for page_num in range(len(doc)):
        pymupdf_page = doc[page_num]
        pdfplumber_page = pdf_pdfplumber.pages[page_num]

        # ======================
        # 1. Detect abnormal character formats
        # ======================
        all_chars = pdfplumber_page.chars
        for char in all_chars:
            current_fmt = {
                "font": char["fontname"],
                "size": round(char["size"], 2),
                "color": char["non_stroking_color"]
            }

            color=current_fmt['color']

            normed_color=format_color(color) if color is not None else None

            # Create comparison key
            current_key = (
                current_fmt["font"],
                current_fmt["size"],
                normed_color
            )


            # Check if in template formats
            if current_key not in template_keys:
                modify_valid=False
                violation={
                    'page':page_num+1,
                    'text':char['text'],
                    'position':(char["x0"], char["top"], char["x1"], char["bottom"]),
                    'format':current_fmt
                }
                format_violations.append(violation)

                # ======================
                # 2. Detect white overlays
                # ======================
        for draw in pymupdf_page.get_drawings():
            if "fill" in draw and draw["fill"] == (1, 1, 1):  # White fill
                modify_valid=False
                overlay = {
                    "page": page_num + 1,
                    "coordinates": draw["rect"],
                    "area": abs(draw["rect"][2] - draw["rect"][0]) * abs(draw["rect"][3] - draw["rect"][1])
                }
                overlay_issues.append(overlay)

                # Close files
    pdf_pdfplumber.close()
    doc.close()

    # Print detection results
    if format_violations:
        result=f"Unusual formatting characters found: {violation['text']}"
        detect_result.append(result)
        print("\n[!] Found abnormal formatting characters:")
        for i, violation in enumerate(format_violations, 1):
            print(f"\nAbnormal {i} (Page {violation['page']}):")
            print(f"Text: '{violation['text']}'")
            print(f"Position: {violation['position']}")
            print(
                f"Format: font={violation['format']['font']}, size={violation['format']['size']}, color={violation['format']['color']}")
    else:
        print("\n[✓] No abnormal formatting characters found")

    if overlay_issues:
        detect_result.append('Suspicious white coverage found')
        print("\n[!] Found suspicious white overlays:")
        for i, overlay in enumerate(overlay_issues, 1):
            print(f"\nOverlay {i} (Page {overlay['page']}):")
            print(f"Coordinates: {overlay['coordinates']}")
            print(f"Area: {overlay['area']:.1f} square units")
    else:
        print("\n[✓] No suspicious white overlays found")

    return modify_valid,detect_result

def modify_detect(file_path):
    # Convert TEMPLATE_FORMATS to the format expected by analyze_pdf
    template_formats = [
        {
            "font": fmt[0],
            "size": fmt[1],
            "color": fmt[2]
        }
        for fmt in TEMPLATE_FORMATS
    ]
    return analyze_pdf(file_path, template_formats)



