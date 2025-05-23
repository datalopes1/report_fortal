import duckdb
import pandas as pd
import logging

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


def main():
    abr_path = "data/raw/abr-2025"
    mai_path = "data/raw/mai-2025"
    
    abr = [
        load_data(f"{abr_path}/chaves_casas.json", "Chaves na Mão", "2025-04"),
        load_data(f"{abr_path}/chaves_condominio.json", "Chaves na Mão", "2025-04"),
        load_data(f"{abr_path}/chaves.json", "Chaves na Mão", "2025-04"),
        load_data(f"{abr_path}/lopes.json", "Imobiliária Lopes", "2025-04")
    ]

    mai = [
        load_data(f"{mai_path}/chaves.json", "Chaves na Mão", "2025-05"),
        load_data(f"{mai_path}/vivareal.json", "Viva Real", "2025-05"),
        load_data(f"{mai_path}/zap.json", "ZAP Imóveis", "2025-05")
    ]

    df_abr = pd.concat(abr, ignore_index=True)
    df_mai = pd.concat(mai, ignore_index=True)

    conn = duckdb.connect("data/database.duckdb")
    logging.info("Conexão com banco de dados iniciada.")

    save_table(df_abr, "imoveis_2025","abril", conn)
    save_table(df_mai, "imoveis_2025","maio", conn)

    logging.info("Ingestão de dados concluída.")
    logging.info("Conexão com o banco de dados encerrada.")
    conn.close()

if __name__=="__main__":
    main()