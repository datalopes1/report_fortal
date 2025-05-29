{{ config(
    materialized='table',
	tags = ['gold']
) }}

WITH silver_base AS (
    SELECT * FROM {{ ref('silver_abr') }} 
    UNION ALL
    SELECT * FROM {{ ref('silver_mai') }}
), gold_features AS (
SELECT 
	id,
	date_ref,
	tipo,
	localizacao,
	CASE
		WHEN LOWER(localizacao) IN ('vila velha', 'barra do ceará', 'cristo redentor', 'pirambu', 'jardim guanabara', 'jardim iracema', 'floresta', 'álvaro weyne', 'carlito pamplona', 'jacarecanga') THEN '1'
		WHEN LOWER(localizacao) IN ('meireles', 'aldeota', 'joaquim távora', 'dionísio torres', 'dionisio torres','tauape', 'são joão do tauape', 'varjota', 'mucuripe', 'vicente pinzon', 'de lourdes', 'papicu', 'cais do porto') THEN '2'
		WHEN LOWER(localizacao) IN ('quintino cunha', 'antônio bezerra', 'olavo oliveira', 'padre andrade', 'presidente kennedy', 'ellery', 'vila ellery', 'são gerardo', 'parquelândia', 'amadeu furtado', 'rodolfo teófilo', 'parque araxá', 'farias brito', 'monte castelo') THEN '3'
		WHEN LOWER(localizacao) IN ('benfica', 'josé bonifácio', 'fátima', 'damas', 'jardim américa', 'bom futuro', 'parreão', 'vila união', 'aeroporto', 'itaoca', 'paraganba', 'vila peri', 'montese', 'parangaba') THEN '4'
		WHEN LOWER(localizacao) IN ('bonsucesso', 'granja portugal', 'bom jardim', 'siqueira', 'granja lisboa') THEN '5'
		WHEN LOWER(localizacao) IN ('alto da balança', 'aerolândia', 'jardim das oliveiras', 'cidade dos funcionários', 'parque manibura', 'parque iracema', 'cambeba', 'josé de alencar', 'messejana', 'curió', 'guajeru', 'guajerú', 'lagoa redonda', 'coaçu', 'são bento', 'paupina') THEN '6'
		WHEN LOWER(localizacao) IN ('sabiaguaba', 'lagoa sapiranga (coité)','sapiranga', 'coité', 'edson queiroz', 'manuel dias branco', 'manoel dias branco', 'praia do futuro i', 'praia do futuro ii', 'praia do futuro','engenheiro luciano cavalcante', 'salinas', 'guararapes', 'cocó', 'dunas','cidade 2000', 'patriolino ribeiro') THEN '7'
		WHEN LOWER(localizacao) IN ('serrinha', 'dias macêdo', 'dias macedo', 'boa vista', 'castelão', 'boa vista castelão', 'passaré', 'prefeito josé walter', 'planalto ayrton senna', 'parque dois irmãos', 'dendê', 'itaperi') THEN '8'
		WHEN LOWER(localizacao) IN ('cajazeiras', 'barroso', 'jangurussu', 'parque santa maria', 'ancuri', 'pedras', 'conjunto palmeiras') THEN '9'
		WHEN LOWER(localizacao) IN ('maraponga', 'jardim cearense', 'mondubim', 'aracapé', 'aracape', 'parque presidente vargas', 'parque santa rosa', 'conjunto esperança', 'novo mondubim', 'manoel sátiro', 'manuel sátiro', 'parque são josé', 'canindezinho') THEN '10'
		WHEN LOWER(localizacao) IN ('couto fernandes', 'bela vista', 'panamericano', 'demócrito rocha', 'democrito rocha', 'pici', 'jóquei clube', 'henrique jorge', 'joao xxiii', 'joão xxiii', 'dom lustosa', 'autran nunes', 'genibau', 'conjunto ceará i', 'conjunto ceará ii', 'conjunto ceará') THEN '11'
		WHEN LOWER(localizacao) IN ('centro', 'moura brasil', 'praia de iracema') THEN '12'
		ELSE 'Outro'
	END AS secretaria_regional,
	CASE 
		WHEN LOWER(localizacao) IN ('centro', 'moura brasil', 'praia de iracema', 'barra do ceará', 'cristo redentor', 'pirambu', 'meireles', 'mucuripe', 'cais do porto', 'vicente pinzon', 'praia do futuro', 'praia do futuro i', 'praia do futuro ii', 'sabiaguaba') THEN 'Sim'
		ELSE 'Não'
	END AS prox_orla,
	CASE 
		WHEN LOWER(localizacao) IN ('centro', 'moura brasil', 'praia de iracema', 'jacarecanga', 'farias brito', 'benfica', 'josé bonifácio', 'joaquim távora', 'joaquim tavora', 'aldeota', 'meireles') THEN 'Sim'
		ELSE 'Não'
	END AS prox_centro,
	CASE 
		WHEN preco <= 200000 THEN '1'
		WHEN preco BETWEEN 200001 AND 500000 THEN '2'
		WHEN preco BETWEEN 500001 AND 1000000 THEN '3'
		WHEN preco BETWEEN 1000001 AND 5000000 THEN '4'
		WHEN preco > 5000000 THEN '5'
	END AS faixa_preco,
	area,
	quartos,
	banheiros,
	vagas,
	preco,
	condo,
    ROW_NUMBER() OVER (PARTITION BY id ORDER BY preco DESC) AS row_num
FROM silver_base)
SELECT 
	id,
	date_ref,
	tipo,
	localizacao,
	secretaria_regional,
	prox_orla,
	prox_centro,
	faixa_preco,
	area,
	quartos,
	banheiros,
	vagas,
	preco,
	condo,
	CURRENT_TIMESTAMP AS ingestion_timestamp
FROM gold_features