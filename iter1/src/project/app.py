from fastapi import FastAPI, Request, Form, Depends
import os
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY=os.getenv('GEMINI_API_KEY')

load_dotenv()  # take environment variables
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app = FastAPI()


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
                
        # Using pydantic we can easily validate the JSON format
        return templates.TemplateResponse(
            "answer.html",
            {
                "request": request,
                "question": text.question,
                "answer": "Soy el Copiloto de RRHH, pronto podré ayudarte.",
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
                "answer": "Ha ocurrido un error",
                "error": str(e)
            }
        )

def _generate_answer(question: str) -> str:
    from google import genai
    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=question
    )
    return str(response.text)