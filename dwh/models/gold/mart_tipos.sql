{{ config(
    materialized='table',
	tags = ['gold']
) }}

WITH stats AS (
    SELECT 
        tipo,
        date_ref,
        COUNT(*) AS qtd_imoveis,
        COUNT(CASE WHEN preco <= 200000 THEN 1 END) AS ate_200k,
        COUNT(CASE WHEN preco BETWEEN 200001 AND 500000 THEN 1 END) AS entre_200k_500k,
        COUNT(CASE WHEN preco BETWEEN 500001 AND 1000000 THEN 1 END) AS entre_500k_1m,
        COUNT(CASE WHEN preco BETWEEN 1000001 AND 5000000 THEN 1 END) AS entre_1m_5m,
        COUNT(CASE WHEN preco > 5000001 THEN 1 END) AS acima_5m,
		ROUND(AVG(preco), 2) AS preco_medio,
        ROUND(MEDIAN(preco), 2) AS preco_mediano,
        ROUND(AVG(preco/area), 2) AS preco_m2_medio,
        ROUND(MEDIAN(preco/area), 2) AS preco_m2_mediano
    FROM {{ ref('obt_imoveis') }}
    GROUP BY tipo, date_ref
    HAVING qtd_imoveis > 20
), var AS (
SELECT 
	*,
	LAG(preco_m2_mediano, 1, NULL) OVER (PARTITION BY tipo ORDER BY date_ref) AS mes_anterior_m2,
FROM stats)
SELECT
	date_ref,
	tipo,
	qtd_imoveis,
	ate_200k,
	entre_200k_500k,
	entre_500k_1m,
	entre_1m_5m,
	acima_5m,
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