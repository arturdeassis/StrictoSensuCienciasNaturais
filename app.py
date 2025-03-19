"""
Dashboard interativo para análise do Stricto Sensu em Ciências Naturais
Autor: [Artur Neves de Assis - arturassis@unisinos.br]
Data: Março 2025
Descrição: Visualização de dados de matrículas em programas de pós-graduação
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração para melhor incorporação em iFrames
st.set_page_config(
    page_title="Panorama do Stricto Sensu",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS para remover elementos indesejados na incorporação
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Title
st.title("Panorama do Stricto Sensu em Ciências Naturais")

# Função para calcular o CAGR (Compound Annual Growth Rate)
def calcular_cagr(valores, anos):
    if len(valores) < 2:
        return 0
    primeiro_valor = valores.iloc[0]
    ultimo_valor = valores.iloc[-1]
    if primeiro_valor == 0 or pd.isna(primeiro_valor):
        return 0
    num_anos = anos.iloc[-1] - anos.iloc[0]
    if num_anos == 0:
        return 0
    return (ultimo_valor / primeiro_valor) ** (1 / num_anos) - 1

# Carregar os dados
@st.cache_data  # Cache data for better performance
def carregar_dados():
    df = pd.read_parquet('stricto_sensu_ciencias_naturais.parquet')
    
    # Garantir que a coluna Ano seja numérica
    df['Ano'] = pd.to_numeric(df['Ano'], errors='coerce')
    
    # Renomear colunas se necessário
    mapa_colunas = {
        'UF': 'Estado',
        'Área Avaliação': 'Área de Avaliação',
        'Área Conhecimento': 'Área de Conhecimento'
    }
    df.rename(columns=mapa_colunas, inplace=True)
    
    # Verificar se COREDE existe e convertê-lo para string
    if 'COREDE' not in df.columns:
        corede_cols = [col for col in df.columns if 'COREDE' in str(col)]
        if corede_cols:
            df['COREDE'] = df[corede_cols[0]].astype(str)
        else:
            df['COREDE'] = 'NA'  # Cria coluna padrão se não existir
    else:
        df['COREDE'] = df['COREDE'].fillna('NA').astype(str)
    
    # Substituir valores NaN por 0 nas colunas numéricas
    colunas_matriculados = [
        'Doutorado - Matriculado', 'Doutorado Profissional - Matriculado',
        'Mestrado - Matriculado', 'Mestrado Profissional - Matriculado'
    ]
    for coluna in colunas_matriculados:
        df[coluna] = df[coluna].fillna(0).astype(int)
    
    # Garantir que as colunas IES e Status Jurídico existam e estejam tratadas
    if 'IES' not in df.columns:
        # Verificar se há alguma coluna com nome parecido
        ies_cols = [col for col in df.columns if 'IES' in str(col) or 'Instituição' in str(col)]
        if ies_cols:
            df['IES'] = df[ies_cols[0]]
        else:
            df['IES'] = 'Não informado'  # Cria coluna padrão se não existir
    
    if 'Status Jurídico' not in df.columns:
        # Verificar se há alguma coluna com nome parecido
        status_cols = [col for col in df.columns if 'Status' in str(col) or 'Jurídico' in str(col) or 'Categoria' in str(col)]
        if status_cols:
            df['Status Jurídico'] = df[status_cols[0]]
        else:
            df['Status Jurídico'] = 'Não informado'  # Cria coluna padrão se não existir
    
    # Tratar valores nulos nas novas colunas
    df['IES'] = df['IES'].fillna('Não informado')
    df['Status Jurídico'] = df['Status Jurídico'].fillna('Não informado')
    
    return df

# Load data
df = carregar_dados()

# Sidebar filters
st.sidebar.header("Filtros")
dimensao = st.sidebar.selectbox("Dimensão de Análise", ['Programa', 'Área de Avaliação', 'Área de Conhecimento'])
metrica = st.sidebar.selectbox("Métrica", ['Doutorado - Matriculado', 'Doutorado Profissional - Matriculado', 'Mestrado - Matriculado', 'Mestrado Profissional - Matriculado', 'Total Matriculados'])

# Filtros organizados em abas para melhor organização
filter_tabs = st.sidebar.tabs(["Geografia", "Instituições"])

with filter_tabs[0]:  # Aba de filtros geográficos
    estados = st.multiselect("Estado", df['Estado'].unique())
    municipios = st.multiselect("Município", df['Município'].unique())
    coredes = st.multiselect("COREDE", df['COREDE'].unique())

with filter_tabs[1]:  # Aba de filtros institucionais
    ies_list = st.multiselect("IES", sorted(df['IES'].unique()))
    status_juridico = st.multiselect("Status Jurídico", sorted(df['Status Jurídico'].unique()))

# Filtro de período (fora das abas)
ano_range = st.sidebar.slider("Ano", int(df['Ano'].min()), int(df['Ano'].max()), (int(df['Ano'].min()), int(df['Ano'].max())))

# Apply filters
filtered_df = df.copy()
filtered_df = filtered_df[(filtered_df['Ano'] >= ano_range[0]) & (filtered_df['Ano'] <= ano_range[1])]
if estados:
    filtered_df = filtered_df[filtered_df['Estado'].isin(estados)]
if municipios:
    filtered_df = filtered_df[filtered_df['Município'].isin(municipios)]
if coredes:
    filtered_df = filtered_df[filtered_df['COREDE'].isin(coredes)]
if ies_list:
    filtered_df = filtered_df[filtered_df['IES'].isin(ies_list)]
if status_juridico:
    filtered_df = filtered_df[filtered_df['Status Jurídico'].isin(status_juridico)]

# Group data
if metrica == 'Total Matriculados':
    filtered_df['Total Matriculados'] = filtered_df[['Doutorado - Matriculado', 'Doutorado Profissional - Matriculado', 'Mestrado - Matriculado', 'Mestrado Profissional - Matriculado']].sum(axis=1)

grouped_df = filtered_df.groupby(['Ano', dimensao])[metrica].sum().reset_index()

# Plot
fig = px.line(grouped_df, x='Ano', y=metrica, color=dimensao, title=f"Evolução Temporal de {metrica} por {dimensao}")

# Ensure x-axis (years) are displayed as integers
fig.update_xaxes(tickmode='linear', tick0=ano_range[0], dtick=1)

# Increase x-axis width by adjusting margins
# Increase plot area by adjusting layout
fig.update_layout(
    width=2000,  # Set the width of the Plotly figure
    height=500,  # Set the height of the Plotly figure
    margin=dict(l=0, r=0, t=40, b=40),  # Adjust margins to give more space to the plot area
    xaxis=dict(
        title_font=dict(size=14),  # Increase font size of x-axis title
        tickfont=dict(size=12),    # Increase font size of x-axis ticks
        automargin=True            # Automatically adjust margins to fit labels
    ),
    yaxis=dict(
        title_font=dict(size=14),  # Increase font size of y-axis title
        tickfont=dict(size=12)     # Increase font size of y-axis ticks
    ),
    legend=dict(
        font=dict(size=10),       # Ajusta o tamanho da fonte na legenda
        itemsizing='constant'     # Mantém o tamanho dos itens da legenda constante
    )
)

# Increase plot width explicitly and disable container width
st.plotly_chart(fig, use_container_width=False)

# Display CAGR
if not grouped_df.empty:
    cagr = calcular_cagr(grouped_df[metrica], grouped_df['Ano'])
    st.write(f"**CAGR (Taxa Composta de Crescimento Anual):** {cagr:.2%}")

# Adicionar ranking de IES por matrículas com market-share
st.subheader("Ranking de IES por Matrículas")
if not filtered_df.empty:
    # Agrupar por IES para obter o total de matrículas por instituição
    ies_stats = filtered_df.groupby('IES')[metrica].sum().reset_index()
    
    # Calcular o total geral para determinar o market-share
    total_geral = ies_stats[metrica].sum()
    
    # Calcular o market-share para cada IES
    ies_stats['Market Share (%)'] = (ies_stats[metrica] / total_geral * 100).round(2)
    
    # Ordenar pelo número de matrículas (decrescente)
    ies_stats = ies_stats.sort_values(metrica, ascending=False)
    
    # Limitar a 15 principais instituições para melhor visualização
    top_ies = ies_stats.head(15).copy()
    
    # Criar rótulos personalizados com o market-share
    top_ies['IES_com_share'] = top_ies['IES'] + ' (' + top_ies['Market Share (%)'].astype(str) + '%)'
    
    # Gráfico de barras horizontais para IES
    fig_ies = px.bar(top_ies, 
                     x=metrica, 
                     y='IES_com_share', 
                     title=f"Top 15 IES por {metrica} (com Market Share)",
                     color='Market Share (%)',
                     color_continuous_scale='Viridis',
                     text='Market Share (%)')
    
    # Configurar o layout do gráfico
    fig_ies.update_layout(
        width=2000,  # Mantém a mesma largura do gráfico principal
        height=600,  # Um pouco maior para acomodar mais IES
        margin=dict(l=0, r=0, t=40, b=40),
        yaxis={'categoryorder':'total ascending'},  # Ordena do menor para o maior
        xaxis_title=metrica,
        yaxis_title="Instituição de Ensino Superior"
    )
    
    # Configurar o formato do texto nos rótulos das barras
    fig_ies.update_traces(
        texttemplate='%{text:.1f}%', 
        textposition='inside',
        insidetextanchor='middle'
    )
    
    # Exibir o gráfico
    st.plotly_chart(fig_ies, use_container_width=False)
    
    # Exibir tabela com dados completos (opcional)
    with st.expander("Ver tabela completa de IES"):
        # Adicionar ranking à tabela completa
        ies_stats['Ranking'] = range(1, len(ies_stats) + 1)
        ies_stats = ies_stats[['Ranking', 'IES', metrica, 'Market Share (%)']]
        st.dataframe(ies_stats, height=400, width=2000)
