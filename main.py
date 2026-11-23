from fastapi import FastAPI, Query
from typing import Annotated

app = FastAPI()

@app.get("/health")
def get_health():
    return {"status": "ok"}

@app.get("/ingressos")
def consultar_ingressos(quantidade: Annotated[int, Query(ge=1)],)->dict[str,int]:
    return {"quantidade": quantidade}

@app.get("/dados/intervalo")
def minimo_maximo_dados(faces: Annotated[int, Query(ge= 2)],)->dict[str, int]:
    return {
        "mínimo": 1,
        "máximo": faces
        }

@app.post("/dados/intervalo")
def dados(face)

@app.get("/teste")
def minimo_teste(quantifa: Annotated[int, Query(ge=1)],)->dict[str,int]:
    return {"mensagem": quantifa}

@app.get("/melhorando")
def testando_teste(mensagem: Annotated[str, Query])-> dict[str,str]:
    return{"mensagem":mensagem}