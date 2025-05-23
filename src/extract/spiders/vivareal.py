import scrapy


class VivarealSpider(scrapy.Spider):
    name = "vivareal"
    allowed_domains = ["www.vivareal.com.br"]

    tipos = {
        "Apartamento": "apartamento_residencial",
        "Casa": "casa_residencial",
        "Condomínio": "condominio_residencial"
    }

    def start_requests(self):
        for tipo_nome, tipo_url in self.tipos.items():
            url = f"https://www.vivareal.com.br/venda/ceara/fortaleza/{tipo_url}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'tipo': tipo_nome, 'page': 1}
            )
    
    def clean_prices(self, price_str):
        if not price_str:
            return None
        return price_str.replace("R$", "").replace(".", "").strip()

    def parse(self, response):
        tipo = response.meta['tipo']
        page = response.meta['page']

        imoveis = response.css('li[data-cy="rp-property-cd"]')

        for imovel in imoveis:
            comodos = imovel.css('ul.flex.flex-row.text-1-75.text-neutral-110.text-nowrap.gap-3 li h3::text').getall()
            area = comodos[0].split(" ")[0] if len(comodos) > 0 else None
            quartos = comodos[1] if len(comodos) > 1 else None
            banheiros = comodos[2] if len(comodos) > 2 else None
            vagas = comodos[3] if len(comodos) > 3 else None

            localizacao_raw = imovel.css('h2[data-cy="rp-cardProperty-location-txt"]::text').getall()
            localizacao = localizacao_raw[-1].strip().split(",")[0] if localizacao_raw else None

            valores = imovel.css('div.shrink.grow.text-nowrap.min-w-0 p::text').getall()
            preco = self.clean_prices(valores[0] if len(valores) > 0 else None)
            condo = valores[1] if len(valores) > 1 else None

            yield {
                'tipo': tipo,
                'localizacao': localizacao,
                'area': area,
                'quartos': quartos,
                'banheiros': banheiros,
                'vagas': vagas,
                'preco': preco,
                'condo': condo
            }

        if page < 50:
            next_page_url = f"{response.url.split('?')[0]}?pagina={page + 1}"
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse,
                meta={'tipo': tipo, 'page': page + 1}
            )
