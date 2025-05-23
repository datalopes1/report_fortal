import scrapy


class ZapSpider(scrapy.Spider):
    name = "zap"
    allowed_domains = ["www.zapimoveis.com.br"]

    tipos = {
        "Casa": "casas",
        "Apartamento": "apartamentos",
        "Condomínio": "casas-de-condominio"
    }

    def start_requests(self):
        for tipo_nome, tipo_url in self.tipos.items():
            url = f"https://www.zapimoveis.com.br/venda/{tipo_url}/ce+fortaleza/"
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

        imoveis = response.css('div.flex.flex-col.content-stretch')

        for imovel in imoveis:
            comodos = imovel.css(
                'ul.flex.flex-row.text-1-75.text-neutral-110.text-nowrap.gap-3 li h3::text'
            ).getall()

            area = comodos[0].split(" ")[0] if len(comodos) > 0 else None
            quartos = comodos[1] if len(comodos) > 1 else None
            banheiros = comodos[2] if len(comodos) > 2 else None
            vagas = comodos[3] if len(comodos) > 3 else None

            precos = imovel.css('div.shrink.grow.text-nowrap.min-w-0 p::text').getall()
            preco = self.clean_prices(precos[0]) if len(precos) > 0 else None
            condo = precos[1] if len(precos) > 1 else None

            localizacao = imovel.css('h2[data-cy="rp-cardProperty-location-txt"]::text').getall()
            bairro_cidade = localizacao[-1].strip().split(",")[0] if localizacao else None

            yield {
                'tipo': tipo,
                'localizacao': bairro_cidade,
                'area': area,
                'quartos': quartos,
                'banheiros': banheiros,
                'vagas': vagas,
                'preco': preco,
                'condo': condo
            }

        if page < 500:
            next_page = f"{response.url.split('?')[0]}?pagina={page + 1}"
            yield scrapy.Request(
                url=next_page,
                callback=self.parse,
                meta={'tipo': tipo, 'page': page + 1}
            )
