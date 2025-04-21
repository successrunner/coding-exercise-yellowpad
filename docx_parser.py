from docx.oxml.ns import qn
import re

# === Get numbering (numId and ilvl) from a paragraph or its style ===
def get_numbering(paragraph):
    """
    Extract numbering info (numId, ilvl) from a paragraph.
    Falls back to style-based numPr if direct numPr is not found.
    """
    p = paragraph._p
    style = paragraph.style

    numPr = None

    # Check direct paragraph numbering
    if p.pPr is not None and p.pPr.numPr is not None:
        numPr = p.pPr.numPr
    # Fallback: use style-based numbering
    elif style and style._element is not None:
        style_pPr = style._element.pPr
        if style_pPr is not None and style_pPr.numPr is not None:
            numPr = style_pPr.numPr

    if numPr is None:
        return None

    # Extract numId and ilvl
    numId_el = numPr.find(qn('w:numId'))
    ilvl_el = numPr.find(qn('w:ilvl'))

    if numId_el is None:
        return None

    numId = int(numId_el.get(qn('w:val')))
    ilvl = int(ilvl_el.get(qn('w:val'))) if ilvl_el is not None else 0

    return (numId, ilvl)

# === Formatting helpers ===
def to_letter(n):
    return chr(64 + n)  # 1 → A, 2 → B

def to_lower_letter(n):
    return chr(96 + n)  # 1 → a, 2 → b

def to_roman(n):
    # Converts to lowercase Roman numerals up to 20
    numerals = [
        '', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix',
        'x', 'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx'
    ]
    return numerals[n] if n < len(numerals) else str(n)

# === Convert list level counts to label string ===
def format_label(levels):
    """
    Build label string from level counts.
    Example: [1] → '1', [1,1] → '1A', [1,1,1] → '1A(a)', etc.
    """
    label = ""

    if len(levels) > 0:
        label += str(levels[0])  # Top-level (1, 2, 3...)

    if len(levels) > 1:
        label += to_letter(levels[1])  # 2nd-level (A, B, C...)

    for i in range(2, len(levels)):
        if i == 2:
            label += f"({to_lower_letter(levels[i])})"  # 3rd-level (a), (b)...
        else:
            label += f"({to_roman(levels[i])})"  # 4th+ level (i), (ii)...

    return label

# === Extract paragraph list labels from document ===
def extract_list_with_numbers(doc):
    """
    Returns a list of label strings for each paragraph.
    For numbered paragraphs, generates labels like '1A(a)'.
    For unnumbered ones, appends empty string.
    """
    numbered_items = []
    tracker = {}  # Keeps track of numbering state per numId

    for para in doc.paragraphs:
        label = ""
        numbering = get_numbering(para)

        if numbering:
            numId, ilvl = numbering

            # Init tracking for this numbering ID
            if numId not in tracker:
                tracker[numId] = {}

            # Ensure all parent levels are initialized
            for level in range(ilvl + 1):
                tracker[numId].setdefault(level, 0)

            # Increment current level
            tracker[numId][ilvl] += 1

            # Reset any deeper levels
            for deeper in [k for k in tracker[numId] if k > ilvl]:
                tracker[numId][deeper] = 0

            # Build levels list up to current ilvl
            levels = [tracker[numId][i] for i in sorted(tracker[numId]) if i <= ilvl]
            label = format_label(levels)

        numbered_items.append(label)

    return numbered_items

# === Utility: Determine indent level based on section name ===
def get_ilvl(section_name):
    """Return ilvl based on section format: numbers only -> 0, number+letter -> 1"""
    if re.fullmatch(r'\d+', section_name):
        return 0
    elif re.fullmatch(r'\d+[A-Za-z]', section_name):
        return 1
    return None