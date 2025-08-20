import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import os

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

URL_NOVIDADES = "https://www.gov.br/antt/pt-br/assuntos/ultimas-noticias"

SAVE_FILE = "ultimo_titulo.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

PALAVRAS_CHAVE = ["antt", "resolução", "frete", "piso mínimo", "reajusta", "reajuste"]

def enviar_email(titulo, url):
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print("❌ Variáveis de ambiente de e-mail não configuradas corretamente.")
        return

    msg = MIMEText(f"⚠️ Nova notícia ANTT detectada:\n\n{titulo}\n\nConfira no site: {url}")
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

def ler_ultimo_titulo():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def salvar_ultimo_titulo(titulo):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        f.write(titulo)
    print("💾 Último título salvo com sucesso.")

def buscar_noticias():
    print(f"🌐 Acessando página de notícias: {URL_NOVIDADES}")
    try:
        resp = requests.get(URL_NOVIDADES, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erro ao acessar {URL_NOVIDADES}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extrair títulos das notícias (exemplo: h3, h2, a)
    titulos = soup.find_all(['h3', 'h2', 'a'])
    lista_titulos = []
    for t in titulos:
        texto = t.get_text(strip=True).lower()
        if any(palavra in texto for palavra in PALAVRAS_CHAVE):
            lista_titulos.append(t.get_text(strip=True))

    return lista_titulos

def main():
    ultimo_titulo_salvo = ler_ultimo_titulo()
    titulos = buscar_noticias()

    if not titulos:
        print("⚠️ Nenhuma notícia relevante encontrada.")
        return

    # Procurar um título diferente do último salvo
    for titulo in titulos:
        if titulo != ultimo_titulo_salvo:
            print(f"✅ Nova notícia detectada: {titulo}")
            enviar_email(titulo, URL_NOVIDADES)
            salvar_ultimo_titulo(titulo)
            return

    print("ℹ️ Nenhuma notícia nova desde a última verificação.")

if __name__ == "__main__":
    main()
