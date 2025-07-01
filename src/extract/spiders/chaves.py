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

        imoveis = response.css('span.card-module__1awNxG__cardContent')

        for imovel in imoveis:
            raw_loc = imovel.css('address.style-module__PkTDxW__address p::text').getall()
            localizacao = raw_loc[1] if len(raw_loc) > 1 else None

            comodos = imovel.css('span.style-module__PkTDxW__list p::text').getall()
            area = comodos[1] if len(comodos) > 1 else None
            quartos = comodos[3] if len(comodos) > 3 else None
            vagas = comodos[5] if len(comodos) > 5 else None
            banheiros = comodos[7] if len(comodos) > 7 else None

            raw_condo = imovel.css('p.column.style-module__PkTDxW__price small::text').getall()
            condo = raw_condo[1] if len(raw_condo) > 1 else None

            preco = imovel.css('span.card-module__1awNxG__cardContent p b::text').get()

            yield {
                'preco': self.clean_prices(preco),
                'tipo': tipo,
                'localizacao': self.clean_local(localizacao),
                'area': area,
                'quartos': quartos,
                'banheiros': banheiros,
                'vagas': vagas,
                'condo': self.clean_prices(condo)
            }

        if page < 99:
            next_page = response.css('a[rel="next"]::attr(href)').get()
            if next_page:
                next_page_url = response.urljoin(next_page)
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse,
                    meta={'tipo': tipo, 'page': page + 1}
                )
