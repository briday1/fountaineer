"""Parser for Fountain screenplay format with corrected metadata handling."""

def parse_fountain(file_path):
    """Parse a Fountain script and structure it for proper formatting."""
    blocks = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_block = None  # Start with no active block
    
    for ii, line in enumerate(lines):
        stripped = line.strip()

        print(ii, line, blocks)  # Debugging output

        # ✅ **Blank line resets current block**
        if not stripped:
            if current_block:
                blocks.append(current_block)  # Store before resetting
                current_block = None  # Reset for next block
            continue

        # ✅ **Handle Title Page Metadata Correctly**
        if stripped.startswith(("Title:", "Credit:", "Author:", "Draft date:")):
            blocks.append({"type": "metadata", "text": stripped})
            continue  # No need to track in `current_block`
        
        # ✅ **Handle Cast List Separately**
        elif stripped.startswith("Cast:"):
            cast_names = stripped.replace("Cast:", "").strip()
            cast_list = [name.strip() for name in cast_names.strip("[]").split(",")]
            blocks.append({"type": "cast", "text": cast_list})  # Store cast as list
            continue  # No need to track in `current_block`
        
        # ✅ **Handle Transitions**
        elif stripped in ["BLACKOUT", "FADE OUT.", "FADE TO BLACK."] or stripped.endswith("TO:"):
            blocks.append({"type": "transition", "text": stripped})
            continue  # No need to track in `current_block`
        
        # ✅ **Handle Character Names**
        elif stripped.isupper() and not stripped.startswith(("INT.", "EXT.")):
            if current_block:
                blocks.append(current_block)  # Store previous before switching
            current_block = {"type": "character", "text": stripped}
            continue

        # ✅ **Handle Parentheticals**
        elif stripped.startswith("(") and stripped.endswith(")"):
            if current_block and current_block["type"] == "character":
                blocks.append(current_block)  # Store character before parenthetical
            current_block = {"type": "parenthetical", "text": stripped}
            continue

        # ✅ **Handle Scene Headings**
        elif stripped.startswith(("INT.", "EXT.")):
            if current_block:
                blocks.append(current_block)  # Store previous before switching
            current_block = {"type": "scene", "text": stripped}
            continue

        # ✅ **Handle Dialogue Properly**
        elif current_block and current_block["type"] in ["character", "parenthetical"]:
            blocks.append(current_block)  # Store character or parenthetical
            current_block = {"type": "dialogue", "text": stripped}
            continue

        elif current_block and current_block["type"] == "dialogue":
            current_block["text"] += f" {stripped}"  # Append to existing dialogue
            continue

        # ✅ **Handle Action Blocks (Default Case)**
        else:
            if current_block:
                blocks.append(current_block)  # Store before switching
            current_block = {"type": "action", "text": stripped}

    # ✅ **Store Last Block Before Exiting**
    if current_block:
        blocks.append(current_block)

    return blocks