"""Renderer for Fountain screenplay format to PDF."""

import json
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from .parser import parse_fountain

def render_fountain_to_pdf(file_path, output_path, config_path):
    """Render a screenplay PDF ensuring correct metadata handling and word wrapping."""
    with open(config_path, "r", encoding="utf-8") as json_file:
        settings = json.load(json_file)

    parsed_script = parse_fountain(file_path)
    title_style = settings.get("title_style", "titlepage")  # 'titlepage' or 'inbody'
    format_style = settings.get("format_style", "standard")  # 'standard' or 'parenthetical_actions'
    page_numbers = settings.get("page_numbers", True)  # Default to True
    title_with_page_number = settings.get("title_with_page_number", False)  # Default to False

    c = canvas.Canvas(output_path, pagesize=letter)
    page_width, page_height = letter

    title, author, draft_date, cast_list = "", "", "", []
    page_number = 1  # Start counting pages

    # ✅ **Extract Metadata Before Rendering**
    new_blocks = []  # Store only non-metadata blocks
    for element in parsed_script:
        if element["type"] == "metadata":
            text = element["text"]
            if text.startswith("Title:"):
                title = text.replace("Title: ", "").upper()
            elif text.startswith("Author:"):
                author = text.replace("Author: ", "")
            elif text.startswith("Draft date:") and not draft_date:
                draft_date = text.replace("Draft date: ", "")  # Only store once
        elif element["type"] == "cast":
            cast_list = element["text"] if isinstance(element["text"], list) else element["text"].split(", ")
        else:
            new_blocks.append(element)  # ✅ Store only non-metadata blocks

    # ✅ **Render Title Page for Standard Format**
    if title_style == "titlepage":
        c.setFont("Courier", 12)
        y_position = page_height - 3 * inch  # Start title in middle of page

        if title:
            c.drawCentredString(page_width / 2, y_position, title)
            y_position -= 40  # Space between title and author

        if author:
            c.drawCentredString(page_width / 2, y_position, author)
            y_position -= 15

        if draft_date:
            c.drawCentredString(page_width / 2, y_position, draft_date)
            y_position -= 80  # Extra space before screenplay starts

        if cast_list:
            c.drawString(1.5 * inch, inch + 50, "CAST")  # Label
            y_position = inch + 30
            for cast_name in cast_list:
                c.drawString(1.5 * inch, y_position, cast_name)
                y_position -= 15  # Single-space each name

        # ✅ **Fix: Avoid Extra Blank Page in Standard Format**
        if new_blocks:
            y_position -= 30  # Space before screenplay starts

        c.showPage()  # Move to screenplay content
        page_number += 1  # First actual content page starts at 2

    # ✅ **Render In-Body Title for Parenthetical Actions Format**
    elif title_style == "inbody":
        c.setFont("Courier", 12)
        y_position = page_height - inch  # Start at top

        if title:
            c.drawString(1.5 * inch, y_position, f'"{title}"')  # Left-aligned, wrapped in quotes
            y_position -= 15

        if author:
            c.drawString(1.5 * inch, y_position, author)  # Left-aligned author
            y_position -= 15

        if draft_date:
            c.drawString(1.5 * inch, y_position, draft_date)  # Left-aligned date
            y_position -= 30  # Extra space before cast list

        if cast_list:
            c.drawString(1.5 * inch, y_position, "CAST")  # Label
            y_position -= 15  # Space between "CAST" and names
            for cast_name in cast_list:
                c.drawString(1.5 * inch, y_position, cast_name)
                y_position -= 15  # Single-space each name

        y_position -= 30  # Extra space before screenplay starts

    # ✅ **Render Screenplay Body Using `new_blocks` (No Duplicates)**
    c.setFont("Courier", 12)
    for element in new_blocks:
        text = element["text"]
        left_margin = settings[element["type"]]["left_margin"] * inch
        right_margin = page_width - settings[element["type"]]["right_margin"] * inch
        max_width = right_margin - left_margin

        # ✅ **Convert Lists to Strings Before Processing**
        if isinstance(text, list):
            text = "\n".join(text)  # Convert lists (e.g., cast) to formatted text

        # ✅ **Fix: Wrap Actions in Parentheses if Using Parenthetical Actions Format**
        if element["type"] == "action" and format_style == "parenthetical_actions":
            text = f"({text})"  # Wrap action text in parentheses
            wrapped_text = textwrap.wrap(text, width=int(max_width / (7.2)))
        elif element["type"] == "action":
            wrapped_text = textwrap.wrap(text, width=int(max_width / (7.2)))  # Normal action
        elif element["type"] == "scene":
            wrapped_text = textwrap.wrap(text, width=int(max_width / (7.2)))  # Scene always wrapped
        else:
            wrapped_text = text.split("\n")  # Otherwise, split normally

        for line in wrapped_text:
            if y_position < inch:
                c.showPage()
                c.setFont("Courier", 12)
                page_number += 1  # Increment page number when a new page is created
                y_position = page_height - inch

            c.drawString(left_margin, y_position, line)
            y_position -= 15  # Default single spacing

        # ✅ **Apply Double Spacing for Everything Except Speakers & Parentheticals**
        if element["type"] not in ["character", "parenthetical"]:
            y_position -= 15  # Extra space for all other blocks (double spacing)

        # ✅ **Add Page Numbers (If Enabled)**
        if page_numbers and y_position < page_height - inch:  # Only add page numbers on non-title pages
            page_label = f"{title} - {page_number}." if title_with_page_number else f"{page_number}."
            c.setFont("Courier", 10)
            c.drawRightString(page_width - inch, page_height - 0.5 * inch, page_label)
            c.setFont("Courier", 12)  # Reset font for the next block

    c.save()