import streamlit as st
import plotly.express as px
import pandas as pd
import duckdb
import utils

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


# === DADOS ===
df = query_data("SELECT *, (preco/area) AS preco_m2 FROM main_gold.obt_imoveis")

if df.empty:
    st.error("Não foi possível carregar os dados. Verifique a conexão com o banco.")
    st.stop()


# === TÍTULO E TABS ===
st.title("🏡 Report Mensal do Mercado de Fortaleza/CE")
st.subheader("Atualizado em 30/06/2025")

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
            value=utils.format_numbers(df_filtrado.shape[0])
        )
    with col2:
        st.metric(
            label="💸 Preço Médio", 
            value=utils.format_currency(df_filtrado['preco'].mean())
        )
    with col3:
        st.metric(
            label="💸 Preço Mediano",
            value=utils.format_currency(df_filtrado['preco'].median())
        )
    with col4:
        # Evolução de preço
        preco_evo = df_filtrado.groupby("date_ref").agg(
            preco_mediano = ('preco', 'median')
        ).reset_index()
        preco_evo['var'] = round(preco_evo['preco_mediano'].pct_change() * 100, 2)
        preco_evo['date_ref'] = preco_evo['date_ref'].replace('2025-04', 'Abril/2025')
        preco_evo['date_ref'] = preco_evo['date_ref'].replace('2025-05', 'Maio/2025')
        preco_evo['date_ref'] = preco_evo['date_ref'].replace('2025-06', 'Junho/2025')
        
        if len(preco_evo) > 1:
            variacao_pct = preco_evo['var'].iloc[-1]
            st.metric(label="📈 Variação de Preço (vs. Mês Anterior)", value=f"{variacao_pct:,.2f}%".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.metric(label="📈 Variação de Preço (vs. Mês Anterior)", value="Dados insuficientes")
    
    st.plotly_chart(
        utils.plot_bar(preco_evo, 
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
            utils.plot_bar(top_bairros, 
                     '🏅 Valor do Metro Quadrado', 
                     x='preco_m2', 
                     y='localizacao',
                     xlabel='Preço (R$/m²)',
                     ylabel='Bairro')
        )
    with col6:
        st.plotly_chart(
            utils.plot_bar(
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
        st.subheader("Relatório Mensal - Junho/2025")
        st.markdown("---")


    summary = st.container()
    with summary:
        st.header("Sumário Executivo")
        st.markdown(
            """
            **Propósito**: Análise do mercado imobiliário da cidade de 
            Fortaleza/CE no mês de Junho de 2025.

            **Insights-chave**:
            - Apartamentos tiveram uma valorização de +4,01%, casas em condomínio 
            tiveram uma alta desvalorização com queda de 15,00%.
            - Os bairros com maior valorização foram Papicu, Prefeito José Walter 
            e Aldeota.
            - Houve uma queda nos preços do Engenheiro Luciano Cavalcante, Guararapes,
            e Fátima o que aponta um bom momento para investir nestes bairros. 
            """
        )
        descritivas_df = pd.DataFrame({
            "Medida": ['Média', 'Desvio Padrão', 'Quartil 1',
                       'Quartil 2 (Mediana)', 'Quartil 3',
                       'Mínimo', 'Máximo'],
            "Resultado": [utils.format_currency(df['preco'].mean()), 
                          utils.format_currency(df['preco'].std()), 
                          utils.format_currency(df['preco'].quantile(0.25)),
                          utils.format_currency(df['preco'].median()), 
                          utils.format_currency(df['preco'].quantile(0.75)), 
                          utils.format_currency(df['preco'].min()), 
                          utils.format_currency(df['preco'].max())]
        })
        st.markdown("##### 🔎 Estatísticas Descritivas dos Preços")
        st.dataframe(descritivas_df)
        st.markdown("---")


    intro = st.container()
    with intro:
        st.header("Introdução")
        st.markdown(
            """
            Dando prosseguimento ao report mensal, vamos para o mês de junho, 
            muito especial para nós aqui no nordeste, é pratinho e mugunzá dia sim
            dia também 😋 

            **Origem dos Dados**:
            - Raspagem de dados públicos colhidos em anúncios de sites especializados.

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
            st.plotly_chart(utils.plot_pie(df_filtrado, 'tipo',title='🏡 Distribuição por Tipo de Imóvel'))
        with col8:
            st.plotly_chart(utils.plot_bar(df_filtrado, '🏢 Distribuição por Faixa de Preço', 'faixa_preco', xlabel='Faixa de Preço',histnorm='percent'))
        st.markdown("---")

        por_tipo = st.container()
        with por_tipo:
            st.header("Tipo de Imóvel")
            st.markdown(
                """
                **Apartamentos** continuam sendo o tipo de imóvel com maior 
                volume de anúncios. No mês de junho aconteceu uma queda na 
                ofeta de casas em condomínios. 

                As faixas de preço **2 e 3** são onde está concetrado o maior 
                volume de imóveis, sejam casas ou apartamentos. Para casas em
                condomínio (que possuem um maior valor), os imóveis aparecem 
                mais nas faixas **3 e 4**.
                """
            )

            vari = df_tipos[df_tipos['date_ref']=='2025-06']
            variacao_precos_df = pd.DataFrame({
                "Tipo": ["Apartamento", "Casa", "Condomínio"],
                "Preço Mediano": [utils.format_currency(df_tipos.query("tipo == 'Apartamento' and date_ref == '2025-06'")['preco_mediano'].squeeze()), 
                                  utils.format_currency(df_tipos.query("tipo == 'Casa' and date_ref == '2025-06'")['preco_mediano'].squeeze()), 
                                  utils.format_currency(df_tipos.query("tipo == 'Condomínio' and date_ref == '2025-06'")['preco_mediano'].squeeze())],
                "Preço m² (Mediano)": [utils.format_currency(df_tipos.query("tipo == 'Apartamento' and date_ref == '2025-06'")['preco_m2_mediano'].squeeze()), 
                                       utils.format_currency(df_tipos.query("tipo == 'Casa' and date_ref == '2025-06'")['preco_m2_mediano'].squeeze()), 
                                       utils.format_currency(df_tipos.query("tipo == 'Condomínio' and date_ref == '2025-06'")['preco_m2_mediano'].squeeze())],
                "Variação": [(f"{df_tipos.query("tipo == 'Apartamento' and date_ref == '2025-06'")['variacao_m2_pct'].squeeze():.2f}%"), 
                             (f"{df_tipos.query("tipo == 'Casa' and date_ref == '2025-06'")['variacao_m2_pct'].squeeze():.2f}%"), 
                             (f"{df_tipos.query("tipo == 'Condomínio' and date_ref == '2025-06'")['variacao_m2_pct'].squeeze():.2f}%")]
            })
            st.markdown("##### 📊 Variação de Preços (vs. Mês Anterior)")
            st.dataframe(variacao_precos_df)

            #variacao_m2_pct
            faixa_tipo = df_filtrado.groupby(["tipo", "faixa_preco"]).agg(preco_medio = ('preco', 'count')).reset_index()
            st.plotly_chart(
                utils.plot_bar(
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

                valori = query_data(
                        """
                        SELECT 
                        localizacao,
                        secretaria_regional,
                        variacao_m2_pct
                        FROM main_gold.mart_localizacao
                        WHERE qtd_imoveis > 58 AND date_ref = '2025-06'
                        ORDER BY 3 DESC
                        LIMIT 5
                        """
                    )
                desval = query_data(
                        """
                        SELECT 
                        localizacao,
                        secretaria_regional,
                        variacao_m2_pct
                        FROM main_gold.mart_localizacao
                        WHERE qtd_imoveis > 58 AND date_ref = '2025-06'
                        ORDER BY 3
                        LIMIT 5
                        """
                    )
                # Dados valorização e desvalorização
                valorizacao_df = pd.DataFrame({
                    "Bairro": [f"{valori['localizacao'][0]}", 
                               f"{valori['localizacao'][1]}", 
                               f"{valori['localizacao'][2]}",
                               f"{valori['localizacao'][3]}",
                               f"{valori['localizacao'][4]}"],
                    "Variação": [f"{valori['variacao_m2_pct'][0]:.2f}%", 
                                 f"{valori['variacao_m2_pct'][1]:.2f}%", 
                                 f"{valori['variacao_m2_pct'][2]:.2f}%",
                                 f"{valori['variacao_m2_pct'][3]:.2f}%",
                                 f"{valori['variacao_m2_pct'][4]:.2f}%"]
                })
                desvalorizacao_df = pd.DataFrame({
                    "Bairro": [f"{desval['localizacao'][0]}", 
                               f"{desval['localizacao'][1]}", 
                               f"{desval['localizacao'][2]}",
                               f"{desval['localizacao'][3]}",
                               f"{desval['localizacao'][4]}"],
                    "Variação": [f"{desval['variacao_m2_pct'][0]:.2f}%", 
                                 f"{desval['variacao_m2_pct'][1]:.2f}%", 
                                 f"{desval['variacao_m2_pct'][2]:.2f}%",
                                 f"{desval['variacao_m2_pct'][3]:.2f}%",
                                 f"{desval['variacao_m2_pct'][4]:.2f}%"]
                })


                st.header("Localização do Imóvel")
                st.markdown(
                    """
                    Considerando o volume de dados coletados e a mediana da 
                    quantidade de anúncios, vou considerar para as análises
                    em relação as localizações somente bairros com mais de 
                    58 anúncios coletados. 
                    """
                )
                st.markdown("##### 📈 Bairros com maior valorização")
                st.dataframe(valorizacao_df)
                st.markdown("##### 📉 Bairros com maior desvalorização")
                st.dataframe(desvalorizacao_df)
                st.markdown(
                    """
                    Houve uma boa valorização em relação ao mês de maio em
                    bairros nobres como Aldeota e Meireles, mas vale destacar
                    o aumento dos preços de oferta nos bairros Papicu e Prefeito
                    José Walter. O querido Zé Walter, é uma área residencial densa
                    e com muitas oportunidades para investidores que pensam em investir
                    em locação.
                    """
                )
                

                col9, col10 = st.columns(2)
                with col9:
                    local_rank = df.copy()
                    local_rank = local_rank.groupby(["localizacao"]).agg(preco_medio = ('preco', 'mean'), m2_mediano = ('preco_m2', 'median')).reset_index()
                    st.plotly_chart(
                        utils.plot_bar(
                            local_rank.sort_values(by='m2_mediano', ascending=False).head(),
                            title='💰 Top 5 Bairros com Maior R$/m²',
                            x='localizacao',
                            y='m2_mediano',
                            xlabel='Localização',
                            ylabel='R$/m²'
                        )
                    )

                with col10:
                    st.plotly_chart(
                        utils.plot_bar(
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
                    os bairros com maior concentração nessa faixa Pedras, Ancuri e 
                    Passaré. Vale destacar também o volume de imóveis no bairro
                    Siqueira.

                    - Na segunda faixa (entre 200mil e 500mil), Passaré tem uma
                    maior quantidade de ofertas seguido de Lagoa Redonda e Mondubim.
                    Aqui estão localizados 105 anúncios no José Walter, bairro com grande 
                    valorização em junho.

                    - Na faixa 3 (entre 500mil e 1mi) e 4 (entre 1mi e 5mi) continua com um
                    grande volume de ofertas nos bairros Engenheiro Luciano Cavalcante, Aldeota e Meireles.

                    - Na última faixa de preço (acima de 5mi) temos a única mudança em 
                    relação ao mês de maio que é o bairro Meireles onde foram encontradas
                    43 ofertas de imóveis nessa faixa. 
                    """
                )
                por_faixa = pd.DataFrame({
                    "Faixa": [1, 2, 3, 4, 5],
                    "Bairro": [df_localizacao.query("faixa_1.max() == faixa_1")['localizacao'].squeeze(), 
                               df_localizacao.query("faixa_2.max() == faixa_2")['localizacao'].squeeze(), 
                               df_localizacao.query("faixa_3.max() == faixa_3")['localizacao'].squeeze(), 
                               df_localizacao.query("faixa_4.max() == faixa_4")['localizacao'].squeeze(), 
                               df_localizacao.query("faixa_5.max() == faixa_5")['localizacao'].squeeze()],
                    "Total de Imóveis": [df_localizacao.query("faixa_1.max() == faixa_1")['faixa_1'].squeeze(), 
                                         df_localizacao.query("faixa_2.max() == faixa_2")['faixa_2'].squeeze(), 
                                         df_localizacao.query("faixa_3.max() == faixa_3")['faixa_3'].squeeze(), 
                                         df_localizacao.query("faixa_4.max() == faixa_4")['faixa_4'].squeeze(), 
                                         df_localizacao.query("faixa_5.max() == faixa_5")['faixa_5'].squeeze()],
                    "Preço Mediano Geral": [utils.format_currency(df_localizacao.query("faixa_1.max() == faixa_1")['preco_mediano'].squeeze()), 
                                            utils.format_currency(df_localizacao.query("faixa_2.max() == faixa_2")['preco_mediano'].squeeze()), 
                                            utils.format_currency(df_localizacao.query("faixa_3.max() == faixa_3")['preco_mediano'].squeeze()), 
                                            utils.format_currency(df_localizacao.query("faixa_4.max() == faixa_4")['preco_mediano'].squeeze()), 
                                            utils.format_currency(df_localizacao.query("faixa_5.max() == faixa_5")['preco_mediano'].squeeze())]
                })
                st.markdown("##### 📊 Imóveis por Faixa de Preço")
                st.dataframe(por_faixa)
                st.markdown("---")
                st.text("☕ Contribua com um cafézinho - PIX: datalopes1@gmail.com")
                st.markdown("Desenvolvido por [André Lopes](https://www.linkedin.com/in/datalopes1/), 2025.")