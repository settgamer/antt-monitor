import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import re
import os

# Configs de e-mail (vindas dos Secrets do GitHub)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

# URL da ANTT Legis
URL = "https://anttlegis.antt.gov.br/action/UrlPublicasAction.php?acao=abrirAtoPublico&num_ato=&sgl_tipo=RES&sgl_orgao=DG/ANTT/MT&vlr_ano=2025&seq_ato=000&cod_modulo=161&cod_menu=5408"

# Arquivo no repositório que guarda a última resolução
SAVE_FILE = "ultima_resolucao.txt"


def enviar_email(nova_res):
    msg = MIMEText(f"⚠️ Nova resolução ANTT detectada: {nova_res}\n\nConfira no site: {URL}")
    msg["Subject"] = f"Nova Resolução ANTT detectada: {nova_res}"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())


def buscar_ultima_resolucao():
    resp = requests.get(URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    textos = soup.get_text()
    match = re.findall(r"Resoluç[aã]o\s*n[ºo]?\s*(\d+)", textos, re.IGNORECASE)

    if match:
        numeros = list(map(int, match))
        return max(numeros)
    return None


def ler_ultima_local():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return int(f.read().strip())
    return 0


def salvar_ultima_resolucao(numero):
    with open(SAVE_FILE, "w") as f:
        f.write(str(numero))


def main():
    ultima_online = buscar_ultima_resolucao()
    if not ultima_online:
        print("❌ Não consegui encontrar resolução no site.")
        return

    ultima_local = ler_ultima_local()

    print(f"🔎 Última online: {ultima_online} | 💾 Local: {ultima_local}")

    if ultima_online > ultima_local:
        print(f"✅ Nova resolução detectada: {ultima_online}")
        enviar_email(ultima_online)
        salvar_ultima_resolucao(ultima_online)
    else:
        print("ℹ️ Nenhuma resolução nova.")


if __name__ == "__main__":
    main()
