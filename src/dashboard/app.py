import streamlit as st
import plotly.express as px
import pandas as pd
import duckdb

# === PAGE CONFIG ===
st.set_page_config(
    page_title="Report do Mercado Imobiliário de Fortaleza/CE",
    page_icon="🏡",
    layout="wide"
)

# === FUNÇÕES ===
@st.cache_data
def query_data(query: str):
    """
    Carrega dados resultado de um query no diretamente no banco de dados.
    """
    try:
        conn = duckdb.connect("data/database.duckdb")
        result = conn.execute(query).fetchdf()
        conn.close()
        return result
    except Exception as e:
        st.error(f"Erro ao consultas dados: {e}")
        return pd.DataFrame
    
def format_currency(value):
    """
    Formata valores para o padrão brasilero.
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_numbers(value):
    """
    Formata números para o padrão brasileiro.
    """
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def plot_bar(data: pd.DataFrame, 
             title: str, 
             x: str, 
             y: str = None,
             color: str = None, 
             xlabel: str = None, 
             ylabel: str = None, 
             histnorm: str = None):
    """
    Cria um gráfico de barras utilizando Plotly Express
    Funciona tanto para contagem quanto para valores específicos
    """
    fig = px.histogram(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        histnorm=histnorm,
        color_discrete_sequence=["#0065f8", 
                                 "#7285f7", 
                                 "#a3a7f6", 
                                 "#cccbf4",
                                 "#f1f1f1", 
                                 "#f1c6c6", 
                                 "#ec9c9d", 
                                 "#e27076", 
                                 "#d43d51"]
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)',
        xaxis_title=xlabel or x,
        yaxis_title=ylabel or ('Proporção (%)' if histnorm == 'percent' else 'Contagem'),
        bargap=0.1
    )
    
    return fig

# === DADOS ===
df = query_data("SELECT * FROM main_gold.obt_imoveis")


# === TÍTULO E TABS ===
st.title("🏡 Report Mensal do Mercado de Fortaleza/CE")
st.subheader("Atualizado em 27/05/2025")

tab_overview, tab_report = st.tabs(["📊 Dashboard", "📒 Report"])

# === SIDEBAR / FILTROS ===
with st.sidebar:
    st.header("Filtros")

    # Filtro por Tipo de Imóvel
    tipos_unicos = df['tipo'].unique()
    tipo_selecionado = st.selectbox("Tipo de Imóvel", ['Todos'] + list(tipos_unicos))

    # Filtro por Bairro (Localização)
    bairros_unicos = df['localizacao'].unique()
    bairros_selecionados = st.multiselect("Bairro", bairros_unicos)

    # Filtro por SER (se presente nos seus dados)
    if 'secretaria_regional' in df.columns:
        sers_unicos = df['secretaria_regional'].unique()
        sers_unicos = sorted(sers_unicos)
        ser_selecionado = st.selectbox("Secretaria Regional Executiva", ['Todos'] + list(sers_unicos))

    # Filtro por Faixa de Preço
    preco_min, preco_max = 80000, int(df['preco'].max())
    preco_range = st.slider("Faixa de Preço (R$)", preco_min, preco_max, (preco_min, preco_max))


# === APLICAÇÃO DOS FILTROS ===
df_filtrado = df.copy()

if tipo_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['tipo'] == tipo_selecionado]

if bairros_selecionados:
    df_filtrado = df_filtrado[df_filtrado['localizacao'].isin(bairros_selecionados)]

preco_min_selecionado, preco_max_selecionado = preco_range
df_filtrado = df_filtrado[(df_filtrado['preco'] >= preco_min_selecionado) & (df_filtrado['preco'] <= preco_max_selecionado)]

if 'secretaria_regional' in df.columns and ser_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['secretaria_regional'] == ser_selecionado]


# === TAB OVERVIEW ===
with tab_overview:

    # KPIs
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="🏡 Total de Anúncios Analisados", 
            value=format_numbers(df_filtrado.shape[0])
        )
    with col2:
        st.metric(
            label="💸 Preço Mediano", 
            value=format_currency(df_filtrado['preco'].median())
        )
    with col3:
        # Evolução de preço
        preco_evo = df_filtrado.groupby("date_ref").agg(
            preco_mediano = ('preco', 'median')
        ).reset_index()
        preco_evo['var'] = round(preco_evo['preco_mediano'].pct_change() * 100, 2)
        preco_evo['date_ref'] = preco_evo['date_ref'].replace('2025-04', 'Abril/2025')
        preco_evo['date_ref'] = preco_evo['date_ref'].replace('2025-05', 'Maio/2025')
        
        if len(preco_evo) > 1:
            variacao_pct = preco_evo['var'].iloc[-1]
            st.metric(label="📈 Variação de Preço (vs. Mês Anterior)", value=f"{variacao_pct:,.2f}%".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.metric(label="📈 Variação de Preço (vs. Mês Anterior)", value="Dados insuficientes")
    
    st.plotly_chart(
        plot_bar(preco_evo, 
                 '📊 Tendêcia de Preços', 
                 'date_ref', 
                 y = 'preco_mediano', 
                 xlabel="Data Referência",
                 ylabel="Preço Mediano (R$)")
    )

    col4, col5 = st.columns(2)
    with col4:
        top_bairros = df_filtrado.groupby("localizacao").agg(preco_m2 = ('preco_m2', 'median')).sort_values(by='preco_m2', ascending=False).reset_index()
        top_bairros = top_bairros.head()
        st.plotly_chart(
            plot_bar(top_bairros, 
                     '🏅 Valor do Metro Quadrado', 
                     x='preco_m2', 
                     y='localizacao',
                     xlabel='Preço (R$/m²)',
                     ylabel='Bairro')
        )
    with col5:
        st.plotly_chart(
            plot_bar(
                df_filtrado[df_filtrado['preco'] <= 1_000_000],
                '💰 Distribuição dos Preços (até 1mi)',
                x='preco',
                color='tipo',
                histnorm='percent',
                xlabel='Preço (R$)'
            )
        )


# === DADOS REPORT ===
df_tipos = query_data("SELECT * FROM main_gold.mart_tipos")
df_localizacao = query_data("SELECT * FROM main_gold.mart_localizacao")


# === TAB REPORT ===
with tab_report:
    header = st.container()
    with header:
        st.header("📝 Relatório de Análise")
        st.subheader("Relatório Mensal - Maio/2025")
        st.markdown("---")

    summary = st.container()
    with summary:
        st.header("Sumário Executivo")
        st.markdown(
            """
            **Propósito**: Análise do mercado imobiliário da cidade de 
            Fortaleza/CE no mês de Maio de 2025.

            **Insights-chave**:
            - A regional 2 
            - O fff
            - Dizz
            """
        )
        st.markdown("---")
    intro = st.container()
    with intro:
        st.header("Introdução")
        st.markdown(
            """
            Com a ideia de dar um próximo passo no meu projeto de web scraping
            de dados imobiliários decidi criar um report mensal com dados 
            colhidos de anúncios em diversos sites para entregar um paranorâma 
            mensal do mercado imobiliário residencial da capital cearense.

            **Origem dos Dados**:
            - Raspagem de dados públicos colhidas em anúncios de sites especializados.

            **Escopo**: Foram exploradas as realões entre localização, área, entre 
            outras variáveis com o preço dos imóveis.
            """
        )
        st.markdown("---")