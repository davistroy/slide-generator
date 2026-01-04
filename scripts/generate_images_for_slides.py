import argparse
import json
import re
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

# Constants
MODEL_ID = 'gemini-3-pro-image-preview'
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def parse_slides_ordered(file_path):
    """
    Parses a text file to find slide headers and extract their numbers and content.
    Handles various Markdown header formats including:
      - "Slide 1"
      - "## Slide 1"
      - "## **SLIDE 1: TITLE**" (Bolded headers)
      - "__Slide 1__" (Italicized/Underlined)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading slides file: {e}")
        sys.exit(1)

    # UPDATED REGEX EXPLANATION:
    # 1. (?:^|\n)           -> Matches start of line or file
    # 2. (?:[#\s]*)?        -> Non-capturing group: Optional hashtags (headers) and whitespace
    # 3. (?:[\*\_]*\s*)?    -> Non-capturing group: Optional bold/italic markers (* or _) and whitespace
    # 4. (Slide\s+(\d+))    -> Capturing Group 1: "Slide N" (full match)
    #                       -> Capturing Group 2: "N" (just the digits)
    # Flags: IGNORECASE (handles "slide" vs "SLIDE")
    header_regex = r'(?:^|\n)(?:[#\s]*)?(?:[\*\_]*\s*)?(Slide\s+(\d+))'
    
    header_matches = list(re.finditer(header_regex, content, flags=re.IGNORECASE | re.MULTILINE))
    
    parsed_slides = []
    for i, match in enumerate(header_matches):
        # match.group(1) is the full "Slide N" string (clean of markdown)
        # match.group(2) is just the number "N"
        slide_header_clean = match.group(1).strip() 
        slide_number_str = match.group(2)
        
        # We capture content from the end of this match to the start of the next match
        start_index = match.end()
        end_index = header_matches[i+1].start() if i+1 < len(header_matches) else len(content)
        
        # Get the raw body text
        slide_body = content[start_index:end_index].strip()
        
        # Combine the CLEAN header with the body for the model's context
        full_slide_context = f"{slide_header_clean}\n{slide_body}"
        
        parsed_slides.append((slide_number_str, full_slide_context))
        
    if not parsed_slides:
        print("Error: No slides found. The script expects headers containing 'Slide N' (e.g., '## **Slide 1**').")
        sys.exit(1)
        
    return parsed_slides

def get_style_instruction(style_path):
    """
    Reads the style file with 'lax' parsing to handle common JSON errors 
    like trailing commas (which standard Python json library hates).
    """
    try:
        with open(style_path, 'r', encoding='utf-8') as f:
            text = f.read()
            # Regex to remove trailing commas before closing braces/brackets
            # Matches a comma, optional whitespace, followed by } or ]
            text = re.sub(r',\s*([\]}])', r'\1', text) 
            data = json.loads(text)
            return json.dumps(data, indent=2)
    except Exception as e:
        print(f"Error reading style file: {e}")
        print("Tip: If you have comments in your JSON, remove them. Standard JSON does not support comments.")
        sys.exit(1)

def generate_image_for_slide(client, style_data, slide_num_str, slide_content, output_dir, args):
    filename = f"slide-{slide_num_str}.jpg"
    output_file_path = Path(output_dir) / filename

    # 1. Check if file exists
    if output_file_path.exists() and not args.force:
        print(f" > Skipping Slide {slide_num_str}: File exists (use --force to overwrite)")
        return

    # 2. Construct Prompt
    text_instruction = ""
    if args.notext:
        text_instruction = (
            "IMPORTANT: Do not render any text, charts, or data labels inside the image. "
            "Create a clean, artistic background or illustration suitable for overlaying text in PowerPoint later."
        )

    prompt = (
        f"You are an expert presentation designer.\n\n"
        f"--- VISUAL STYLE ---\n{style_data}\n\n"
        f"--- SLIDE CONTENT FOCUS ---\n{slide_content}\n\n"
        f"--- TASK ---\n"
        f"Generate a high-quality presentation slide image that visually represents the "
        f"content provided above, especially including the Speaker Notes, if any. The image must strictly adhere to the defined visual style.\n"
        f"{text_instruction}"
    )

    # 3. Dry Run Check
    if args.dry_run:
        print(f" > [DRY RUN] Would generate '{filename}' using model '{MODEL_ID}'.")
        return

    # 4. Configuration (Fast vs 4K)
    target_size = None 
    if not args.fast:
        target_size = "4K"

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size=target_size
        ),
    )

    # 5. Retry Loop
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=config,
            )

            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        output_file_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_file_path, 'wb') as f:
                            f.write(part.inline_data.data)
                        print(f" > Success: Saved {filename}")
                        return

            print(f" > Attempt {attempt}: No image returned.")
            # Check for safety blocks or other finish reasons
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
                if "SAFETY" in str(finish_reason):
                    print(" > BLOCK: Image blocked by safety filters. Check prompt or style content.")
                    return # Do not retry safety blocks

        except Exception as e:
            print(f" > Attempt {attempt} failed: {e}")

        if attempt < MAX_RETRIES:
            # print(f" > Retrying in {RETRY_DELAY} seconds...") # Optional verbosity
            time.sleep(RETRY_DELAY)
    
    print(f" > Failed to generate Slide {slide_num_str} after {MAX_RETRIES} attempts.")

def main():
    parser = argparse.ArgumentParser(description="Batch generate PPT slide images using Gemini 3 Pro.")
    
    # Required
    parser.add_argument("--style", required=True, help="Path to style.json")
    parser.add_argument("--slides", required=True, help="Path to the slides text file")
    
    # Optional
    parser.add_argument("--output", default=".", help="Directory for output images (default: current dir)")
    parser.add_argument("--fast", action="store_true", help="Use standard resolution (faster/cheaper) instead of 4K.")
    parser.add_argument("--dry-run", action="store_true", help="Parse slides and print intent without calling API.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing image files.")
    parser.add_argument("--notext", action="store_true", help="Instruct the model NOT to render text in the image.")

    args = parser.parse_args()

    # API Key Check
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not found.")
        sys.exit(1)

    # Load Inputs
    style_text = get_style_instruction(args.style)
    slides_list = parse_slides_ordered(args.slides)
    total_slides = len(slides_list)
    output_dir = Path(args.output)

    # Initialize Client (5 min timeout for 4K)
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=300000) 
    )

    print(f"--- Starting Batch Generation ---")
    print(f"Slides Found: {total_slides}")
    print(f"Model:        {MODEL_ID}")
    print(f"Resolution:   {'Standard (Fast)' if args.fast else '4K (High Res)'}")
    print(f"Text Removal: {'Enabled' if args.notext else 'Disabled'}")
    print(f"Output Dir:   {output_dir.absolute()}\n")

    for i, (slide_num_str, slide_content) in enumerate(slides_list):
        print(f"Processing slide {i + 1} of {total_slides} (Slide {slide_num_str})...")
        generate_image_for_slide(client, style_text, slide_num_str, slide_content, output_dir, args)
        print("-" * 30)

    print("\n--- Batch Generation Complete ---")

if __name__ == "__main__":
    main()