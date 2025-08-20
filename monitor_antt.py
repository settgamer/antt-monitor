import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

GOOGLE_SEARCH_URL = "https://www.google.com/search"

# Queries separadas (sem aspas e OR)
SEARCH_QUERIES = [
    "Tabelas de frete atualizadas ANTT",
    "ANTT reajusta tabela dos pisos mínimos de frete"
]

DATA_LIMITE = datetime.strptime("18/07/2025", "%d/%m/%Y")

TITULOS_FILTRO = [
    "Tabelas de frete atualizadas:",
    "ANTT reajusta tabela dos pisos mínimos de frete"
]

def enviar_email(titulo, link, data):
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print("❌ Variáveis de ambiente de e-mail não configuradas corretamente.")
        return

    corpo = f"⚠️ Nova notícia detectada:\n\nTítulo: {titulo}\nData: {data.strftime('%d/%m/%Y')}\nLink: {link}\n\nConfira no site da ANTT."
    msg = MIMEText(corpo)
    msg["Subject"] = f"Nova notícia ANTT: {titulo}"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    print("📤 Enviando e-mail de notificação...")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
        print("✅ E-mail enviado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

def buscar_noticias_google(query):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
    }
    params = {
        "q": query,
        "hl": "pt-BR",
        "gl": "br",
        "num": "10"
    }

    print(f"🌐 Pesquisando no Google: {query}")
    try:
        resp = requests.get(GOOGLE_SEARCH_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erro ao acessar Google: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    for g in soup.find_all('div', class_='tF2Cxc'):
        titulo_tag = g.find('h3')
        link_tag = g.find('a', href=True)
        snippet_tag = g.find('div', class_='IsZvec')

        if not titulo_tag or not link_tag:
            continue

        titulo = titulo_tag.get_text(strip=True)
        link = link_tag['href']
        snippet = snippet_tag.get_text(separator=' ', strip=True) if snippet_tag else ""

        data = extrair_data(snippet)

        resultados.append({
            "titulo": titulo,
            "link": link,
            "data": data,
            "snippet": snippet
        })

    return resultados

def extrair_data(texto):
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }

    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', texto)
    if match:
        try:
            return datetime.strptime(match.group(0), "%d/%m/%Y")
        except:
            pass

    match = re.search(r'(\d{1,2}) de (\w+) de (\d{4})', texto.lower())
    if match:
        dia = int(match.group(1))
        mes_str = match.group(2)
        ano = int(match.group(3))
        mes = meses.get(mes_str)
        if mes:
            try:
                return datetime(ano, mes, dia)
            except:
                pass

    return None

def main():
    todas_noticias = []
    for q in SEARCH_QUERIES:
        resultados = buscar_noticias_google(q)
        todas_noticias.extend(resultados)

    if not todas_noticias:
        print("⚠️ Nenhuma notícia encontrada na pesquisa Google.")
        return

    # Ordenar por data, ignorando None, colocando None no fim
    todas_noticias = sorted(
        todas_noticias, 
        key=lambda n: n['data'] or datetime.min, 
        reverse=True
    )

    ultima = todas_noticias[0]
    data_ultima = ultima['data']
    data_ultima_str = data_ultima.strftime('%d/%m/%Y') if data_ultima else "sem data"

    print(f"🕵️‍♂️ Última notícia detectada: {ultima['titulo']} | {data_ultima_str}")

    if (data_ultima and data_ultima > DATA_LIMITE and
        any(term.lower() in ultima['titulo'].lower() for term in TITULOS_FILTRO)):
        enviar_email(ultima['titulo'], ultima['link'], data_ultima)
    else:
        print(f"ℹ️ A última notícia não atende aos critérios para envio de e-mail.")

if __name__ == "__main__":
    main()
