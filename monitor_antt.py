import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.gov.br"
URL_BUSCA = "https://www.gov.br/antt/pt-br/search?origem=form&SearchableText=Tabelas%20de%20frete%20atualizadas%3A%20OR%20ANTT%20reajusta%20tabela%20dos%20pisos%20m%C3%ADnimos%20de%20frete%20OR%20ANTT%20avanca%20na%20fiscalizacao%20do%20Piso%20Minimo%20de%20Frete"

TERMOS_FILTRAGEM = [
    "Tabelas de frete atualizadas",
    "ANTT reajusta tabela dos pisos mínimos de frete",
    "ANTT avança na fiscalização do Piso Mínimo de Frete"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def buscar_noticias_relevantes():
    print(f"🌐 Acessando busca: {URL_BUSCA}")
    resp = requests.get(URL_BUSCA, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    container = soup.select_one("div.column.col-md-9 ul.searchResults.noticias")
    if not container:
        print("⚠️ Container de notícias não encontrado.")
        return []

    noticias_relevantes = []

    for li in container.find_all("li", class_="item-collective.nitf.content"):
        a_tag = li.select_one("span.titulo > a")
        if not a_tag:
            continue
        titulo = a_tag.get_text(strip=True)
        href = a_tag.get("href")
        url_completa = BASE_URL + href if href.startswith("/") else href

        if any(termo.lower() in titulo.lower() for termo in TERMOS_FILTRAGEM):
            noticias_relevantes.append((titulo, url_completa))

    return noticias_relevantes

# Exemplo de uso:
if __name__ == "__main__":
    noticias = buscar_noticias_relevantes()
    if noticias:
        print(f"🔍 {len(noticias)} notícias relevantes encontradas:")
        for titulo, url in noticias:
            print(f"- {titulo}\n  {url}\n")
    else:
        print("⚠️ Nenhuma notícia relevante encontrada.")
