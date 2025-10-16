from fastapi import FastAPI, Request, Form, Depends
import os
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from .utils import Utils
from .rag import RAG
from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
API_KEY=os.getenv('GEMINI_API_KEY')
CLIENT = genai.Client()

load_dotenv()  # take environment variables
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app = FastAPI()
rag = RAG(DB_DIR, CLIENT)
# rag.create_database()
# rag.save_database()
rag.load_database()

# Load css style
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):

    return templates.TemplateResponse(
        name="index.html",
        context={"request": request}  # Needed to obtain the user qusetion
    )

# Get the users question with a form
@app.get("/ask", response_class=HTMLResponse)
async def ask(request: Request):
    return templates.TemplateResponse(
        name="ask.html",
        context={"request": request}
    )

class Question(BaseModel):
    question: str

    @classmethod
    def as_form(cls, question: str = Form(...)):
        # Create an instance of Question
        return cls(question=question)

# Send the users the answer
@app.post("/answer", response_class=HTMLResponse)
# Depdens allow us to execute functions as parameters
async def answer(request: Request, text = Depends(Question.as_form)):
    try:
        if text is None:
            raise Exception("No question provided")
        
        top_docs = rag.search(text.question, k=10)  # text.question is a string
        question = Utils._inyect_chunks_into_question(text.question, top_docs)

        # Using pydantic we can easily validate the JSON format
        return templates.TemplateResponse(
            "answer.html",
            {
                "request": request,
                "question": text.question,
                "answer": Utils._generate_answer(CLIENT, question),
                "error": None
            }
        )
    except Exception as e:
        question_text = text.question if text else ""  # Avoids null values
        return templates.TemplateResponse(
            "answer.html",
            {
                "request": request,
                "question": question_text,
                "answer": Utils._generate_answer(CLIENT, question_text, error=True),
                "error": str(e)
            }
        )
