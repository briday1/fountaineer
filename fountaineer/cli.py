"""CLI for Fountaineer with verbose parsing option."""

import argparse
import json
from .renderer import render_fountain_to_pdf
from .parser import parse_fountain

def main():
    parser = argparse.ArgumentParser(description="Compile a Fountain script to a formatted PDF.")
    parser.add_argument("input", help="Path to the input Fountain file")
    parser.add_argument("output", help="Path to the output PDF file")
    parser.add_argument("config", help="Path to the JSON configuration file")
    parser.add_argument("--verbose", action="store_true", help="Display parsed blocks and their margins")

    args = parser.parse_args()

    if args.verbose:
        # Load config
        with open(args.config, "r", encoding="utf-8") as json_file:
            settings = json.load(json_file)

        # Parse script
        parsed_script = parse_fountain(args.input)
        
        print("\n--- Parsed Blocks ---")
        for element in parsed_script:
            block_type = element["type"]
            text = element["text"]
            left_margin = settings.get(block_type, {}).get("left_margin", "N/A")
            right_margin = settings.get(block_type, {}).get("right_margin", "N/A")
            print(f"[{block_type.upper()}] Left Margin: {left_margin}in, Right Margin: {right_margin}in\n{text}\n")

    else:
        render_fountain_to_pdf(args.input, args.output, args.config)

if __name__ == "__main__":
    main()