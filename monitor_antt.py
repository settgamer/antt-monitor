import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import re
import os
import sys

# Configs de e-mail (vindas dos Secrets do GitHub)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

# URL da ANTT Legis
URL = "https://anttlegis.antt.gov.br/action/UrlPublicasAction.php?acao=abrirAtoPublico&num_ato=&sgl_tipo=RES&sgl_orgao=DG/ANTT/MT&vlr_ano=2025&seq_ato=000&cod_modulo=161&cod_menu=5408"

# Arquivo no repositório que guarda a última resolução
SAVE_FILE = "ultima_resolucao.txt"


def enviar_email(nova_res):
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print("❌ Variáveis de ambiente de e-mail não configuradas corretamente.")
        return

    msg = MIMEText(f"⚠️ Nova resolução ANTT detectada: {nova_res}\n\nConfira no site: {URL}")
    msg["Subject"] = f"Nova Resolução ANTT detectada: {nova_res}"
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


def buscar_ultima_resolucao():
    print("🌐 Acessando site da ANTT...")
    try:
        resp = requests.get(URL, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erro ao acessar o site da ANTT: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    textos = soup.get_text()

    # Expressão regular para encontrar números de resoluções
    match = re.findall(r"Resoluç[aã]o\s*n[ºo]?\s*(\d+)", textos, re.IGNORECASE)

    if match:
        numeros = list(map(int, match))
        maior = max(numeros)
        print(f"📄 Resoluções encontradas: {numeros}")
        return maior

    print("⚠️ Site acessado, mas nenhuma resolução foi encontrada.")
    return None


def ler_ultima_local():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return int(f.read().strip())
    return 0


def salvar_ultima_resolucao(numero):
    with open(SAVE_FILE, "w") as f:
        f.write(str(numero))
    print("💾 Última resolução salva com sucesso.")


def main():
    ultima_online = buscar_ultima_resolucao()
    if not ultima_online:
        print("🚫 Interrompendo: nenhuma resolução válida foi encontrada.")
        return

    ultima_local = ler_ultima_local()
    print(f"🔎 Última online: {ultima_online} | 💾 Local: {ultima_local}")

    if ultima_online > ultima_local:
        print(f"✅ Nova resolução detectada: {ultima_online}")
        enviar_email(ultima_online)
        salvar_ultima_resolucao(ultima_online)
    else:
        print("ℹ️ Nenhuma resolução nova detectada.")


if __name__ == "__main__":
    main()
