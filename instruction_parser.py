import re

def parse_contract_instructions(raw_text: str):
    """
    Parse instruction text into structured data:
    Extract contract number, insertion type, section, and snippet to insert.
    """
    result = []

    # Split by each "Contract X" block (e.g., Contract 1, Contract 2, etc.)
    blocks = re.split(r'\nContract\s+(\d+)[:\n]', raw_text)

    for i in range(1, len(blocks), 2):
        contract_number = blocks[i].strip()
        content = blocks[i + 1].strip()

        # Expect content to have two parts: instruction + text to insert
        parts = re.split(r'\n\n+', content, maxsplit=1)
        if len(parts) != 2:
            continue  # Skip if content format is invalid

        instruction_text, insert_text = parts[0], parts[1]

        insert_type = None
        section_name = None
        sentence_after = None

        # Case 1: Match "Insert this clause as section 1A"
        match_as = re.search(r'as section (\w+)', instruction_text, re.IGNORECASE)
        if match_as:
            insert_type = "as"
            section_name = match_as.group(1)

        # Case 2: Match "Insert ... between the second and third sentence in Section 11"
        match_between = re.search(
            r'between the (\w+)(?:st|nd|rd|th)? and (\w+)(?:st|nd|rd|th)? sentence in Section (\w+)',
            instruction_text,
            re.IGNORECASE
        )
        if match_between:
            insert_type = "in"
            section_name = match_between.group(3)

            # Convert ordinal words to integer (e.g., "second" → 2)
            ordinals = {
                "first": 1, "second": 2, "third": 3, "fourth": 4,
                "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
                "ninth": 9, "tenth": 10
            }
            sentence_after = ordinals.get(match_between.group(1).lower())

        # Add parsed instruction to result
        result.append({
            "contract": f"Contract {contract_number}",
            "insert_type": insert_type,
            "section_name": section_name,
            "sentence_after": sentence_after,
            "text": insert_text.strip()
        })

    return result
