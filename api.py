"""
API FastAPI — Agente de E-Commerce
====================================
Expõe o EcommerceAgent como um serviço HTTP REST.

Endpoints:
    GET  /           → Info da API
    GET  /health     → Health check
    POST /query      → Envia pergunta ao agente
    POST /reset      → Reinicia histórico de conversa
    GET  /exemplos   → Lista perguntas de exemplo

Como rodar:
    uvicorn api:app --reload --port 8000

Testar (curl):
    curl -X POST http://localhost:8000/query \
         -H "Content-Type: application/json" \
         -d '{"pergunta": "Top 10 produtos mais vendidos?"}'
"""

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from agent import EcommerceAgent

load_dotenv()

# =============================================================================
# SETUP DO APP
# =============================================================================

app = FastAPI(
    title="Agente de E-Commerce — API",
    description=(
        "API REST para análise de dados de e-commerce via linguagem natural (Text-to-SQL). "
        "Powered by Google Gemini 2.5 Flash."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Permite acesso de qualquer origem (útil para front-ends locais)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# SINGLETON DO AGENTE
# =============================================================================

_agent: Optional[EcommerceAgent] = None


def get_agent() -> EcommerceAgent:
    """Retorna a instância global do agente, inicializando na primeira chamada."""
    global _agent
    if _agent is None:
        _agent = EcommerceAgent(
            db_path=os.getenv("DB_PATH", "files/banco.db"),
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        )
    return _agent


# =============================================================================
# MODELOS DE REQUEST / RESPONSE
# =============================================================================

class QueryRequest(BaseModel):
    pergunta: str = Field(
        ...,
        description="Pergunta em português sobre os dados do e-commerce.",
        examples=["Quais são os 10 produtos mais vendidos?"],
    )
    nova_conversa: bool = Field(
        False,
        description="Se True, reinicia o histórico antes de processar a pergunta.",
    )


class QueryResponse(BaseModel):
    resposta: str = Field(..., description="Resposta gerada pelo agente.")
    sucesso: bool = Field(..., description="Indica se a operação foi bem-sucedida.")
    erro: Optional[str] = Field(None, description="Mensagem de erro, se houver.")


# =============================================================================
# PERGUNTAS DE EXEMPLO
# =============================================================================

EXEMPLOS = [
    # Vendas e Receita
    "Quais são os 10 produtos mais vendidos?",
    "Qual é a receita total por categoria de produto?",
    "Qual foi o mês com maior volume de vendas?",
    # Entrega e Logística
    "Qual é a quantidade de pedidos por status?",
    "Qual é o percentual de pedidos entregues no prazo por estado?",
    "Quais estados têm maior atraso médio nas entregas?",
    # Satisfação e Avaliações
    "Qual é a média geral de avaliação dos pedidos?",
    "Quais são os 10 vendedores com maior média de avaliação?",
    "Quais categorias têm maior taxa de avaliação negativa (nota 1 ou 2)?",
    # Consumidores
    "Quais estados têm maior volume de pedidos e maior ticket médio?",
    "Qual é a distribuição de pedidos por estado?",
    # Vendedores e Produtos
    "Quais são os produtos mais vendidos por estado?",
    "Quais vendedores têm maior volume de vendas em R$?",
]

# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/", tags=["Info"])
def root():
    """Informações gerais da API."""
    return {
        "nome": "Agente de E-Commerce API",
        "versao": "1.0.0",
        "status": "online",
        "modelo": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "docs": "/docs",
        "exemplos": "/exemplos",
    }


@app.get("/health", tags=["Info"])
def health():
    """Verifica se a API está funcionando."""
    return {"status": "healthy"}


@app.get("/exemplos", tags=["Info"])
def listar_exemplos():
    """Retorna uma lista de perguntas de exemplo para testar o agente."""
    return {
        "total": len(EXEMPLOS),
        "exemplos": EXEMPLOS,
    }


@app.post("/query", response_model=QueryResponse, tags=["Agente"])
def query(request: QueryRequest):
    """
    Envia uma pergunta ao agente de e-commerce e recebe uma resposta analítica.

    O agente gera automaticamente queries SQL, executa no banco de dados
    e retorna uma análise interpretada dos resultados.
    """
    try:
        agent = get_agent()

        if request.nova_conversa:
            agent.nova_conversa()

        resposta = agent.perguntar(request.pergunta)
        return QueryResponse(resposta=resposta, sucesso=True)

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.post("/reset", tags=["Agente"])
def reset_conversa():
    """
    Reinicia o histórico de conversa do agente.
    Use quando quiser começar uma análise do zero.
    """
    try:
        agent = get_agent()
        agent.nova_conversa()
        return {"mensagem": "✅ Histórico de conversa reiniciado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
