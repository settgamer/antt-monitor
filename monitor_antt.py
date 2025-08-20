import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os

# Configs de e-mail (vindas dos Secrets do GitHub)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

GOOGLE_SEARCH_URL = "https://www.google.com/search"
SEARCH_QUERY = '"Tabelas de frete atualizadas: ANTT" OR "ANTT reajusta tabela dos pisos mínimos de frete"'

# Data limite para nova notícia
DATA_LIMITE = datetime.strptime("18/07/2025", "%d/%m/%Y")

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

def buscar_noticias_google():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36"
    }
    params = {
        "q": SEARCH_QUERY,
        "hl": "pt-BR",
        "gl": "br",
        "num": "10"  # limitar a 10 resultados
    }

    print(f"🌐 Pesquisando no Google: {SEARCH_QUERY}")
    try:
        resp = requests.get(GOOGLE_SEARCH_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erro ao acessar Google: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    resultados = []

    # Resultados estão em divs com class 'tF2Cxc'
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

    # Exemplo dd/mm/yyyy
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', texto)
    if match:
        try:
            return datetime.strptime(match.group(0), "%d/%m/%Y")
        except:
            pass

    # Exemplo dd de mês de yyyy
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
    noticias = buscar_noticias_google()
    if not noticias:
        print("⚠️ Nenhuma notícia encontrada na pesquisa Google.")
        return

    noticias_recentes = [n for n in noticias if n["data"] and n["data"] >= DATA_LIMITE]

    if not noticias_recentes:
        print(f"ℹ️ Nenhuma notícia nova encontrada depois de {DATA_LIMITE.strftime('%d/%m/%Y')}.")
        return

    for noticia in noticias_recentes:
        print(f"✅ Nova notícia detectada: {noticia['titulo']} ({noticia['data'].strftime('%d/%m/%Y')})")
        enviar_email(noticia['titulo'], noticia['link'], noticia['data'])

if __name__ == "__main__":
    main()
