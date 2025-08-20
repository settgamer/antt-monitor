import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import os

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

SAVE_FILE = "ultima_noticia.txt"

# URL base para busca gov.br ANTT, usando query com termos exatos (pode ajustar se quiser)
BUSCA_URL = "https://www.gov.br/antt/pt-br/search?origem=form&SearchableText="

# Frases para filtrar títulos que interessam
TERMS = [
    "Tabelas de frete atualizadas:",
    "ANTT reajusta tabela dos pisos mínimos de frete",
    "ANTT avança na fiscalização do Piso Mínimo de Frete"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def enviar_email(titulo, url):
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print("❌ Variáveis de ambiente de e-mail não configuradas corretamente.")
        return

    msg = MIMEText(f"⚠️ Nova notícia ANTT detectada:\n\n{titulo}\n\nConfira no site: {url}")
    msg["Subject"] = f"Nova notícia ANTT detectada: {titulo}"
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

def ler_ultima_noticia():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def salvar_ultima_noticia(titulo):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        f.write(titulo)
    print("💾 Última notícia salva com sucesso.")

def buscar_noticias():
    query = " OR ".join(TERMS)
    url_busca = BUSCA_URL + requests.utils.quote(query)
    print(f"🌐 Buscando notícias em: {url_busca}")

    try:
        resp = requests.get(url_busca, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erro ao acessar {url_busca}: {e}")
        return None, None

    soup = BeautifulSoup(resp.text, "html.parser")

    # No gov.br, notícias aparecem em <div class="results"> e cada notícia em <div class="result-item">
    resultados = soup.select("div.results div.result-item")

    for item in resultados:
        titulo_tag = item.select_one("a.result-title")
        if not titulo_tag:
            continue
        titulo = titulo_tag.get_text(strip=True)
        link = titulo_tag.get("href")

        # Filtrar só títulos que contenham algum termo da lista (case insensitive)
        if any(term.lower() in titulo.lower() for term in TERMS):
            print(f"🔍 Notícia filtrada: {titulo}")
            return titulo, link

    print("⚠️ Nenhuma notícia relevante encontrada.")
    return None, None

def main():
    ultima_noticia = ler_ultima_noticia()
    titulo, url = buscar_noticias()

    if titulo and titulo != ultima_noticia:
        print(f"✅ Nova notícia detectada: {titulo}")
        enviar_email(titulo, url)
        salvar_ultima_noticia(titulo)
    else:
        print("ℹ️ Nenhuma notícia nova detectada.")

if __name__ == "__main__":
    main()
