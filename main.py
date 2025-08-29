import sys
import asyncio
import subprocess


from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configuração do servidor LM Studio
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_START_COMMAND = "caminho/para/lmstudio.exe --api-key SEU_TOKEN_API_KEY --port 1234"

async def is_lm_studio_running() -> bool:
    """Verifica se o servidor LM Studio está rodando."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.get(LM_STUDIO_URL)
            return True
    except httpx.ConnectError:
        return False
    except httpx.TimeoutException:
        return False

async def start_lm_studio() -> None:
    """Inicia o servidor LM Studio usando o comando especificado."""
    print("Iniciando o servidor LM Studio...")
    try:
        subprocess.Popen(LM_STUDIO_START_COMMAND, shell=True)
        await asyncio.sleep(10)
        print("Servidor LM Studio iniciado (aguarde alguns instantes até estar totalmente operacional).")
    except Exception as e:
        print(f"Erro ao iniciar o servidor LM Studio: {e}")

async def ensure_lm_studio_is_running() -> None:
    """Garante que o LM Studio esteja rodando. Se não estiver, tenta iniciá-lo."""
    if not await is_lm_studio_running():
        print("Servidor LM Studio não detectado.")
        await start_lm_studio()
    else:
        print("Servidor LM Studio já está rodando.")

async def generate_text_with_lm_studio(prompt: str) -> str:
    """Envia o prompt para o LM Studio e retorna o texto gerado."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LM_STUDIO_URL,
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 200,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            response_json = response.json()
            generated_text = response_json["choices"][0]["message"]["content"]
            return generated_text

    except httpx.HTTPStatusError as e:
        return f"Erro HTTP: {e}"
    except httpx.TimeoutException:
        return "Erro: Tempo limite ao conectar com o LM Studio."
    except Exception as e:
        return f"Erro inesperado: {e}"

@app.on_event("startup")
async def startup_event():
    await ensure_lm_studio_is_running()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_text(request: Request, prompt: str = Form(...)):
    generated_text = await generate_text_with_lm_studio(prompt)
    return generated_text

if __name__ == "__main__":
    import uvicorn
    asyncio.run(uvicorn.run(app, host="0.0.0.0", port=8000))