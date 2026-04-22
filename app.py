"""
Interface Visual - Agente de Analise de E-Commerce
====================================================
Interface de chat construida com Streamlit, com geracao automatica de graficos
a partir dos dados retornados pelo agente.

Como rodar:
    streamlit run app.py
"""

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from agent import EcommerceAgent

load_dotenv()

st.set_page_config(
    page_title="Agente de E-Commerce",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Agente de Analise de E-Commerce")
st.caption(
    f"Modelo: {os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')} | "
    f"Banco: {os.getenv('DB_PATH', 'files/banco.db')} | "
    "Dados pessoais anonimizados"
)

EXEMPLOS = {
    "Vendas e Receita": [
        "Quais sao os 10 produtos mais vendidos?",
        "Qual e a receita total por categoria de produto?",
        "Qual foi a evolucao mensal do numero de pedidos?",
    ],
    "Entrega e Logistica": [
        "Qual e a quantidade de pedidos por status?",
        "Qual e o percentual de pedidos entregues no prazo por estado?",
        "Quais estados tem maior atraso medio nas entregas?",
    ],
    "Satisfacao e Avaliacoes": [
        "Qual e a distribuicao de notas de avaliacao?",
        "Quais sao os 10 vendedores com maior media de avaliacao?",
        "Quais categorias tem maior taxa de avaliacao negativa?",
    ],
    "Consumidores": [
        "Quais estados tem maior volume de pedidos?",
        "Quais estados tem maior ticket medio?",
    ],
    "Vendedores e Produtos": [
        "Quais vendedores tem maior receita total?",
        "Quais categorias tem maior volume de vendas?",
    ],
}


@st.cache_resource(show_spinner="Inicializando agente...")
def carregar_agente():
    return EcommerceAgent(
        db_path=os.getenv("DB_PATH", "files/banco.db"),
        api_key=os.getenv("GEMINI_API_KEY"),
        model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )


try:
    agent = carregar_agente()
except Exception as e:
    st.error(f"Erro ao inicializar o agente: {e}")
    st.stop()

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "pergunta_exemplo" not in st.session_state:
    st.session_state.pergunta_exemplo = None


def detectar_colunas(df):
    numericas = df.select_dtypes(include="number").columns.tolist()
    categoricas = df.select_dtypes(exclude="number").columns.tolist()
    return numericas, categoricas


def contem_data(col):
    palavras = ["mes", "ano", "data", "periodo", "month", "year", "date", "trimestre"]
    return any(p in col.lower() for p in palavras)


def gerar_grafico(df, pergunta):
    if df is None or df.empty or len(df.columns) < 2:
        return None
    numericas, categoricas = detectar_colunas(df)
    if not numericas:
        return None
    col_num = numericas[0]
    col_cat = categoricas[0] if categoricas else df.columns[0]

    if any(contem_data(c) for c in df.columns):
        col_tempo = next((c for c in df.columns if contem_data(c)), col_cat)
        return px.line(
            df, x=col_tempo, y=col_num, markers=True, title=pergunta[:80],
            labels={col_tempo: col_tempo.replace("_", " ").title(),
                    col_num: col_num.replace("_", " ").title()},
        )

    if len(df) <= 20 and len(df.columns) == 2:
        fig = px.bar(
            df.sort_values(col_num, ascending=True),
            x=col_num, y=col_cat, orientation="h", title=pergunta[:80],
            labels={col_cat: col_cat.replace("_", " ").title(),
                    col_num: col_num.replace("_", " ").title()},
            color=col_num, color_continuous_scale="Blues",
        )
        fig.update_layout(coloraxis_showscale=False)
        return fig

    if categoricas and len(df) <= 30:
        fig = px.bar(
            df, x=col_cat, y=col_num, title=pergunta[:80],
            labels={col_cat: col_cat.replace("_", " ").title(),
                    col_num: col_num.replace("_", " ").title()},
            color=col_num, color_continuous_scale="Blues",
        )
        fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-35)
        return fig

    return None


with st.sidebar:
    st.header("Perguntas de Exemplo")
    st.write("Clique para enviar diretamente ao agente.")
    for categoria, perguntas in EXEMPLOS.items():
        with st.expander(categoria):
            for p in perguntas:
                if st.button(p, key=p, use_container_width=True):
                    st.session_state.pergunta_exemplo = p
    st.divider()
    if st.button("Nova conversa", use_container_width=True, type="secondary"):
        agent.nova_conversa()
        st.session_state.mensagens = []
        st.session_state.pergunta_exemplo = None
        st.rerun()
    st.divider()
    st.caption("Apenas leitura - queries SELECT sao permitidas.")
    st.caption("Dados pessoais anonimizados (nome_consumidor, nome_vendedor).")

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("grafico") is not None:
            st.plotly_chart(msg["grafico"], use_container_width=True)
        if msg.get("dados") is not None:
            with st.expander("Ver dados completos"):
                st.dataframe(msg["dados"], use_container_width=True)

pergunta = st.chat_input("Faca uma pergunta sobre os dados do e-commerce...")

if st.session_state.pergunta_exemplo:
    pergunta = st.session_state.pergunta_exemplo
    st.session_state.pergunta_exemplo = None

if pergunta:
    with st.chat_message("user"):
        st.markdown(pergunta)
    st.session_state.mensagens.append({"role": "user", "content": pergunta})

    with st.chat_message("assistant"):
        with st.spinner("Consultando banco de dados..."):
            resposta, df = agent.perguntar_com_dados(pergunta)
        st.markdown(resposta)
        grafico = None
        if df is not None and not df.empty:
            grafico = gerar_grafico(df, pergunta)
            if grafico:
                st.plotly_chart(grafico, use_container_width=True)
            with st.expander("Ver dados completos"):
                st.dataframe(df, use_container_width=True)

    st.session_state.mensagens.append({
        "role": "assistant",
        "content": resposta,
        "grafico": grafico,
        "dados": df if df is not None and not df.empty else None,
    })
