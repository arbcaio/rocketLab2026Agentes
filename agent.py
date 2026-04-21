"""
Agente de Análise de E-Commerce com Text-to-SQL
================================================
Powered by Google Gemini 2.5 Flash

Permite que usuarios nao tecnicos facam perguntas em portugues sobre os dados
do e-commerce e recebam respostas interpretadas com base em queries SQL geradas
automaticamente pelo modelo.

Uso rapido:
    from agent import EcommerceAgent
    agent = EcommerceAgent(db_path="files/banco.db")
    resposta = agent.perguntar("Quais sao os 10 produtos mais vendidos?")
    print(resposta)
"""

import sqlite3
import re
import os
from typing import Optional

import pandas as pd
from tabulate import tabulate
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# SCHEMA DO BANCO DE DADOS (contexto para o modelo)
# =============================================================================

SCHEMA_DESCRIPTION = """
## Banco de Dados: Sistema de E-Commerce (SQLite)

### Tabelas Disponiveis:

**dim_consumidores** - Informacoes dos consumidores (99.441 registros)
- id_consumidor (TEXT): Identificador unico do consumidor
- prefixo_cep (INTEGER): Prefixo do CEP (5 digitos)
- nome_consumidor (TEXT): Nome anonimizado
- cidade (TEXT): Cidade do consumidor
- estado (TEXT): Estado em sigla (SP, RJ, MG, etc.)

**dim_produtos** - Cadastro de produtos (32.951 registros)
- id_produto (TEXT): Identificador unico do produto
- nome_produto (TEXT): Nome do produto
- categoria_produto (TEXT): Categoria (ex: informatica, beleza_saude, moveis_decoracao)
- peso_produto_gramas (REAL): Peso em gramas
- comprimento_centimetros, altura_centimetros, largura_centimetros (REAL): Dimensoes

**dim_vendedores** - Dados dos vendedores (3.095 registros)
- id_vendedor (TEXT): Identificador unico do vendedor
- nome_vendedor (TEXT): Nome do vendedor
- prefixo_cep (INTEGER): Prefixo do CEP
- cidade (TEXT): Cidade do vendedor
- estado (TEXT): Estado do vendedor

**fat_pedidos** - Informacoes de entrega de cada pedido (99.441 registros)
- id_pedido (TEXT): Identificador unico do pedido
- id_consumidor (TEXT): FK -> dim_consumidores.id_consumidor
- status (TEXT): Status do pedido (entregue, enviado, cancelado, aprovado, faturado, criado, em processamento, indisponivel)
- pedido_compra_timestamp (TEXT): Data/hora da compra (formato: YYYY-MM-DD HH:MM:SS)
- pedido_entregue_timestamp (TEXT): Data/hora real da entrega
- data_estimada_entrega (TEXT): Data estimada de entrega (YYYY-MM-DD)
- tempo_entrega_dias (REAL): Dias ate a entrega real
- tempo_entrega_estimado_dias (INTEGER): Dias estimados para entrega
- diferenca_entrega_dias (REAL): Diferenca em dias (negativo = entregue antes do prazo)
- entrega_no_prazo (TEXT): 'Sim', 'Nao', ou 'Nao Entregue'

**fat_pedido_total** - Valores financeiros dos pedidos (99.441 registros)
- id_pedido (TEXT): Identificador unico do pedido
- id_consumidor (TEXT): FK -> dim_consumidores.id_consumidor
- status (TEXT): Status do pedido
- valor_total_pago_brl (REAL): Valor total pago em R$
- valor_total_pago_usd (REAL): Valor total pago em USD
- data_pedido (TEXT): Data do pedido (YYYY-MM-DD)

**fat_itens_pedidos** - Itens individuais de cada pedido (112.650 registros)
- id_pedido (TEXT): FK -> fat_pedidos.id_pedido
- id_item (INTEGER): Numero sequencial do item no pedido
- id_produto (TEXT): FK -> dim_produtos.id_produto
- id_vendedor (TEXT): FK -> dim_vendedores.id_vendedor
- preco_BRL (REAL): Preco do item em R$
- preco_frete (REAL): Preco do frete em R$

**fat_avaliacoes_pedidos** - Avaliacoes dos clientes (95.307 registros)
- id_avaliacao (TEXT): Identificador unico da avaliacao
- id_pedido (TEXT): FK -> fat_pedidos.id_pedido
- avaliacao (INTEGER): Nota de 1 a 5
- titulo_comentario (TEXT): Titulo do comentario
- comentario (TEXT): Texto completo do comentario
- data_comentario (TEXT): Data em que o comentario foi feito
- data_resposta (TEXT): Data da resposta ao comentario

### Relacionamentos Principais:
- fat_pedidos <-> fat_pedido_total <-> fat_itens_pedidos <-> fat_avaliacoes_pedidos (por id_pedido)
- fat_itens_pedidos -> dim_produtos (por id_produto)
- fat_itens_pedidos -> dim_vendedores (por id_vendedor)
- fat_pedidos / fat_pedido_total -> dim_consumidores (por id_consumidor)
"""

SYSTEM_PROMPT = f"""Voce e um assistente especialista em analise de dados de e-commerce.
Voce tem acesso a um banco de dados SQLite e deve usar a ferramenta `executar_sql` para buscar dados antes de responder.

{SCHEMA_DESCRIPTION}

## Instrucoes de Uso:
1. SEMPRE chame a ferramenta executar_sql para buscar dados antes de dar uma resposta definitiva
2. Escreva queries SQL corretas e eficientes para SQLite
3. Use LIMIT para controlar resultados (ex: LIMIT 10 para top N, LIMIT 500 para analises gerais)
4. Responda em portugues brasileiro, de forma clara e objetiva
5. Interprete os dados - nao apenas apresente numeros brutos
6. Adicione insights e observacoes relevantes sobre os resultados
7. Use aliases descritivos em portugues nas colunas SQL (ex: COUNT(*) AS total_pedidos)
8. Para analises complexas, execute multiplas queries em sequencia
9. Ao apresentar percentuais, arredonde para 1 casa decimal

## Regras de Seguranca:
- APENAS queries SELECT (ou WITH para CTEs) sao permitidas
- Nunca execute INSERT, UPDATE, DELETE, DROP, ALTER ou qualquer comando de modificacao
- Nunca acesse tabelas que nao estejam listadas no schema acima
"""


# =============================================================================
# CLASSE PRINCIPAL DO AGENTE
# =============================================================================

class EcommerceAgent:
    """
    Agente de analise de e-commerce com capacidades Text-to-SQL.

    Transforma perguntas em portugues natural em queries SQL,
    executa-as no banco SQLite e interpreta os resultados usando
    o modelo Gemini da Google.

    Exemplo de uso:
        agent = EcommerceAgent(db_path="files/banco.db")
        print(agent.perguntar("Quais sao os 10 produtos mais vendidos?"))
    """

    def __init__(
        self,
        db_path: str = "files/banco.db",
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
    ):
        """
        Inicializa o agente.

        Args:
            db_path: Caminho para o arquivo banco.db.
            api_key: Chave da API Gemini. Se None, le de GEMINI_API_KEY no .env.
            model_name: Nome do modelo Gemini. Padrao: 'gemini-2.5-flash'.
        """
        self.db_path = db_path
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY nao encontrada!\n"
                "  Opcao 1: crie um arquivo .env com  GEMINI_API_KEY=sua_chave\n"
                "  Opcao 2: passe como parametro  EcommerceAgent(api_key='sua_chave')"
            )

        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"Banco de dados nao encontrado: '{db_path}'\n"
                "  Coloque o arquivo banco.db na pasta indicada."
            )

        genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=[self.executar_sql],
            system_instruction=SYSTEM_PROMPT,
        )

        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

        print(f"Agente de E-Commerce inicializado.")
        print(f"  Modelo : {model_name}")
        print(f"  Banco  : {db_path}")

    # -------------------------------------------------------------------------
    # FERRAMENTA SQL (chamada automaticamente pelo modelo)
    # -------------------------------------------------------------------------

    def executar_sql(self, query: str) -> str:
        """
        Executa uma query SQL SELECT no banco de dados de e-commerce e retorna
        os resultados em formato tabular.

        Args:
            query: Query SQL SELECT (ou WITH) a ser executada.

        Returns:
            Resultado em formato de tabela Markdown ou mensagem de erro.
        """
        query_upper = query.strip().upper()

        comandos_proibidos = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
            "ALTER", "TRUNCATE", "REPLACE", "ATTACH", "DETACH",
        ]
        for cmd in comandos_proibidos:
            if re.search(r"\b" + cmd + r"\b", query_upper):
                return (
                    f"ERRO DE SEGURANCA: Comando '{cmd}' nao e permitido. "
                    "Use apenas queries SELECT ou WITH (CTEs)."
                )

        if not query_upper.startswith("SELECT") and not query_upper.startswith("WITH"):
            return "ERRO: Somente queries que comecam com SELECT ou WITH sao permitidas."

        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                return "Nenhum resultado encontrado para esta consulta."

            n_total = len(df)
            n_exibir = min(n_total, 50)

            header = f"Resultados: {n_total} linha{'s' if n_total != 1 else ''}"
            if n_total > n_exibir:
                header += f" (exibindo as primeiras {n_exibir})"
            header += "\n\n"

            tabela = tabulate(
                df.head(n_exibir),
                headers="keys",
                tablefmt="pipe",
                showindex=False,
                floatfmt=".2f",
            )

            return header + tabela

        except sqlite3.Error as e:
            return f"ERRO SQL: {str(e)}\nQuery: {query}"
        except Exception as e:
            return f"ERRO inesperado: {str(e)}"

    # -------------------------------------------------------------------------
    # INTERFACE PUBLICA
    # -------------------------------------------------------------------------

    def perguntar(self, pergunta: str) -> str:
        """
        Envia uma pergunta em linguagem natural ao agente e retorna a resposta.

        Args:
            pergunta: Pergunta em portugues sobre os dados do e-commerce.

        Returns:
            Resposta do agente com analise e interpretacao dos dados.
        """
        try:
            response = self.chat.send_message(pergunta)
            return response.text
        except Exception as e:
            return f"Erro ao processar a pergunta: {str(e)}"

    def nova_conversa(self):
        """Reinicia o historico de conversa."""
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)
        print("Nova conversa iniciada. Historico limpo.")

    def chat_interativo(self):
        """
        Inicia um loop de chat interativo no terminal.

        Comandos especiais:
            'sair'  -> encerra o agente
            'novo'  -> reinicia o historico de conversa
        """
        print("\n" + "=" * 62)
        print("  Agente de Analise de E-Commerce  |  Gemini")
        print("=" * 62)
        print("  Digite sua pergunta sobre os dados do e-commerce.")
        print("  Comandos: 'novo' = nova conversa  |  'sair' = encerrar")
        print("=" * 62 + "\n")

        while True:
            try:
                pergunta = input("Voce: ").strip()

                if not pergunta:
                    continue

                if pergunta.lower() in ("sair", "exit", "quit"):
                    print("\nAte logo!")
                    break

                if pergunta.lower() in ("novo", "reset", "reiniciar"):
                    self.nova_conversa()
                    continue

                print("\nAgente:\n")
                resposta = self.perguntar(pergunta)
                print(resposta)
                print()

            except KeyboardInterrupt:
                print("\n\nAte logo!")
                break
            except Exception as e:
                print(f"\nErro: {e}\n")


# =============================================================================
# EXECUCAO DIRETA
# =============================================================================

if __name__ == "__main__":
    agent = EcommerceAgent(
        db_path=os.getenv("DB_PATH", "files/banco.db"),
        model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )
    agent.chat_interativo()
