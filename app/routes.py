from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from pydantic import BaseModel
from collections import defaultdict, Counter
from keybert import KeyBERT
import uuid
import logging

router = APIRouter()

# Global dictionary to store tag words and associated document IDs with tag frequencies
global_tag_dictionary = defaultdict(lambda: defaultdict(int))

# Store documents with their unique IDs, tags, and frequencies
document_store = {}

# Initialize KeyBERT with a BERT model
kw_model = KeyBERT()

# Setup logging
logging.basicConfig(level=logging.INFO)


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
    # Generate a unique document ID
    document_id = generate_document_id()

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

    # Store the document metadata in the document store
    document_store[document_id] = {
        "content": text,
        "tags": tag_frequencies
    }

    # Update the global tag dictionary with frequencies, using document ID
    for tag, frequency in tag_frequencies.items():
        global_tag_dictionary[tag][document_id] = frequency

    return {
        "document_id": document_id,
        "formatted_text": format_text(text),
        "document_tag_frequencies": tag_frequencies,
        "global_tag_dictionary": {k: dict(v) for k, v in global_tag_dictionary.items()}
    }


def generate_document_id() -> str:
    """
    Generate a unique identifier for each document.
    """
    return str(uuid.uuid4())


def format_text(text: str) -> str:
    """
    Basic text formatting function.
    Trims whitespace and converts the text to lowercase.
    """
    return text.strip().lower()


def process_with_ai(text: str) -> dict:
    """
    Uses KeyBERT to extract keywords and their frequencies.
    """
    logging.info("Processing text with KeyBERT for keyword extraction.")
    try:
        # Extract keywords
        keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 1), stop_words='english', top_n=10,
                                             diversity=0.7)

        # Convert the list of keywords into a frequency dictionary
        word_counts = Counter(keyword for keyword, score in keywords)

        logging.info(f"Extracted keywords: {keywords}")
        return dict(word_counts)
    except Exception as e:
        logging.error(f"Error during keyword extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during keyword extraction: {str(e)}")


# TODO: Add support for other document types (PDF, DOCX, etc.)
# TODO: Add image scanning capability (OCR to extract text from images)
# TODO: Add video scanning capability (extract speech/text from video content)
