# 🛒 Agente de Análise de E-Commerce

Agente conversacional que permite a **usuários não técnicos** realizarem consultas e análises sobre dados de um sistema de e-commerce usando **linguagem natural em português**.

O agente traduz automaticamente perguntas para SQL (Text-to-SQL), executa as queries no banco de dados SQLite e retorna análises interpretadas — tudo sem que o usuário precise conhecer SQL ou estrutura de dados.

**Stack:**
- 🤖 Modelo: Google Gemini 2.5 Flash (`google-generativeai`)
- 🐍 Linguagem: Python 3.10+
- 🗄️ Banco: SQLite3 (embutido no Python, sem instalação extra)
- 🌐 API: FastAPI + Uvicorn
- 📓 Demo: Jupyter Notebook

---

## 📁 Estrutura do Projeto

```
.
├── agent.py           # 🤖 Núcleo do agente (Text-to-SQL + Gemini)
├── api.py             # 🌐 API REST com FastAPI
├── demo.ipynb         # 📓 Notebook Jupyter com exemplos
├── requirements.txt   # 📦 Dependências Python
├── .env.example       # ⚙️  Template de variáveis de ambiente
├── .gitignore
└── files/
    └── banco.db       # 🗄️  Banco SQLite (você precisa adicionar este arquivo)
```

---

## 🚀 Passo a Passo para Executar

### Pré-requisitos

- Python 3.10 ou superior
- Arquivo `banco.db` (disponível na pasta da atividade)
- Chave da API Gemini (gratuita em [aistudio.google.com](https://aistudio.google.com/apikey))

---

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

---

### 2. Crie e ative um ambiente virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

---

### 4. Configure as variáveis de ambiente

Copie o template e preencha com sua chave:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edite o arquivo `.env`:

```env
GEMINI_API_KEY=sua_chave_aqui
DB_PATH=files/banco.db
GEMINI_MODEL=gemini-2.5-flash
```

> 💡 **Como obter a chave gratuita:**  
> Acesse [aistudio.google.com/apikey](https://aistudio.google.com/apikey), faça login com sua conta Google e clique em **"Create API key"**.

---

### 5. Adicione o banco de dados

> ⚠️ O arquivo `banco.db` **não está versionado** no repositório por ser grande (~118 MB).  
> Você precisa obtê-lo separadamente e colocá-lo na pasta correta.

**Como obter o banco.db:**
- Faça o download do arquivo disponibilizado na pasta compartilhada da atividade (Google Drive / Teams)
- O arquivo se chama `banco.db`

**Onde colocar:**

```
rocketLab2026Agentes/
└── files/
    └── banco.db   ← coloque aqui
```

**Caminho esperado pelo agente:** `files/banco.db`

> 💡 Você pode usar um caminho diferente editando `DB_PATH` no arquivo `.env`:</p>
> ```
> DB_PATH=caminho/para/seu/banco.db
> ```

---

## 🎯 Formas de Usar

### Opção A — Jupyter Notebook (recomendada para demonstração)

```bash
jupyter notebook demo.ipynb
```

O notebook contém exemplos prontos para todas as categorias de análise:
- 📈 Vendas e Receita
- 🚚 Entrega e Logística
- ⭐ Satisfação e Avaliações
- 👥 Consumidores
- 🏪 Vendedores e Produtos

---

### Opção B — Script Python (terminal interativo)

```bash
python agent.py
```

Abre um chat interativo no terminal:

```
══════════════════════════════════════════════════════════════
  🛒  Agente de Análise de E-Commerce  |  Gemini 2.5 Flash
══════════════════════════════════════════════════════════════
  Digite sua pergunta sobre os dados do e-commerce.
  Comandos: 'novo' = nova conversa  |  'sair' = encerrar
══════════════════════════════════════════════════════════════

👤 Você: Quais são os 10 produtos mais vendidos?

🤖 Agente:
Os 10 produtos mais vendidos são: ...
```

---

### Opção C — API FastAPI

Suba o servidor:

```bash
uvicorn api:app --reload --port 8000
```

Acesse a documentação interativa em: **http://localhost:8000/docs**

**Exemplo de uso com curl:**

```bash
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"pergunta": "Top 10 produtos mais vendidos?"}'
```

**Exemplo de uso com Python:**

```python
import requests

resposta = requests.post(
    "http://localhost:8000/query",
    json={"pergunta": "Qual é a receita total por categoria de produto?"}
)
print(resposta.json()["resposta"])
```

**Endpoints disponíveis:**

| Método | Endpoint     | Descrição                              |
|--------|-------------|----------------------------------------|
| GET    | `/`         | Informações da API                     |
| GET    | `/health`   | Health check                           |
| GET    | `/exemplos` | Lista de perguntas de exemplo          |
| POST   | `/query`    | Envia pergunta ao agente               |
| POST   | `/reset`    | Reinicia o histórico de conversa       |

---

### Opção D — Uso como Biblioteca Python

```python
from agent import EcommerceAgent

agent = EcommerceAgent(db_path="files/banco.db")

# Pergunta simples
print(agent.perguntar("Quais são os 10 produtos mais vendidos?"))

# Pergunta de follow-up (mantém contexto)
print(agent.perguntar("E qual é a receita total desses produtos?"))

# Reiniciar conversa
agent.nova_conversa()
```

---

## 💡 Exemplos de Perguntas

### Análise de Vendas e Receita
- *"Quais são os 10 produtos mais vendidos?"*
- *"Qual é a receita total por categoria de produto?"*
- *"Qual foi o mês com maior volume de vendas?"*

### Análise de Entrega e Logística
- *"Qual é a quantidade de pedidos por status?"*
- *"Qual é o percentual de pedidos entregues no prazo por estado?"*
- *"Quais estados têm maior atraso médio nas entregas?"*

### Análise de Satisfação e Avaliações
- *"Qual é a média geral de avaliação dos pedidos?"*
- *"Quais são os 10 vendedores com maior média de avaliação?"*
- *"Quais categorias têm maior taxa de avaliação negativa?"*

### Análise de Consumidores
- *"Quais estados têm maior volume de pedidos e maior ticket médio?"*
- *"Qual é a distribuição de pedidos por estado?"*

### Análise de Vendedores e Produtos
- *"Quais são os produtos mais vendidos por estado?"*
- *"Quais vendedores têm maior volume de vendas em R$?"*

---

## 🗄️ Banco de Dados

O banco `banco.db` é um SQLite3 com 7 tabelas:

| Tabela                   | Descrição                          | Registros |
|--------------------------|------------------------------------|-----------|
| `dim_consumidores`       | Dados dos consumidores             | ~99k      |
| `dim_produtos`           | Cadastro de produtos               | ~33k      |
| `dim_vendedores`         | Dados dos vendedores               | ~3k       |
| `fat_pedidos`            | Status e prazos de entrega         | ~99k      |
| `fat_pedido_total`       | Valores financeiros dos pedidos    | ~99k      |
| `fat_itens_pedidos`      | Itens individuais de cada pedido   | ~113k     |
| `fat_avaliacoes_pedidos` | Avaliações e comentários           | ~95k      |

---

## 🔒 Segurança (Guardrails)

O agente possui proteções embutidas que impedem operações destrutivas:

- ✅ Apenas queries `SELECT` e `WITH` (CTEs) são permitidas
- ❌ Comandos `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER` são bloqueados automaticamente
- ❌ Comandos `ATTACH`, `DETACH` e `PRAGMA` também são bloqueados
- 📊 Resultados são limitados a 50 linhas no contexto do modelo (proteção contra sobrecarga)

---

## 🛠️ Solução de Problemas

**`GEMINI_API_KEY não encontrada`**
→ Verifique se o arquivo `.env` existe e contém a chave correta.

**`Banco de dados não encontrado`**
→ Confirme que `banco.db` está em `files/banco.db` (ou ajuste `DB_PATH` no `.env`).

**`ModuleNotFoundError`**
→ Execute `pip install -r requirements.txt` com o ambiente virtual ativado.

**Erro de modelo não encontrado**
→ Verifique os modelos disponíveis em [ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models) e atualize `GEMINI_MODEL` no `.env`.

---

## 📄 Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.
