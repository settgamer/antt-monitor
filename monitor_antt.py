import requests
from bs4 import BeautifulSoup

URL = "https://www.gov.br/antt/pt-br/search?origem=form&SearchableText=Tabelas%20de%20frete%20atualizadas%3A"

def buscar_noticias(url):
    print(f"🌐 Acessando busca: {url}")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erro ao acessar {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # A div que contém as notícias
    container = soup.find("ul", class_="searchResults noticias")
    if not container:
        print("⚠️ Container de notícias não encontrado.")
        return []

    noticias = []
    itens = container.find_all("li", class_="item-collective.nitf.content")
    for item in itens:
        titulo_tag = item.find("span", class_="titulo").find("a")
        if titulo_tag:
            titulo = titulo_tag.text.strip()
            link = "https://www.gov.br" + titulo_tag["href"]
            noticias.append((titulo, link))

    print(f"🔍 Notícias filtradas encontradas: {len(noticias)}")
    return noticias

if __name__ == "__main__":
    noticias = buscar_noticias(URL)
    for titulo, link in noticias:
        print(f"- {titulo}\n  {link}\n")
