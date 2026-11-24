from fastapi import FastAPI, Query
from typing import Annotated

from pydantic import Field

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


# Quando for um envio (POST) pelo proprio json tem que ser usando fields ja que é um campo do model

@app.post("/dados/intervalo")
def dados(face: int = Field(ge=2, le=100), quantidade: int = Field(ge=1)):

    maximo = face * quantidade

    return {
        "minimo": quantidade,
        "máximo": maximo,
    }

# aqui por ser um GET o query param está sendo o "filtro" valida o valor pela URL.
@app.get("/teste")
def minimo_teste(quantifa: Annotated[int, Query(ge=1)],)->dict[str,int]:
    return {"mensagem": quantifa}

@app.get("/melhorando")
def testando_teste(mensagem: Annotated[str, Query])-> dict[str,str]:
    return{"mensagem":mensagem}