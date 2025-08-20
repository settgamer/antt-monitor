import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.gov.br"
URL_BUSCA = "https://www.gov.br/antt/pt-br/search?origem=form&SearchableText=Tabelas%20de%20frete%20atualizadas%3A"

TERMO_FILTRAGEM = "Tabelas de frete atualizadas:"

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

        if TERMO_FILTRAGEM.lower() in titulo.lower():
            noticias_relevantes.append((titulo, url_completa))

    return noticias_relevantes

# Teste rápido
if __name__ == "__main__":
    noticias = buscar_noticias_relevantes()
    if noticias:
        print(f"🔍 {len(noticias)} notícias relevantes encontradas:")
        for titulo, url in noticias:
            print(f"- {titulo}\n  {url}\n")
    else:
        print("⚠️ Nenhuma notícia relevante encontrada.")
