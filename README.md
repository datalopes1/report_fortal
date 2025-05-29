# 🏡 Radar Imobiliário Mensal de Fortaleza/CE

## 📜Sumário
1. 📌 [Sobre o Projeto](#-sobre-o-projeto)
2. ⚙️ [Tecnologias Utilizadas](#️-tecnologias-utilizadas)
3. 🚀 [Como Executar](#-como-executar)
4. 📊 [Estrutura do Projeto](#-estrutura-do-projeto)
5. 🗒️ [Licença](#️-licença)
6. 📞 [Contato](#-contato)

## 📌 Sobre o Projeto
Com a ideia de dar um próximo passo no meu projeto de web scraping de dados imobiliários decidi criar um report mensal com dados colhidos de anúncios em diversos sites para entregar um paranorâma mensal do mercado imobiliário residencial da capital cearense.

### Próximo passos
- [x] Maio/2025 - Criação de um Data Warehouse.
- [ ] Junho/2025 - Orquestração com Airflow.
- [ ] Julho/2025 - Pipeline CI/CD Completo.

## ⚙️ Tecnologias Utilizadas
Este projeto foi desenvolvido utilizando:

- 🐍 Python 3.11.8+
- 📊 Streamlit (Interface)
- 🦆 DuckDB & dbt (Armazenamento e transformação dos dados)
- 🔢 Pandas & NumPy (Manipulação de Dados e Armazenamento)
- 🕸️ Scrapy (Web Scraping)
- 📈 Plotly (Visualização de Dados)

### Arquitetura da solução

![img](img/arq.png)

## 🚀 Como Executar
Acesse a aplicação web no [Streamlit Cloud](https://radarimob-fortal.streamlit.app/).

#### Execução
1️⃣ **Clone o repositório**
```bash
git clone https://github.com/datalopes1/report_fortal.git
cd report_fortal
```

2️⃣ **Crie e ative um ambiente virtual (recomendado)**
 ```bash
python -m venv .venv
source .venv/bin/activate  # Mac e Linux
.venv\Scripts\activate  # Windows
 ```

3️⃣ **Instale as dependências**
```bash
pip install -r requirements.txt
```

4️⃣ **Execute o projeto**
```bash
streamlit run src/dashboard/app.py
```
## 📊 Estrutura do Projeto
```plain_text
report_fortal/
│-- .streamlit/                 # Arquivos de configuração do Streamlit
|-- data/
|   └── processed/              # Dados processados
|   └── raw/                    # Arquivos brutos extraídos
|   └── database.duckdb         # Banco de Dados 
|-- dwh/                        # Modelos do Data Warehouse
|-- img/                        # Imagens utilizadas na documentação
|-- src/                
|   └── dashboard/              # Script do Streamlit
|   └── extract/                # Scripts de extração dos dados
|   └── load/                   # Scripts de ingestão dos dados
|-- LICENSE.md                  # Licença do projeto
|-- poetry.lock                 # Lock do Poetry
|-- pyproject.toml              # Dependências do projeto
|-- README.md                   
└── requirements.txt              

```

## 🗒️ Licença
Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE.md) para mais detalhes.

## 📞 Contato
- 📬 datalopes1@proton.me
- 🖱️ https://datalopes1.github.io/
- 📱 +55 88 99993-4237