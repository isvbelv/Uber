import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="Painel Uber", layout="wide")

st.sidebar.title("Painel do Eduardo")

menu = st.sidebar.radio("Navegação", ["Registrar Dia", "Histórico Diário", "Resumo Mensal", "Resumo Anual", "Comparar Meses"])

@st.cache_data

def carregar_dados():
    try:
        return pd.read_csv("dados_uber.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Data", "Valor Recebido", "KM Rodado", "Combustível", "Horas Trabalhadas", 
            "Gasto Comida", "Gasto Frentista", "Gasto Lavagem", "Gasto Oficina", "Gasto Outro", 
            "Desc Outro", "Trabalhou", "Meta", "Observações"
        ])


def salvar_dados(dados):
    dados.to_csv("dados_uber.csv", index=False)

dados = carregar_dados()

if menu == "Registrar Dia":
    st.title("Registrar dados do dia")
    data = st.date_input("Data", datetime.today())

    trabalhou = st.radio("Você trabalhou hoje?", ["Sim", "Não"])

    if trabalhou == "Sim":
        valor_recebido = st.number_input("Valor Recebido (R$)", 0.0)
        km_rodado = st.number_input("KM Rodado", 0.0)
        combustivel = st.number_input("Gasto com Combustível (R$)", 0.0)
        horas_trabalhadas = st.number_input("Horas Trabalhadas", 0.0)
        meta = st.number_input("Meta do Dia (R$)", 0.0)

        st.subheader("Outros Gastos")
        gasto_comida = st.number_input("Comida (R$)", 0.0)
        gasto_frentista = st.number_input("Frentista (R$)", 0.0)
        gasto_lavagem = st.number_input("Lava-Rápido (R$)", 0.0)
        gasto_oficina = st.number_input("Oficina (R$)", 0.0)
        gasto_outro = st.number_input("Outros (R$)", 0.0)
        desc_outro = ""
        if gasto_outro > 0:
            desc_outro = st.text_input("Descreva o gasto 'Outros'")

        observacoes = st.text_area("Observações do dia", "")

        if st.button("Salvar Registro"):
            novo_dado = pd.DataFrame([{
                "Data": data,
                "Valor Recebido": valor_recebido,
                "KM Rodado": km_rodado,
                "Combustível": combustivel,
                "Horas Trabalhadas": horas_trabalhadas,
                "Gasto Comida": gasto_comida,
                "Gasto Frentista": gasto_frentista,
                "Gasto Lavagem": gasto_lavagem,
                "Gasto Oficina": gasto_oficina,
                "Gasto Outro": gasto_outro,
                "Desc Outro": desc_outro,
                "Trabalhou": True,
                "Meta": meta,
                "Observações": observacoes
            }])
            dados = pd.concat([dados, novo_dado], ignore_index=True)
            salvar_dados(dados)
            st.success("Dados salvos com sucesso!")

    else:
        if st.button("Salvar como dia não trabalhado"):
            novo_dado = pd.DataFrame([{
                "Data": data,
                "Valor Recebido": 0,
                "KM Rodado": 0,
                "Combustível": 0,
                "Horas Trabalhadas": 0,
                "Gasto Comida": 0,
                "Gasto Frentista": 0,
                "Gasto Lavagem": 0,
                "Gasto Oficina": 0,
                "Gasto Outro": 0,
                "Desc Outro": "",
                "Trabalhou": False,
                "Meta": 0,
                "Observações": ""
            }])
            dados = pd.concat([dados, novo_dado], ignore_index=True)
            salvar_dados(dados)
            st.success("Dia registrado como não trabalhado.")

if menu == "Histórico Diário":
    st.title("Histórico Diário")
    st.dataframe(dados.sort_values("Data", ascending=False))

if menu == "Resumo Mensal":
    st.title("Resumo do Mês")
    mes = st.selectbox("Selecione o mês", sorted(dados['Data'].str[:7].unique(), reverse=True))
    df_mes = dados[dados['Data'].str.startswith(mes) & (dados['Trabalhou'] == True)]

    valor_bruto = df_mes["Valor Recebido"].sum()
    despesas = df_mes[["Combustível", "Gasto Comida", "Gasto Frentista", "Gasto Lavagem", "Gasto Oficina", "Gasto Outro"]].sum().sum()
    lucro_liquido = valor_bruto - despesas

    st.metric("Valor Bruto", f"R$ {valor_bruto:.2f}")
    st.metric("Despesas", f"R$ {despesas:.2f}")
    st.metric("Lucro Líquido", f"R$ {lucro_liquido:.2f}")

    st.subheader("Distribuição de Despesas")
    categorias = ["Combustível", "Gasto Comida", "Gasto Frentista", "Gasto Lavagem", "Gasto Oficina", "Gasto Outro"]
    valores = df_mes[categorias].sum()
    plt.figure(figsize=(6,6))
    plt.pie(valores, labels=categorias, autopct='%1.1f%%')
    st.pyplot(plt)

    if st.button("Exportar PDF do mês"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Resumo do mês {mes}", ln=True)
        pdf.cell(200, 10, txt=f"Valor Bruto: R$ {valor_bruto:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Despesas: R$ {despesas:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Lucro Líquido: R$ {lucro_liquido:.2f}", ln=True)

        buffer = BytesIO()
        pdf.output(buffer)
        st.download_button(label="Baixar PDF", data=buffer.getvalue(), file_name=f"Resumo_{mes}.pdf")

if menu == "Resumo Anual":
    st.title("Resumo Anual")
    ano = st.selectbox("Selecione o ano", sorted(dados['Data'].str[:4].unique(), reverse=True))
    df_ano = dados[dados['Data'].str.startswith(ano) & (dados['Trabalhou'] == True)]
    lucro_anual = df_ano["Valor Recebido"].sum() - df_ano[["Combustível", "Gasto Comida", "Gasto Frentista", "Gasto Lavagem", "Gasto Oficina", "Gasto Outro"]].sum().sum()
    st.metric("Lucro Total do Ano", f"R$ {lucro_anual:.2f}")

if menu == "Comparar Meses":
    st.title("Comparativo de Lucros por Mês")
    dados["Mês"] = dados["Data"].str[:7]
    df_mensal = dados[dados['Trabalhou'] == True].groupby("Mês").apply(
        lambda df: df["Valor Recebido"].sum() - df[["Combustível", "Gasto Comida", "Gasto Frentista", "Gasto Lavagem", "Gasto Oficina", "Gasto Outro"]].sum().sum()
    )
    df_mensal.plot(kind='bar', figsize=(10,5))
    plt.ylabel("Lucro Líquido (R$)")
    st.pyplot(plt)

    st.subheader("Indicadores Gerais")
    total_dias = len(dados)
    dias_trabalhados = dados[dados['Trabalhou'] == True].shape[0]
    dias_nao_trabalhados = total_dias - dias_trabalhados
    lucro_medio = dados[dados['Trabalhou'] == True]["Valor Recebido"].mean()
    metas_batidas = dados[(dados['Trabalhou'] == True) & (dados['Valor Recebido'] >= dados['Meta'])].shape[0]

    st.markdown(f"- Dias trabalhados: **{dias_trabalhados}**")
    st.markdown(f"- Dias sem trabalhar: **{dias_nao_trabalhados}**")
    st.markdown(f"- Lucro médio diário: **R$ {lucro_medio:.2f}**")
    st.markdown(f"- Dias com meta batida: **{metas_batidas}**")
