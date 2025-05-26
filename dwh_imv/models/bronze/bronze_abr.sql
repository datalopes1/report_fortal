{{ config(
    materialized='view',
	tags = ['bronze']
) }}

SELECT
    origem,
    date_ref,
    tipo , 
    localizacao, 
    area, 
    quartos, 
    banheiros, 
    vagas, 
    preco, 
    condo, 
    CURRENT_TIMESTAMP AS ingestion_timestamp
FROM {{ source ('imoveis_2025', 'abril') }}