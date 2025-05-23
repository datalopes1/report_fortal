import scrapy


class OlxSpider(scrapy.Spider):
    name = "olx"
    allowed_domains = ["www.olx.com.br"]
    start_urls = ["https://www.olx.com.br/imoveis/venda/estado-ce/fortaleza"]
    page_count = 1
    max_page = 100

    def clean_prices(self, price_str):
        if not price_str:
            return None
        return price_str.replace("R$", "").replace(".", "").strip() 

    def clean_condo(self, price_str):
        if not price_str:
            return None
        return price_str.replace("Condomínio R$", "").replace(".", "").strip()

    def parse(self, response):
        imoveis = response.css('div.olx-adcard__content')

        for imovel in imoveis:
            tipo = imovel.css('h2.olx-text.olx-text--body-large.olx-text--block.olx-text--semibold.olx-adcard__title::text').get()
            raw_loc = imovel.css('div.olx-adcard__location-date p::text').getall()
            localizacao = raw_loc[1] if len(raw_loc) > 1 else None

            comodos = comodos = [i.strip() for i in imovel.css('div.olx-adcard__details div::text').getall() if i.strip()]
            quartos = comodos[0] if len(comodos) > 0 else None
            area = comodos[1] if len(comodos) > 1 else None
            vagas = comodos[2] if len(comodos) > 2 else None
            banheiros = comodos[3] if len(comodos) > 3 else None

            raw_condo = imovel.css('div.olx-adcard__price-info::text').getall()
            condo = raw_condo[1] if len(raw_condo) > 1 else None
            preco = imovel.css('h3.olx-text.olx-text--body-large.olx-text--block.olx-text--semibold.olx-adcard__price::text').get()

            yield {
                'tipo': tipo,
                'localizacao': localizacao,
                'area': area.replace("m²", ""),
                'quartos': quartos,
                'banheiros': banheiros,
                'vagas': vagas,
                'preco': self.clean_prices(preco),
                'condo': self.clean_condo(condo)
            }

        if self.page_count < self.max_page:
            self.page_count += 1
            next_page = (
                f"https://www.olx.com.br/imoveis/venda/estado-ce/fortaleza/?o={self.page_count}"
            )
            yield scrapy.Request(url=next_page, callback=self.parse)