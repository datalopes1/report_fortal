{{ config(
    materialized='table',
	tags = ['gold']
) }}


WITH stats AS (
    SELECT 
        localizacao,
		secretaria_regional,
        date_ref,
        COUNT(*) AS qtd_imoveis,
        COUNT(CASE WHEN preco <= 200000 THEN 1 END) AS faixa_1,
        COUNT(CASE WHEN preco BETWEEN 200001 AND 500000 THEN 1 END) AS faixa_2,
        COUNT(CASE WHEN preco BETWEEN 500001 AND 1000000 THEN 1 END) AS faixa_3,
        COUNT(CASE WHEN preco BETWEEN 1000001 AND 5000000 THEN 1 END) AS faixa_4,
        COUNT(CASE WHEN preco > 5000001 THEN 1 END) AS faixa_5,
		ROUND(AVG(preco), 2) AS preco_medio,
        ROUND(MEDIAN(preco), 2) AS preco_mediano,
        ROUND(AVG(preco/area), 2) AS preco_m2_medio,
        ROUND(MEDIAN(preco/area), 2) AS preco_m2_mediano
    FROM {{ ref('obt_imoveis') }}
    GROUP BY ALL
    HAVING qtd_imoveis > 20
), var AS (
SELECT 
	*,
	LAG(preco_m2_mediano, 1, NULL) OVER (PARTITION BY localizacao ORDER BY date_ref) AS mes_anterior_m2
FROM stats)
SELECT
	date_ref,
	localizacao,
	secretaria_regional,
	qtd_imoveis,
	faixa_1,
	faixa_2,
	faixa_3,
	faixa_4,
	faixa_5,
	preco_medio,
	preco_m2_medio,
	preco_mediano,
	preco_m2_mediano,
	CASE 
		WHEN mes_anterior_m2 IS NOT NULL THEN ROUND((((preco_m2_mediano - mes_anterior_m2 ) / mes_anterior_m2) * 100), 2)
		ELSE 0
	END AS variacao_m2_pct,
    CURRENT_TIMESTAMP AS ingestion_timestamp
FROM var
