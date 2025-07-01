import duckdb
import pandas as pd
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def load_data(file_path: str, origem: str, date_ref: str):
    """
    Carrega arquivos .JSON em um pd.DataFrame

    Args:
        - file_path (str): Caminho do arquivo .JSON
        - origem (str): Site onde os dados foram raspados 
        - date_ref (str): Data de referência da raspagem ('YYYY-MM')
    """
    try:
        df = pd.read_json(file_path)
        df['origem'] = origem
        df['date_ref'] = date_ref
        logging.info(f"Carregamento do arquivo '{file_path}' concluído.")
        return df
    except Exception as e:
        logging.error(f"Erro ao carregar '{file_path}': {e}", exc_info=True)
        raise 

def save_table(df: pd.DataFrame, 
               schema_name: str, 
               table_name: str, 
               conn: duckdb.DuckDBPyConnection):
    """
    Salva pd.DataFrames em um banco de dados DuckDB

    Args:
        - df (pd.DataFrame): DataFrame com os dados que devem ser ingeridos.
        - schema_name (str): Schema onde a tabela será salva
        - table_name (str): Nome da tabela onde os dados serão ingeridos
        - conn (duckdb.DuckDBPyConnection): Conexão com banco de dados DuckDB
    """
    try:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        conn.execute(f"DROP TABLE IF EXISTS {schema_name}.{table_name}")

        conn.register("tmp_df", df)
        conn.execute(f"CREATE TABLE {schema_name}.{table_name} AS SELECT * FROM tmp_df")

        logging.info(f"Tabela {schema_name}.{table_name} salva no banco de dados.")
        logging.info(f"{len(df)} linhas inseridas.")
    except Exception as e:
        logging.error(f"Erro ao salvar {table_name}: {e}", exc_info=True)
        raise 


def get_origin(file_name: str, name_map: dict):
    """
    Identifica a origem dos dados extraídos pelo nome do arquivo

    Args:
        - file_name (str): Nome do arquivo 
        - name_map (dict): Dicionário com os nomes
    """
    for chave, origem in name_map.items():
        if chave in file_name.lower():
            return origem
    return "Origem Desconhecida"


def main():
    file_path = input("Insira o caminho da pasta com os arquivos.json: ").strip()
    date_ref = input("Insira a data de referência da extração no formato YYYY-MM: ").strip()

    origens = {
        "chaves": "Chaves na Mão",
        "vivareal": "Viva Real",
        "zap": "ZAP Imóveis"
    }

    files = [
        os.path.join(file_path, file)
        for file in os.listdir(file_path)
        if file.endswith(".json")
    ]

    dataframes = []
    for file in files:
        file_name = os.path.basename(file)
        origem = get_origin(file_name, origens)

        try:
            df = load_data(file, origem, date_ref)
            dataframes.append(df)
        except Exception:
            raise

    df_final = pd.concat(dataframes, ignore_index=True)

    conn = duckdb.connect("data/database.duckdb")
    logging.info("Conexão com banco de dados iniciada.")

    table_name = os.path.basename(file_path).split("-")[0]
    save_table(df_final, "imoveis_2025", table_name, conn)

    logging.info("Ingestão de dados concluída.")
    logging.info("Conexão com o banco de dados encerrada.")
    conn.close()

if __name__=="__main__":
    main()