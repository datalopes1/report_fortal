import scrapy


class ChavesSpider(scrapy.Spider):
    name = "chaves"
    allowed_domains = ["www.chavesnamao.com.br"]

    tipos = {
        "Casa": "casas-a-venda",
        "Apartamento": "apartamentos-a-venda",
        "Condomínio": "casas-em-condominio-a-venda"
    }

    def start_requests(self):
        for tipo_nome, tipo_url in self.tipos.items():
            url = f"https://www.chavesnamao.com.br/{tipo_url}/ce-fortaleza/"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'tipo': tipo_nome, 'page': 1}
            )

    def clean_prices(self, price_str):
        if not price_str:
            return None
        return price_str.replace("R$", "").replace(".", "").strip()

    def clean_local(self, local_str):
        if not local_str:
            return None
        return local_str.split(",")[0]

    def parse(self, response):
        tipo = response.meta['tipo']
        page = response.meta['page']

        imoveis = response.css('span.card-module__cvK-Xa__cardContent')

        for imovel in imoveis:
            raw_area = imovel.css('p.styles-module__aBT18q__body2.undefined::text').getall()
            condos = imovel.css('span.card-module__cvK-Xa__cardContent p small::text').getall()

            yield {
                'preco': self.clean_prices(imovel.css('span.card-module__cvK-Xa__cardContent p b::text').get()),
                'tipo': tipo,
                'localizacao': self.clean_local(imovel.css('address p:nth-of-type(2)::text').get()),
                'area': raw_area[1] if len(raw_area) > 1 else None,
                'quartos': imovel.css('span.style-module__Yo5w-q__list p:nth-of-type(2)::text').get(),
                'banheiros': imovel.css('span.style-module__Yo5w-q__list p:nth-of-type(4)::text').get(),
                'vagas': imovel.css('span.style-module__Yo5w-q__list p:nth-of-type(3)::text').get(),
                'condo': self.clean_prices(condos[1]) if len(condos) > 1 else None
            }

        if page < 100:
            next_page = response.css(
                'span.row.w100.style-module__yjYI8a__nextlink a::attr(href)'
            ).get()
            if next_page:
                next_page_url = response.urljoin(next_page)
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse,
                    meta={'tipo': tipo, 'page': page + 1}
                )
