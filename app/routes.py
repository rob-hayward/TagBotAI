from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body, Header, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from collections import Counter
from keybert import KeyBERT
import uuid
import logging
from app.config import db
from bson import ObjectId

router = APIRouter()

# Initialize KeyBERT with a BERT model
kw_model = KeyBERT()

# Setup logging
logging.basicConfig(level=logging.INFO)


class TextInput(BaseModel):
    content: str
    preface: str = ""
    user_tags: list[str] = []
    privacy: str = "private"


@router.post("/process_text")
async def process_text(
    request: Request,
    body: TextInput = Body(None),
    file: UploadFile = File(None),
    content: str = Form(None),
    preface: str = Form(""),
    user_tags: str = Form(""),
    privacy: str = Form("private"),
    user_id: str = Header(None, alias="x-user-id")
):
    try:
        # Log the request details
        logging.info(f"Request method: {request.method}")
        logging.info(f"Request URL: {request.url}")
        logging.info(f"Request headers: {request.headers}")
        logging.info(f"Body: {body}")
        logging.info(f"File: {file}")
        logging.info(f"Form content: {content}")

        # Initialize variables
        text = None
        tags = []

        # Handle JSON body
        if request.headers.get("content-type") == "application/json":
            logging.info("Processing JSON body")
            json_body = await request.json()
            text = json_body.get("content")
            preface = json_body.get("preface", "")
            tags = json_body.get("user_tags", [])
            privacy = json_body.get("privacy", "private")
        # Handle form data
        elif content:
            logging.info("Processing form data")
            text = content
            tags = user_tags.split(',') if user_tags else []
        # Handle file upload
        elif file:
            logging.info("Processing file upload")
            contents = await file.read()
            text = contents.decode('utf-8')
            tags = user_tags.split(',') if user_tags else []

        # If no input provided, raise an exception
        if not text:
            logging.error("No input provided")
            raise HTTPException(status_code=400, detail="No input provided")

        # Log the received data
        logging.info(f"Received content: {text}")
        logging.info(f"Received user ID: {user_id}")

        # Process the text
        document_id = generate_document_id()
        combined_text = f"{preface}\n\n{text}" if preface else text
        tag_frequencies = process_with_ai(combined_text)

        # Include user-added tags
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                tag_frequencies[tag.strip()] = tag_frequencies.get(tag.strip(), 0) + 1

        # Store the document in MongoDB
        document_data = {
            "_id": document_id,
            "content": text,
            "tags": tag_frequencies,
            "user_id": user_id,
            "privacy": privacy,
            "user_tags": [tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()],
            "public": privacy.lower() == "public"
        }
        db.documents.insert_one(document_data)

        return JSONResponse(content={
            "document_id": document_id,
            "formatted_text": format_text(text),
            "document_tag_frequencies": tag_frequencies,
            "user_tags": document_data["user_tags"],
            "privacy": privacy
        })

    except ValidationError as ve:
        logging.error(f"Validation error: {ve.errors()}")
        raise HTTPException(status_code=422, detail=ve.errors())
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_documents")
async def get_documents(limit: int = Query(10, ge=1, le=100), skip: int = Query(0, ge=0)):
    try:
        # Retrieve documents from MongoDB
        documents = list(db.documents.find().skip(skip).limit(limit))

        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            doc['_id'] = str(doc['_id'])

        return JSONResponse(content={
            "total_documents": db.documents.count_documents({}),
            "documents": documents
        })
    except Exception as e:
        logging.error(f"An error occurred while retrieving documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear_database")
async def clear_database():
    try:
        result = db.documents.delete_many({})
        return JSONResponse(content={
            "message": f"Deleted {result.deleted_count} documents"
        })
    except Exception as e:
        logging.error(f"An error occurred while clearing the database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_document_id() -> str:
    return str(uuid.uuid4())


def format_text(text: str) -> str:
    return text.strip().lower()


def process_with_ai(text: str) -> dict:
    logging.info("Processing text with KeyBERT for keyword extraction.")
    try:
        keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 1), stop_words='english', top_n=10,
                                             diversity=0.7)
        word_counts = Counter(keyword for keyword, score in keywords)
        logging.info(f"Extracted keywords: {keywords}")
        return dict(word_counts)
    except Exception as e:
        logging.error(f"Error during keyword extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during keyword extraction: {str(e)}")


@router.post("/clear_database")
async def clear_database():
    try:
        result = db.documents.delete_many({})
        return JSONResponse(content={
            "message": f"Deleted {result.deleted_count} documents"
        })
    except Exception as e:
        logging.error(f"An error occurred while clearing the database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# TODO: Add support for other document types (PDF, DOCX, etc.)
# TODO: Add image scanning capability (OCR to extract text from images)
# TODO: Add video scanning capability (extract speech/text from video content)
