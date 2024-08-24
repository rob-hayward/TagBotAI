from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

router = APIRouter()


class TextInput(BaseModel):
    content: str


@router.post("/process_text")
async def process_text(
    content: str = Form(None),
    file: UploadFile = File(None)
):
    # If a file is uploaded, read its contents
    if file:
        contents = await file.read()
        text = contents.decode('utf-8')
    # If no file, use the content from the form
    elif content:
        text = content
    else:
        raise HTTPException(status_code=400, detail="No input provided")

    formatted_text = format_text(text)
    return {"formatted_text": formatted_text}


def format_text(text: str) -> str:
    """
    Basic text formatting function.
    In this example, it trims whitespace and converts the text to lowercase.
    """
    return text.strip().lower()
