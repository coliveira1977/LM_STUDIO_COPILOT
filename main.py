# main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from diffusers import StableDiffusionPipeline
from PIL import Image
import torch
import io
import os

app = FastAPI()

# Configuração do modelo (ajuste conforme necessário)
MODEL_ID = "runwayml/stable-diffusion-v1-5"  # ou "stabilityai/stable-diffusion-2-1"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Carregamento do modelo
pipe = StableDiffusionPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.float16)
pipe = pipe.to(DEVICE)

# Configuração dos templates
templates = Jinja2Templates(directory="templates")

# Servir arquivos estáticos (CSS, JavaScript)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Rota para a página inicial
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Rota para gerar a imagem
@app.post("/generate")
async def generate_image(request: Request, prompt: str = Form(...)):
    image = pipe(prompt).images[0]

    # Salvar a imagem em um buffer na memória
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    # Retornar a imagem como um arquivo
    return FileResponse(io.BytesIO(img_byte_arr), media_type="image/png", filename="generated.png")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)