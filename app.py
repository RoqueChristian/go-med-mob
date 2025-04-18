import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os

st.set_page_config(page_title="Go MED SAÚDE", page_icon=":bar_chart:", layout="wide")

# Configurações Globais
CAMINHO_ARQUIVO_IMAGENS = "go_med_saude.jpeg"
CAMINHO_ARQUIVO_VENDAS = "df_vendas.csv"
MESES_ABREVIADOS = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

def carregar_dados(caminho_arquivo):
    try:
        df = pd.read_csv(caminho_arquivo)
        if df.empty:
            st.warning("O arquivo CSV está vazio.")
            return None
        return df
    except FileNotFoundError:
        st.error("Arquivo não encontrado!")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
        return None

def formatar_moeda(valor, simbolo_moeda="R$"):
    if pd.isna(valor):
        return ''
    try:
        return f"{simbolo_moeda} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "Valor inválido"

def calcular_metricas(df):
    """Calcula métricas de vendas, incluindo o Ticket Médio Geral."""
    total_nf = len(df['NF'].unique())
    total_qtd_produto = df['Qtd_Produto'].sum()
    valor_total_item = df['Valor_Total_Item'].sum()
    total_custo_compra = df['Total_Custo_Compra'].sum()
    total_lucro_venda = df['Total_Lucro_Venda_Item'].sum()

    ticket_medio_geral = valor_total_item / total_nf if total_nf > 0 else 0

    return total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda, ticket_medio_geral

def agrupar_e_somar(df, coluna_agrupamento):
    return df.groupby(coluna_agrupamento).agg(
        {'Valor_Total_Item': 'sum', 'Total_Custo_Compra': 'sum', 'Total_Lucro_Venda_Item': 'sum'}
    ).reset_index()

def ranking_clientes(df, top_n=5, max_len=25):
    """Retorna os top N clientes com maior faturamento total, incluindo o número do ranking."""
    df_clientes = df.groupby('Cliente').agg({'Valor_Total_Item': 'sum'}).reset_index()
    df_clientes = df_clientes.sort_values(by='Valor_Total_Item', ascending=False).head(top_n)
    df_clientes['Ranking'] = range(1, len(df_clientes) + 1)
    df_clientes['Valor_Total_Item'] = df_clientes['Valor_Total_Item'].apply(formatar_moeda)
    df_clientes = df_clientes[['Ranking', 'Cliente', 'Valor_Total_Item']]
    df_clientes['Cliente'] = df_clientes['Cliente'].str[:max_len]
    return df_clientes

def produtos_mais_vendidos(df, top_n=5, ordenar_por='Valor_Total_Item', max_len=15):
    df_agrupado = df.groupby('Descricao_produto')[ordenar_por].sum().reset_index()
    df_ordenado = df_agrupado.sort_values(by=ordenar_por, ascending=False)
    df_ordenado['Descricao_produto'] = df_ordenado['Descricao_produto'].str[:max_len]
    return df_ordenado.head(top_n)

def criar_grafico_barras(df, x, y, title, labels):
    df = df.sort_values(by=y, ascending=False)
    df['Valor_Monetario'] = df['Valor_Total_Item'].apply(formatar_moeda)
    fig = px.bar(df, x=x, y=y,
                title=title,
                labels={labels.get(x, x): labels.get(x, x), labels.get(y, y): labels.get(y, y)},
                text=df['Valor_Monetario'],
                template="ggplot2",
                hover_data={y: False, x: False, 'Valor_Monetario': True},
                orientation='v')
    fig.update_traces(
        marker=dict(line=dict(color='black', width=1), color='blue'),
        textfont=dict(size=18, color='#ffffff'),
        textangle=-0,
        textposition='inside',
    )
    fig.update_layout(
        yaxis_title=labels.get(y, y),
        xaxis_title=labels.get(x, x),
        showlegend=False,
        height=400,
        width=350,
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(
            title=dict(
                text=labels.get(y, y),
                font=dict(size=12)
            ),
            tickfont=dict(size=10),
        ),
        title_font=dict(size=18, family="Times New Roman"),
        margin=dict(l=10, r=10)
    )
    return fig

def criar_grafico_vendas_diarias(df, mes, ano):
    df_filtrado = df[(df['Mes'] == mes) & (df['Ano'] == ano)]
    vendas_diarias = df_filtrado.groupby('Dia')['Valor_Total_Item'].sum().reset_index()
    vendas_diarias["Valor_Monetario"] = vendas_diarias["Valor_Total_Item"].apply(formatar_moeda)

    fig = px.bar(
        vendas_diarias,
        x='Dia',
        y='Valor_Total_Item',
        title=f'Vendas Diárias em {mes}/{ano}',
        labels={'Dia': 'Dia', 'Valor_Total_Item': 'Valor Total de Venda'},
        text=vendas_diarias["Valor_Monetario"]
    )

    fig.update_traces(
        marker=dict(line=dict(color='black', width=1), color='green'),
        textfont=dict(color='white')
    )

    fig.update_layout(
        showlegend=False,
        height=300,
        width=300,
        title_font=dict(size=14)
    )

    return fig


def criar_grafico_pizza_vendas_linha(df):
    """Cria um gráfico de pizza mostrando as vendas por linha de produto."""
    df_linha = df.groupby('Linha')['Valor_Total_Item'].sum().reset_index()
    fig = px.pie(df_linha, values='Valor_Total_Item', names='Linha',
                title='Vendas por Linha de Produto',
                hover_data=['Valor_Total_Item'])
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(size=14)  # Ajuste para telas menores
    )
    fig.update_layout(
        height=400, width=350,  # Ajuste para telas menores
        showlegend=True,
        title_font=dict(size=20, family="Times New Roman")  # Ajuste para telas menores
    )
    return fig

def aplicar_filtros(df, vendedor='Todos', mes=None, ano=None, situacao='Faturada'):
    """Aplica filtros aos dados."""
    df_filtrado = df.copy()
    if ano is None:
        ano = datetime.datetime.now().year
    if mes is None:
        mes = datetime.datetime.now().month
    if vendedor != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Vendedor'] == vendedor]
    if mes is not None:
        df_filtrado = df_filtrado[df_filtrado['Mes'] == mes]
    if ano is not None:
        df_filtrado = df_filtrado[df_filtrado['Ano'] == ano]
    if situacao != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['situacao'] == situacao]
    return df_filtrado

def processar_dados_ticket_medio(df):
    df['Data_Emissao'] = pd.to_datetime(df['Data_Emissao'], format='mixed', dayfirst=True)
    colunas_nf_unicas = ['NF', 'Data_Emissao', 'Vendedor', 'Valor_Total_Nota', 'Mes', 'Ano', 'situacao']
    df_nf_unicas = df.drop_duplicates(subset='NF')[colunas_nf_unicas].copy()
    df_nf_unicas = df_nf_unicas[df_nf_unicas['situacao'] == 'Faturada']

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month

    df_nf_unicas = aplicar_filtros(df_nf_unicas, mes=mes_atual, ano=ano_atual)

    df_ticket_medio = df_nf_unicas.groupby('Vendedor')['Valor_Total_Nota'].mean().reset_index(name='Ticket_Medio')
    df_ticket_medio['Ticket Medio'] = df_ticket_medio['Ticket_Medio'].apply(formatar_moeda) 
    
    return df_ticket_medio

def exibir_grafico_ticket_medio(df_ticket_medio):
    df_ticket_medio['Ticket Medio'] = df_ticket_medio['Ticket_Medio'].apply(formatar_moeda)

    fig = px.bar(
        df_ticket_medio,
        x="Vendedor",
        y="Ticket_Medio",
        title="Ticket Médio por Vendedor",
        labels={"Ticket_Medio": "Ticket Médio", "Vendedor": "Vendedor"},
        text=df_ticket_medio["Ticket Medio"],
        template="plotly_dark",
        hover_data={"Vendedor": False, "Ticket_Medio": False, 'Ticket Medio': True}
    )

    fig.update_traces(
        marker=dict(line=dict(color='black', width=1)),
        hoverlabel=dict(bgcolor="black", font_size=18, font_family="Arial, sans-serif"),
        textfont=dict(size=14, color='#ffffff', family="Arial, sans-serif"),
        textposition='outside',
        cliponaxis=False
    )

    fig.update_layout(
        yaxis_title="Ticket Médio",
        xaxis_title="Vendedor",
        showlegend=False,
        height=400, width=350,
        xaxis=dict(tickfont=dict(size=14)),
        yaxis=dict(
            title=dict(
                text="Ticket Médio",
                font=dict(size=14)
            ),
            tickfont=dict(size=14),
        ),
        title_font=dict(size=16, family="Times New Roman"),
        bargap=0.1
    )

    return fig



def renderizar_pagina_vendas(df):
    df_filtrado = aplicar_filtros(df)

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month

    total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda, ticket_medio_geral = calcular_metricas(df_filtrado)

    def card_style(metric_name, value, color="#FFFFFF", bg_color="#262730"):
        return f"""
        <div style="
            padding: 10px;
            border-radius: 10px;
            background-color: {bg_color};
            color: {color};
            text-align: center;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; font-size: 16px;">{metric_name}</h4>
            <h2 style="margin: 5px 0; font-size: 20px;">{value}</h2>
        </div>
        """

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(card_style("Total de Notas", f"{total_nf}"), unsafe_allow_html=True)
    with col2:
        st.markdown(card_style("Total de Produtos", f"{total_qtd_produto}"), unsafe_allow_html=True)
    with col3:
        st.markdown(card_style("Faturamento Total", formatar_moeda(valor_total_item)), unsafe_allow_html=True)
    with col4:
        st.markdown(card_style("Ticket Médio", formatar_moeda(ticket_medio_geral)), unsafe_allow_html=True)

    df_ticket_medio = processar_dados_ticket_medio(df_filtrado)

    df_ranking = ranking_clientes(df_filtrado)
    df_ranking = df_ranking.reset_index(drop=True)
    df_ranking = df_ranking.iloc[::-1]
    
    df_ranking["Cliente Curto"] = df_ranking["Cliente"].apply(lambda x: x[:25] + '...' if len(x) > 10 else x)


    fig = px.bar(
        df_ranking,
        x="Cliente Curto",
        y="Valor_Total_Item",
        orientation="v",
        title="Top Clientes por Faturamento",
        labels={"Valor_Total_Item": "Faturamento (R$)", "Cliente": "Clientes"},
        text=df_ranking["Valor_Total_Item"]
    )

    fig.update_traces(
        textposition="outside",
        textfont=dict(size=18, color="white")
    )

    fig.update_layout(
        height=600,
        width=300,
        title_font=dict(size=14),
        xaxis={'categoryorder':'total descending'}
    )

    graphs = [
        criar_grafico_vendas_diarias(df_filtrado, mes_atual, ano_atual),
        criar_grafico_barras(agrupar_e_somar(df_filtrado, 'Vendedor'), 'Vendedor', 'Valor_Total_Item', 'Vendas por Vendedor', {'Valor_Total_Item': 'Valor Total de Venda'}),
        criar_grafico_barras(produtos_mais_vendidos(df_filtrado), 'Descricao_produto', 'Valor_Total_Item', 'Top 5 Produtos Mais Vendidos', {'Descricao_produto': 'Produto', 'Valor_Total_Item': 'Valor Total de Venda'}),
        criar_grafico_pizza_vendas_linha(df_filtrado),
        exibir_grafico_ticket_medio(df_ticket_medio),
        fig
    ]

    for graph in graphs:
        st.plotly_chart(graph)

def main():
    caminho_arquivo = CAMINHO_ARQUIVO_VENDAS

    if caminho_arquivo and os.path.exists(caminho_arquivo):
        try:
            df = carregar_dados(caminho_arquivo)
            if df is not None:
                renderizar_pagina_vendas(df)

        except Exception as e:
            st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
    else:
        st.error("Arquivo não encontrado!")

if __name__ == "__main__":
    main()