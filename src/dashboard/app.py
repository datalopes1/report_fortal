import streamlit as st
import plotly.express as px
import pandas as pd
import duckdb

# === PAGE CONFIG ===
st.set_page_config(
    page_title="Report do Mercado Imobiliário de Fortaleza/CE",
    page_icon="🏗️",
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
        return pd.DataFrame()
    
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
             text_auto: bool = False,
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
        text_auto=text_auto,
        color=color,
        title=title,
        histnorm=histnorm,
        color_discrete_sequence=["#130a24", 
                                 "#3a3548", 
                                 "#666170", 
                                 "#95929a",
                                 "#c6c6c6", 
                                 "#d1a8a7", 
                                 "#d68889", 
                                 "#d7666c", 
                                 "#de425b"]
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)',
        xaxis_title=xlabel or x,
        yaxis_title=ylabel or ('Proporção (%)' if histnorm == 'percent' else 'Contagem'),
        bargap=0.1
    )
    
    return fig

def plot_pie(data: pd.DataFrame, 
             names: str, 
             values: str = None,
             title: str = ""):
    """
    Cria um gráfico de pizza utilizando Plotly Express
    Pode ser usado para contagem (sem valores) ou valores agregados.
    """
    fig = px.pie(
        data,
        names=names,
        values=values,
        title=title,
        hole=0.65,
        color_discrete_sequence=[
            "#130a24", "#3a3548", "#666170", "#95929a", "#c6c6c6",
            "#d1a8a7", "#d68889", "#d7666c", "#de425b"
        ]
    )
    
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)')
    
    return fig

# === DADOS ===
df = query_data("SELECT *, (preco/area) AS preco_m2 FROM main_gold.obt_imoveis")

if df.empty:
    st.error("Não foi possível carregar os dados. Verifique a conexão com o banco.")
    st.stop()


# === TÍTULO E TABS ===
st.title("🏡 Report Mensal do Mercado de Fortaleza/CE")
st.subheader("Atualizado em 29/05/2025")

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
        ser_selecionado = st.selectbox("Secretaria Executiva Regional", ['Todos'] + list(sers_unicos))

    # Filtro por Faixa de Preço
    preco_min, preco_max = int(df['preco'].min()), int(df['preco'].max())
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
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🏡 Total de Anúncios Analisados", 
            value=format_numbers(df_filtrado.shape[0])
        )
    with col2:
        st.metric(
            label="💸 Preço Médio", 
            value=format_currency(df_filtrado['preco'].mean())
        )
    with col3:
        st.metric(
            label="💸 Preço Mediano",
            value=format_currency(df_filtrado['preco'].median())
        )
    with col4:
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

    col5, col6 = st.columns(2)
    with col5:
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
    with col6:
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
    st.markdown("---")
    st.text("☕ Contribua com um cafézinho - PIX: datalopes1@gmail.com")
    st.markdown("Desenvolvido por [André Lopes](https://www.linkedin.com/in/datalopes1/), 2025.")


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
            - Apartamentos tiveram uma valorização de +4,14%
            - Com uma queda nos preços, imóveis em bairros nobres como Meireles
            e Aldeota estão mais acessíveis. 
            - Lagoa Redonda e Vicente Pinzon apontam certo potencial 
            para crescimento em investimentos a longo prazo.
            """
        )
        descritivas_df = pd.DataFrame({
            "Medida": ['Média', 'Desvio Padrão', 'Quartil 1',
                       'Quartil 2 (Mediana)', 'Quartil 3',
                       'Mínimo', 'Máximo'],
            "Resultado": ['R$ 888.210', 'R$ 1.117.880,12', 'R$ 375.000',
                          'R$ 595.000', 'R$ 948.000', 'R$ 68.000', 
                          'R$ 20.000.000']
        })
        st.markdown("##### 🔎 Estatísticas Descritivas dos Preços")
        st.dataframe(descritivas_df)
        st.markdown("---")


    intro = st.container()
    with intro:
        st.header("Introdução")
        st.markdown(
            """
            Com a ideia de dar um próximo passo no meu projeto de web scraping
            de dados imobiliários decidi criar um report mensal com dados 
            colhidos de anúncios em diversos sites para entregar um paranorâma 
            mensal do mercado imobiliário residencial da capital cearense. A 
            medida que sempre vou dar preferência nas análises é a mediana por conta
            da sua menor sucetibilidade a distorções causadas por dados extremos, 
            o que é esperado quando se trata de mercado imobiliário.

            **Origem dos Dados**:
            - Raspagem de dados públicos colhidas em anúncios de sites especializados.

            **Escopo**: Foram exploradas as relações entre localização, área, dentre 
            outras variáveis com o preço dos imóveis.

            **Faixas de Preço**: As faixas de preço dos imóveis foram definidas como:
            - 1: imóveis até 200mil reais.
            - 2: imóveis entre 200mil e 500mil reais.
            - 3: imóveis entre 500mil e 1mi de reais.
            - 4: imóveis entre 1mi e 5mi de reais.
            - 5: imóveis acima de 5mi de reais.

            #### Distribuição dos Imóveis por Tipo e Preço
            """
        )
        col7, col8 = st.columns(2)
        with col7:
            st.plotly_chart(plot_pie(df_filtrado, 'tipo',title='🏡 Distribuição por Tipo de Imóvel'))
        with col8:
            st.plotly_chart(plot_bar(df_filtrado, '🏢 Distribuição por Faixa de Preço', 'faixa_preco', xlabel='Faixa de Preço',histnorm='percent'))
        st.markdown("---")

        por_tipo = st.container()
        with por_tipo:
            st.header("Tipo de Imóvel")
            st.markdown(
                """
                **Apartamentos** são de longe o tipo mais comum de imóvel
                ofertado, o que é normal em grandes centros onde a demanda
                urbana é concetrada na verticalização, mas mesmo assim casas
                ainda têm representativdade são imóveis que podem atender famílias 
                que buscam mais espaço e privacidade, geralmente fora do centro 
                urbano ou em bairros com perfil mais residencial (especialmente
                em condomínios). Apartamentos são o tipo de imóvel que apresentou 
                maior valorização no mês de maio.

                As faixas de preço **2 e 3** são onde está concetrado o maior 
                volume de imóveis, sejam casas ou apartamentos. Para casas em
                condomínio (que possuem um maior valor), os imóveis aparecem 
                mais nas faixas **3 e 4**.
                """
            )
            variacao_precos_df = pd.DataFrame({
                "Tipo": ["Apartamento", "Casa", "Condomínio"],
                "Preço Mediano": ["R$ 600.000,00", "R$ 510.000,00", "R$ 715.000,00"],
                "Preço m² (Mediano)": ["R$ 7.322,00", "R$ 3.411,76", "R$ 4.640,00"],
                "Variação": ["+4,14%", "+3,42%", "-1,13%"]
            })
            st.markdown("##### 📊 Variação de Preços (vs. Mês Anterior)")
            st.dataframe(variacao_precos_df)

            
            faixa_tipo = df_filtrado.groupby(["tipo", "faixa_preco"]).agg(preco_medio = ('preco', 'count')).reset_index()
            st.plotly_chart(
                plot_bar(
                    faixa_tipo,
                    title='🏢 Distribuição por Faixa de Preço por Tipo',
                    x='tipo',
                    y='preco_medio',
                    color='faixa_preco',
                    xlabel='Tipo',
                    ylabel=' '
                )
            )
            st.markdown("---")

            por_local = st.container()
            with por_local:


                # Dados valorização e desvalorização
                valorizacao_df = pd.DataFrame({
                    "Bairro": ["Maraponga", "José de Alencar", "Mondubim"],
                    "Variação": ["+29,73%", "+14,98%", "+14,59%"]
                })
                desvalorizacao_df = pd.DataFrame({
                    "Bairro": ["Meireles", "Aldeota", "Passaré"],
                    "Variação": ["-12,64%", "-8,03%", "-7,19%"]
                })


                st.header("Localização do Imóvel")
                st.markdown(
                    """
                    Considerando o volume de dados coletados, vou considerar para as análises
                    em relação as localizações somente bairros com mais de 250 anúncios coletados. 
                    """
                )
                st.markdown("##### 📈 Bairros com maior valorização")
                st.dataframe(valorizacao_df)
                st.markdown("##### 📉 Bairros com maior desvalorização")
                st.dataframe(desvalorizacao_df)
                st.markdown(
                    """
                    Aqui vale a pena destcar para a além da valorização da Maraponga,
                    a queda nos preços de imóveis em regiões nobres como Meireles e
                    Aldeota, o que aponta um bom momento para buscar imóveis nessa áreas.
                    Mondubim e José de Alencar são dois bairros com grande extensão territorial
                    e valores mais acessíveis vale apena ficar de olho em ambos.
                    """
                )
                

                col9, col10 = st.columns(2)
                with col9:
                    local_rank = df.copy()
                    local_rank = local_rank.groupby(["localizacao"]).agg(preco_medio = ('preco', 'mean'), m2_mediano = ('preco_m2', 'median')).reset_index()
                    st.plotly_chart(
                        plot_bar(
                            local_rank.sort_values(by='m2_mediano', ascending=False).head(),
                            title='💰 Top 5 Bairros com Maior R$/m²',
                            x='localizacao',
                            y='m2_mediano',
                            xlabel='Localização',
                            ylabel='R$/m²'
                        )
                    )

                with col10:
                    valori = query_data(
                        """
                        SELECT 
                        localizacao,
                        secretaria_regional,
                        variacao_m2_pct
                        FROM main_gold.mart_localizacao
                        WHERE qtd_imoveis > 250 AND date_ref = '2025-05'
                        ORDER BY 3 DESC
                        LIMIT 5
                        """
                    )
                    st.plotly_chart(
                        plot_bar(
                            valori,
                            title='💰 Top 5 Bairros com Maior Valorização (Maio/2025)',
                            x='localizacao',
                            y='variacao_m2_pct',
                            xlabel='Localização',
                            ylabel='%'
                        )
                    )
                st.markdown(
                    """
                    ### Considerações sobre faixa de preço

                    - Em relação a imóveis na faixa mais acessível (até 200mil) 
                    os bairros com maior concentraçaõ nessa faixa são Ancuri,
                    Passaré e Pedras, os bairros dos imóveis nessa faixa estão 
                    concentrados em regiões mais populosas e distantes do Centro.

                    - Também presente na segunda faixa (entre 200mil e 500mil), 
                    Passaré tem grande quantidade imóveis, aqui Lagoa Redonda 
                    apresenta também um alto volume de imóveis, o que contrasta 
                    com a sua grande oferta também de imóveis na quinta faixa 
                    (acima de 5mi) o que pode apontar o bairro como uma boa 
                    opção para investimentos a longo prazo. 

                    - Nas faixas 3 (entre 500mil e 1mi) e 4 (entre 1mi e 5mi), 
                    existe uma predominancia dos bairros da SER 2, destacando
                    bairros como Engenheiro Luciano Cavalcante, Meireles e Aldeota.

                    - Na última faixa de preço (acima de 5mi) temos como destaque o
                    bairro de Lourdes com seu alto valor, e o bairro Vicente Pinzon,
                    que teve uma grande valorização e é mais acessível que outros 
                    bairros da SER 2. 
                    """
                )
                por_faixa = pd.DataFrame({
                    "Faixa": [1, 2, 3, 4, 5],
                    "Bairro": ["Pedras", "Lagoa Redonda", "Engenheiro Luciano Cavalcante", "Meireles", "de Lourdes"],
                    "Total de Imóveis": [76, 349, 299, 200, 24],
                    "Preço Mediano Geral": ["R$ 189.500,00", "R$ 400.000,00", "R$ 780.000,00", "R$ 970.000,00", "R$ 3.442.500,000"]
                })
                st.markdown("##### 📊 Imóveis por Faixa de Preço")
                st.dataframe(por_faixa)
                st.markdown("---")
                st.text("☕ Contribua com um cafézinho - PIX: datalopes1@gmail.com")
                st.markdown("Desenvolvido por [André Lopes](https://www.linkedin.com/in/datalopes1/), 2025.")