# Agente de Analise de E-Commerce

Agente conversacional que permite a **usuarios nao tecnicos** realizarem consultas e analises sobre dados de um sistema de e-commerce usando **linguagem natural em portugues**.

O agente traduz automaticamente perguntas para SQL (Text-to-SQL), executa as queries no banco SQLite e retorna analises interpretadas — sem que o usuario precise conhecer SQL ou estrutura de dados.

**Stack:**
- Modelo: Google Gemini 2.5 Flash (`google-generativeai`)
- Linguagem: Python 3.10+
- Banco: SQLite3 (embutido no Python, sem instalacao extra)
- Interface Visual: Streamlit + Plotly
- API: FastAPI + Uvicorn
- Demo: Jupyter Notebook

---

## Estrutura do Projeto

```
.
├── agent.py           # Nucleo do agente (Text-to-SQL + Gemini + anonimizacao)
├── app.py             # Interface visual com Streamlit e graficos
├── api.py             # API REST com FastAPI
├── demo.ipynb         # Notebook Jupyter com exemplos
├── requirements.txt   # Dependencias Python
├── .env.example       # Template de variaveis de ambiente
├── .gitignore
└── files/
    └── banco.db       # Banco SQLite (adicionar manualmente - nao versionado)
```

---

## Passo a Passo para Executar

### Pre-requisitos

- Python 3.10 ou superior
- Arquivo `banco.db` (disponivel na pasta compartilhada da atividade)
- Chave da API Gemini gratuita em [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

### 1. Clone o repositorio

```bash
git clone https://github.com/arbcaio/rocketLab2026Agentes.git
cd rocketLab2026Agentes
```

---

### 3. Instale as dependencias

```bash
pip install -r requirements.txt
```

---

### 4. Configure as variaveis de ambiente

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Abra o arquivo `.env` e preencha com sua chave:

```env
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash
DB_PATH=files/banco.db
PORT=8000
```

> **Como obter a chave gratuita:**
> Acesse [aistudio.google.com/apikey](https://aistudio.google.com/apikey), faca login com sua conta Google e clique em **"Create API key"**.

> **Limite do free tier do Gemini 2.5 Flash:** 20 requisicoes/dia.
> Para testes com mais volume, use `GEMINI_MODEL=gemini-2.0-flash` (1.500 req/dia gratis).

---

### 5. Adicione o banco de dados

> O arquivo `banco.db` nao esta versionado no repositorio (arquivo grande, ~63 MB).
> Voce precisa obtê-lo separadamente.

**Como obter:** faca o download do arquivo disponibilizado na pasta compartilhada da atividade (Google Drive / Teams).

**Onde colocar:**

```
rocketLab2026Agentes/
└── files/
    └── banco.db   <- coloque aqui
```

> Para usar um caminho diferente, edite `DB_PATH` no arquivo `.env`.

---

## Como Usar

### Interface Visual com Streamlit (recomendada)

```bash
streamlit run app.py
```

Acesse em **http://localhost:8501**

A interface oferece:
- Chat com historico persistente de conversa
- Graficos interativos gerados automaticamente (barras, linhas, tabelas)
- Sidebar com perguntas de exemplo clicaveis por categoria
- Botao de nova conversa para limpar o historico
- Dados pessoais anonimizados automaticamente

---

### Terminal interativo

```bash
python agent.py
```

```
==============================================================
  Agente de Analise de E-Commerce  |  Gemini 2.5 Flash
==============================================================
  Comandos: 'novo' = nova conversa  |  'sair' = encerrar
==============================================================

Voce: Quais sao os 10 produtos mais vendidos?

Agente:
Os 10 produtos mais vendidos sao: ...
```

---

### Notebook Jupyter

```bash
jupyter notebook demo.ipynb
```

Notebook com exemplos prontos para todas as categorias de analise, executaveis celula a celula.

---

### API FastAPI

```bash
uvicorn api:app --reload --port 8000
```

Documentacao interativa disponivel em **http://localhost:8000/docs**

**Exemplo com curl:**

```bash
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"pergunta": "Quais sao os 10 produtos mais vendidos?"}'
```

**Endpoints:**

| Metodo | Endpoint     | Descricao                          |
|--------|--------------|------------------------------------|
| GET    | `/`          | Informacoes da API                 |
| GET    | `/health`    | Health check                       |
| GET    | `/exemplos`  | Lista de perguntas de exemplo      |
| POST   | `/query`     | Envia pergunta ao agente           |
| POST   | `/reset`     | Reinicia historico de conversa     |

---

### Como biblioteca Python

```python
from agent import EcommerceAgent

agent = EcommerceAgent(db_path="files/banco.db")

print(agent.perguntar("Quais sao os 10 produtos mais vendidos?"))

# Follow-up (mantem contexto)
print(agent.perguntar("E qual e a receita total desses produtos?"))

# Reiniciar conversa
agent.nova_conversa()
```

---

## Exemplos de Perguntas

**Vendas e Receita**
- "Quais sao os 10 produtos mais vendidos?"
- "Qual e a receita total por categoria de produto?"
- "Qual foi a evolucao mensal do numero de pedidos?"

**Entrega e Logistica**
- "Qual e a quantidade de pedidos por status?"
- "Qual e o percentual de pedidos entregues no prazo por estado?"
- "Quais estados tem maior atraso medio nas entregas?"

**Satisfacao e Avaliacoes**
- "Qual e a media geral de avaliacao dos pedidos?"
- "Quais sao os 10 vendedores com maior media de avaliacao?"
- "Quais categorias tem maior taxa de avaliacao negativa?"

**Consumidores**
- "Quais estados tem maior volume de pedidos e maior ticket medio?"
- "Qual e a distribuicao de pedidos por estado?"

**Vendedores e Produtos**
- "Quais sao os produtos mais vendidos por estado?"
- "Quais vendedores tem maior volume de vendas em R$?"

---

## Banco de Dados

SQLite3 com 7 tabelas (~63 MB):

| Tabela                   | Descricao                          | Registros |
|--------------------------|------------------------------------|-----------|
| `dim_consumidores`       | Dados dos consumidores             | ~99k      |
| `dim_produtos`           | Cadastro de produtos               | ~33k      |
| `dim_vendedores`         | Dados dos vendedores               | ~3k       |
| `fat_pedidos`            | Status e prazos de entrega         | ~99k      |
| `fat_pedido_total`       | Valores financeiros dos pedidos    | ~99k      |
| `fat_itens_pedidos`      | Itens individuais de cada pedido   | ~113k     |
| `fat_avaliacoes_pedidos` | Avaliacoes e comentarios           | ~95k      |

---

## Seguranca e Privacidade

**Guardrails (leitura apenas):**
- Apenas queries `SELECT` e `WITH` (CTEs) sao permitidas
- Comandos `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `ATTACH` sao bloqueados automaticamente

**Anonimizacao de dados pessoais:**
- Os campos `nome_consumidor` e `nome_vendedor` sao substituidos por pseudonimos deterministicos antes de chegarem ao modelo
- Formato: `Consumidor-XXXXXX` / `Vendedor-XXXXXX` (hash MD5 truncado)
- A anonimizacao e irreversivel mas consistente: o mesmo nome sempre gera o mesmo pseudonimo, preservando analises de agrupamento

---

## Licenca

MIT License — veja [LICENSE](LICENSE) para detalhes.
