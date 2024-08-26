from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from pydantic import BaseModel
from collections import defaultdict, Counter

router = APIRouter()

# Global dictionary to store tag words, associated documents, and their frequencies
global_tag_dictionary = defaultdict(lambda: defaultdict(int))


class TextInput(BaseModel):
    content: str
    preface: str = ""


@router.post("/process_text")
async def process_text(
        content: str = Form(None),
        file: UploadFile = File(None),
        preface: str = Form(""),
        body: TextInput = Body(None)
):
    # Check if we have JSON input
    if body:
        content = body.content
        preface = body.preface

    # If a file is uploaded, read its contents
    if file:
        contents = await file.read()
        text = contents.decode('utf-8')
    # If no file, use the content from the form or JSON body
    elif content:
        text = content
    else:
        raise HTTPException(status_code=400, detail="No input provided")

    # Combine the preface with the user's text for AI context if preface is provided
    combined_text = f"{preface}\n\n{text}" if preface else text

    # Process the combined text with AI for context (result ignored)
    _ = process_with_ai(combined_text)

    # Now process the content alone for tag generation
    tag_frequencies = process_with_ai(text)

    # Generate a unique tag identifier for the document
    tag_identifier = generate_unique_tag_identifier(tag_frequencies)

    # Update the global tag dictionary with frequencies
    for tag, frequency in tag_frequencies.items():
        global_tag_dictionary[tag][tag_identifier] = frequency

    return {
        "formatted_text": format_text(text),
        "tag_identifier": tag_identifier,
        "document_tag_frequencies": tag_frequencies,
        "global_tag_dictionary": {k: dict(v) for k, v in global_tag_dictionary.items()}
    }


def format_text(text: str) -> str:
    """
    Basic text formatting function.
    Trims whitespace and converts the text to lowercase.
    """
    return text.strip().lower()


def process_with_ai(text: str) -> dict:
    """
    Mock AI processing function.
    Replace this with actual AI model integration.
    Returns a dictionary with tag words as keys and their frequencies as values.
    """
    words = text.lower().split()
    tag_candidates = ["ai", "ml", "tag"]  # Example tag words to consider
    word_counts = Counter(words)

    # Filter word counts to include only the tag candidates
    tag_frequencies = {word: count for word, count in word_counts.items() if word in tag_candidates}

    return tag_frequencies


def generate_unique_tag_identifier(tag_frequencies: dict) -> str:
    """
    Generate a unique identifier based on sorted tag words.
    """
    sorted_tags = sorted(tag_frequencies.keys())
    unique_id = "_".join(sorted_tags)
    return unique_id

# TODO: Add support for other document types (PDF, DOCX, etc.)
# TODO: Add image scanning capability (OCR to extract text from images)
# TODO: Add video scanning capability (extract speech/text from video content)
