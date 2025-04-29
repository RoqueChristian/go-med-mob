import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import datetime
import time
import os
import plotly.graph_objects as go

st.set_page_config(page_title="Go MED SAÚDE", page_icon=":bar_chart:", layout="wide")

CAMINHO_ARQUIVO_IMAGENS = "go_med_saude.jpeg"
CAMINHO_ARQUIVO_VENDAS = "df_vendas.csv"
MESES_ABREVIADOS = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

METAS_VENDEDORES = {
    'VERIDIANA SERRA': 500000.00,
    'CESAR GAMA': 400000.00,
    'JORGE TOTE': 150000.00,
    'FABIAN SILVA': 100000.00,
    'DENIS SOUSA': 1000000.00,
    'THIAGO SOUSA': 300000.00
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
    """Calcula métricas de vendas, incluindo o Ticket Médio Geral e a porcentagem de lucro."""
    total_nf = len(df['NF'].unique())
    total_qtd_produto = df['Qtd_Produto'].sum()
    valor_total_item = df['Valor_Total_Item'].sum()
    total_custo_compra = df['Total_Custo_Compra'].sum()
    total_lucro_venda_absoluto = df['Total_Lucro_Venda_Item'].sum()

    ticket_medio_geral = valor_total_item / total_nf if total_nf > 0 else 0
    porcentagem_lucro_venda = (total_lucro_venda_absoluto / valor_total_item * 100) if valor_total_item > 0 else 0

    return total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda_absoluto, ticket_medio_geral, porcentagem_lucro_venda


def agrupar_e_somar(df, coluna_agrupamento, funcoes_agregacao=None):
    if funcoes_agregacao is None:
        funcoes_agregacao = {'Valor_Total_Item': 'sum', 'Total_Custo_Compra': 'sum', 'Total_Lucro_Venda_Item': 'sum'}
    return df.groupby(coluna_agrupamento).agg(funcoes_agregacao).reset_index()


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


def exibir_grafico_ticket_medio(df_ticket_medio):
    fig = px.bar(
        df_ticket_medio,
        x='Vendedor',
        y='Ticket_Medio',
        title='Ticket Médio por Vendedor',
        labels={'Ticket_Medio': 'Ticket Médio', 'Vendedor': 'Vendedor'},
        text=df_ticket_medio['Ticket Medio'],
        hover_data={'Vendedor': False, 'Ticket_Medio': False, 'Ticket_Medio': True}
    )

    fig.update_traces(
        marker=dict(line=dict(color='black', width=1)),
        hoverlabel=dict(bgcolor='black', font_size=22, font_family='Arial, sans-serif'),
        textfont=dict(size=20, color='#ffffff', family='Arial, sans-serif'),
        textposition='outside',
        cliponaxis=False
    )

    fig.update_layout(
        yaxis_title='Ticket Médio',
        xaxis_title='Vendedor',
        showlegend=False,
        height=300,
        width=300,
        xaxis=dict(tickfont=dict(size=12)),
        yaxis=dict(
            title=dict(
                text='Ticket Médio',
                font=dict(size=14),
            ),
            tickfont=dict(size=14)
        ),
        title_font=dict(size=22, family='Times New Roman'),
        bargap=0.1
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
    # Certifique-se de que as colunas abaixo existem no seu DataFrame
    colunas_nf_unicas = ['NF', 'Data_Emissao', 'Vendedor', 'Valor_Total_Nota', 'Mes', 'Ano', 'situacao']
    # Verifique se todas as colunas esperadas estão presentes
    colunas_presentes = all(col in df.columns for col in colunas_nf_unicas)
    if not colunas_presentes:
        st.error(f"Erro: Algumas colunas esperadas ({colunas_nf_unicas}) não foram encontradas no DataFrame.")
        return pd.DataFrame(columns=['Vendedor', 'Ticket_Medio', 'Ticket Medio'])  # Retorna um DataFrame vazio para evitar erros posteriores

    df_nf_unicas = df.drop_duplicates(subset='NF')[colunas_nf_unicas].copy()
    df_nf_unicas = df_nf_unicas[df_nf_unicas['situacao'] == 'Faturada']

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month

    df_nf_unicas = aplicar_filtros(df_nf_unicas, mes=mes_atual, ano=ano_atual)

    df_ticket_medio = df_nf_unicas.groupby('Vendedor')['Valor_Total_Nota'].mean().reset_index(name='Ticket_Medio')
    df_ticket_medio['Ticket Medio'] = df_ticket_medio['Ticket_Medio'].apply(formatar_moeda)

    return df_ticket_medio


def criar_grafico_barras_vendas_linha(df):
    df_grouped = df.groupby('Linha')['Valor_Total_Item'].sum().reset_index()
    total_vendas = df_grouped['Valor_Total_Item'].sum()
    df_grouped['Porcentagem'] = (df_grouped['Valor_Total_Item'] / total_vendas) * 100
    df_grouped = df_grouped.sort_values(by='Valor_Total_Item', ascending=False)

    fig = px.bar(df_grouped, x='Linha', y='Valor_Total_Item',
                 title='Participação de Vendas por Linha de Produto',
                 hover_data=['Valor_Total_Item', 'Porcentagem'],
                 text='Porcentagem')

    fig.update_traces(
        texttemplate='%{text:.2f}%',
        textposition='outside',
        textfont_size=20
    )

    fig.update_layout(
        height=600,
        width=100,
        showlegend=False,
        title_font=dict(size=22, family="Times New Roman"),
        xaxis_title='Linha de Produto',
        yaxis_title='Valor Total de Vendas',
        yaxis=dict(tickformat=',.2f'),
        xaxis=dict(
            tickfont=dict(size=12)
        )
    )
    return fig


def calcular_performance_vendedores(df_vendas):
    # Filtrar os vendedores diferentes de 'GERAL VENDAS' E 'NATALIA SILVA'
    vendas_por_vendedor_filtrado = df_vendas[
        (df_vendas['Vendedor'] != 'GERAL VENDAS') & (df_vendas['Vendedor'] != 'NATALIA SILVA')
    ].copy()

    # Realizar o groupby e os cálculos no DataFrame filtrado
    vendas_por_vendedor = vendas_por_vendedor_filtrado.groupby('Vendedor')['Valor_Total_Item'].sum().reset_index()
    vendas_por_vendedor = vendas_por_vendedor.rename(columns={'Valor_Total_Item': 'Total_Vendido'})

    vendas_por_vendedor['Meta'] = vendas_por_vendedor['Vendedor'].map(METAS_VENDEDORES).fillna(0)
    vendas_por_vendedor['Porcentagem_Atingida'] = (vendas_por_vendedor['Total_Vendido'] / vendas_por_vendedor['Meta'] * 100).fillna(0).round(2)
    vendas_por_vendedor['Meta_Formatada'] = vendas_por_vendedor['Meta'].apply(formatar_moeda)
    vendas_por_vendedor['Total_Vendido_Formatado'] = vendas_por_vendedor['Total_Vendido'].apply(formatar_moeda)
    vendas_por_vendedor['Porcentagem_Texto'] = vendas_por_vendedor['Porcentagem_Atingida'].astype(str) + '%'

    return vendas_por_vendedor


def criar_grafico_performance_vendedores(df_performance):
    fig = go.Figure()

    max_meta = df_performance['Meta'].max()
    limite_superior_yaxis = max_meta * 1.2

    # Barra de Meta (Background)
    fig.add_trace(go.Bar(
        x=df_performance['Vendedor'],
        y=df_performance['Meta'],
        name='Meta',
        marker=dict(color='lightgrey'),
        text=df_performance['Meta_Formatada'],
        textposition='outside',
        insidetextanchor='end',
        textfont=dict(size=20, color='#ffffff', family="Arial, sans-serif")
    ))

    fig.add_trace(go.Bar(
        x=df_performance['Vendedor'],
        y=df_performance['Total_Vendido'],
        name='Total Vendido',
        marker_color='skyblue',
        text=df_performance['Total_Vendido_Formatado'],
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(size=18, color='#000', family="Arial, sans-serif")
    ))

    altura_anotacao = max_meta * 0.05  # 5% da maior meta acima

    for index, row in df_performance.iterrows():
        # Condição para verificar se o vendedor passou da meta
        if row['Total_Vendido'] > row['Meta']:
            y_pos_annotation = row['Meta'] + altura_anotacao
            cor_texto_anotacao = '#228B22'  # Verde para acima da meta
        else:
            y_pos_annotation = row['Total_Vendido'] + (row['Total_Vendido'] * 0.10)  # Ajustei a posição
            cor_texto_anotacao = '#FF4500'  #

        fig.add_annotation(
            x=row['Vendedor'],
            y=y_pos_annotation,
            text=row['Porcentagem_Texto'],
            showarrow=False,
            font=dict(size=32, color=cor_texto_anotacao, family="Arial, sans-serif"),
            align='center',
            hoverlabel=dict(bgcolor="#fff", font_size=22, font_family="Arial, sans-serif")
        )
        

    fig.update_layout(
        title='Performance de Vendas por Vendedor',
        xaxis_title='Vendedor',
        yaxis_title='Valor (R$)',
        yaxis=dict(tickformat=',.2f'),
        template='plotly_white',
        barmode='overlay', # sobrepor as barras
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
        width=300,
        xaxis=dict(tickfont=dict(size=28)),
        title_font=dict(size=40, family="Times New Roman"),
        margin=dict(l=50, r=20, b=100, t=50)
    )
    return fig


def renderizar_pagina_vendas(df):
    df_filtrado = aplicar_filtros(df)

    ano_atual = datetime.datetime.now().year
    mes_atual = datetime.datetime.now().month

    total_nf, total_qtd_produto, valor_total_item, total_custo_compra, total_lucro_venda_absoluto, ticket_medio_geral, porcentagem_lucro_venda = calcular_metricas(df_filtrado)


    def card_style(metric_name, value, color="#FFFFFF", bg_color="#262730"):
        return f"""
        <div style="
            padding: 15px;
            border-radius: 15px;
            background-color: {bg_color};
            color: {color};
            text-align: center;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
        ">
            <h4 style="margin: 0; font-size: 22px;">{metric_name}</h4>
            <h2 style="margin: 10px 0; font-size: 36px;">{value}</h2>
        </div>
        """

    col1, col2, col3, col4, col5, col6 = st.columns([0.3, 1, 1, 1.2, 1.2, 1.2]) # Ajustei as proporções e adicionei uma coluna

    with col1:
        st.image(CAMINHO_ARQUIVO_IMAGENS, width=150) # Reduzi um pouco a largura da imagem para caber mais colunas
    with col2:
        st.markdown(card_style("Total de Notas", f"{total_nf}"), unsafe_allow_html=True)
    with col3:
        st.markdown(card_style("Total de Produtos", f"{total_qtd_produto}"), unsafe_allow_html=True)
    with col4:
        st.markdown(card_style("Faturamento Total", formatar_moeda(valor_total_item)), unsafe_allow_html=True)
    with col5:
        st.markdown(card_style("Custo Total", formatar_moeda(total_custo_compra)), unsafe_allow_html=True) # Adicionei o custo total
    with col6:
        st.markdown(card_style("Margem Bruta (%)", f"{porcentagem_lucro_venda:.2f}%"), unsafe_allow_html=True) # Nova métrica da porcentagem


    df_ticket_medio = processar_dados_ticket_medio(df_filtrado)

    df_ranking = ranking_clientes(df_filtrado)
    df_ranking = df_ranking.reset_index(drop=True)
    df_ranking = df_ranking.iloc[::-1]
    
    fig_ranking = px.bar(
        df_ranking,
        x="Valor_Total_Item",
        y="Cliente",
        orientation="h",
        title="Top Clientes por Faturamento",
        labels={"Valor_Total_Item": "Faturamento (R$)", "Cliente": "Clientes"},
        text=df_ranking["Valor_Total_Item"],
        color="Valor_Total_Item",
        color_continuous_scale="Viridis"
    )

    fig_ranking.update_traces(
        textposition="inside",
        textfont=dict(size=28, color="black")
    )

    fig_ranking.update_layout(
        xaxis_showticklabels=True,
        height=1100,
        width=750,
        yaxis=dict(
            title=dict(font=dict(size=24)),
            tickfont=dict(size=16)
        ),
        xaxis=dict(
            tickfont=dict(size=16)
        ),
        title_font=dict(size=50, family="Times New Roman")

    )

    # Calcular performance dos vendedores
    df_performance_vendedores = calcular_performance_vendedores(df_filtrado)
    fig_performance = criar_grafico_performance_vendedores(df_performance_vendedores)

    graphs = [
        criar_grafico_vendas_diarias(df_filtrado, mes_atual, ano_atual),
        fig_performance,
        exibir_grafico_ticket_medio(df_ticket_medio),
        criar_grafico_barras(produtos_mais_vendidos(df_filtrado), 'Descricao_produto', 'Valor_Total_Item', 'Top Produtos Mais Vendidos', {'Descricao_produto': 'Produto', 'Valor_Total_Item': 'Valor Total de Venda'}),
        criar_grafico_barras_vendas_linha(df_filtrado),
        fig_ranking
        
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