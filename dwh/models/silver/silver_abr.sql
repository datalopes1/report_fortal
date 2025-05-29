{{ config(
    materialized='incremental',
	tags = ['silver']
) }}

WITH initial AS (
SELECT 
	origem
	, date_ref
	, tipo
	, COALESCE(STR_SPLIT(localizacao, ',')[1], NULL) AS localizacao
	, COALESCE(TRY_CAST(area AS INTEGER), 0) AS area
	, COALESCE(TRY_CAST(quartos AS INTEGER), 0) AS quartos
	, COALESCE(TRY_CAST(banheiros AS INTEGER), 0) AS banheiros
	, COALESCE(TRY_CAST(vagas AS INTEGER), 0) AS vagas
	, REPLACE(REPLACE(preco, 'R$', ''), '.', '') AS preco
	, REPLACE(REPLACE(condo, 'R$', ''), '.', '') AS condo 
FROM {{ ref('bronze_abr') }}),
clean AS (
SELECT
	SHA256(origem || tipo || localizacao || area || quartos || banheiros || vagas || preco) AS id
	, origem 
	, date_ref
	, tipo
	, localizacao
	, area
	, quartos
	, banheiros
	, vagas
	, COALESCE(TRY_CAST(preco AS REAL), 0) AS preco
	, COALESCE(TRY_CAST(condo AS REAL), 0) AS condo
FROM initial),
deduplication AS (
SELECT
	*
	, ROW_NUMBER() OVER (PARTITION BY id ORDER BY preco DESC) AS row_num
FROM clean)
SELECT 
	id
	, origem
	, date_ref
	, tipo
	, localizacao
	, area
	, quartos
	, banheiros
	, vagas
	, preco
	, condo
	, CURRENT_TIMESTAMP AS ingestion_timestamp
FROM deduplication
WHERE 
	row_num = 1
	AND preco > 65000
	AND quartos BETWEEN 1 AND 10
	AND banheiros BETWEEN 1 AND 10
	AND vagas BETWEEN 1 AND 10
	AND area BETWEEN 30 AND 1000