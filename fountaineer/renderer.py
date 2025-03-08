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

    line_spacing = 14  

    c = canvas.Canvas(output_path, pagesize=letter)
    page_width, page_height = letter

    title, author, draft_date, cast_list = "", "", "", []
    new_blocks = []  

    for element in parsed_script:
        if element["type"] == "metadata":
            text = element["text"]
            if text.startswith("Title:"):
                title = text.replace("Title: ", "").upper()
            elif text.startswith("Author:"):
                author = text.replace("Author: ", "")
            elif text.startswith("Draft date:") and not draft_date:
                draft_date = text.replace("Draft date: ", "")  
        elif element["type"] == "cast":
            cast_list = element["text"] if isinstance(element["text"], list) else element["text"].split(", ")
        else:
            new_blocks.append(element)

    page_number = 0 if title_style == "titlepage" else 1  

    if title_style == "titlepage":
        c.setFont("Courier", 12)
        y_position = page_height - 3 * inch  

        if title:
            c.drawCentredString(page_width / 2, y_position, title)
            y_position -= 3 * line_spacing  

        if author:
            c.drawCentredString(page_width / 2, y_position, author)
            y_position -= line_spacing

        if draft_date:
            c.drawCentredString(page_width / 2, y_position, draft_date)
            y_position -= 6 * line_spacing  

        if cast_list:
            c.drawString(1.5 * inch, inch + 50, "CAST")
            y_position = inch + 30
            for cast_name in cast_list:
                c.drawString(1.5 * inch, y_position, cast_name)
                y_position -= line_spacing  

        if new_blocks:
            c.showPage()
            page_number = 1  
            y_position = page_height - inch

    elif title_style == "inbody":
        c.setFont("Courier", 12)
        y_position = page_height - inch  

        left_margin = settings["metadata"]["left_margin"] * inch

        if title:
            c.drawString(left_margin, y_position, f'"{title}"')
            y_position -= line_spacing

        if author:
            c.drawString(left_margin, y_position, author)
            y_position -= line_spacing

        if draft_date:
            c.drawString(left_margin, y_position, draft_date)
            y_position -= 2 * line_spacing

        if cast_list:
            c.drawString(left_margin, y_position, "CAST")
            y_position -= line_spacing
            for cast_name in cast_list:
                c.drawString(left_margin, y_position, cast_name)
                y_position -= line_spacing  

        y_position -= 2 * line_spacing  

    c.setFont("Courier", 12)
    for element in new_blocks:
        text = element["text"]
        left_margin = settings[element["type"]]["left_margin"] * inch
        right_margin = page_width - settings[element["type"]]["right_margin"] * inch
        max_width = right_margin - left_margin

        if isinstance(text, list):
            text = "\n".join(text)

        if element["type"] == "action" and format_style == "parenthetical_actions":
            text = f"({text})"
            wrapped_text = textwrap.fill(text, width=int(max_width / (7.2))).split("\n")
        elif element["type"] == "action":
            wrapped_text = textwrap.fill(text, width=int(max_width / (7.2))).split("\n")
        elif element["type"] == "scene":
            wrapped_text = textwrap.fill(text, width=int(max_width / (7.2))).split("\n")
        elif element["type"] == "dialogue":
            wrapped_text = textwrap.fill(text, width=int(max_width / (7.2))).split("\n")  
        else:
            wrapped_text = text.split("\n")

        for line in wrapped_text:
            if y_position < inch:
                c.showPage()
                c.setFont("Courier", 12)
                page_number += 1  
                y_position = page_height - inch  

            c.drawString(left_margin, y_position, line)
            y_position -= line_spacing  

        if element["type"] not in ["character", "parenthetical"]:
            y_position -= line_spacing  

        if page_numbers and y_position < page_height - inch:
            page_label = f"{title} - {page_number}." if title_with_page_number else f"{page_number}."
            c.setFont("Courier", 10)
            c.drawRightString(page_width - inch, page_height - 0.5 * inch, page_label)
            c.setFont("Courier", 12)

    c.save()