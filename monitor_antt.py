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

# Lista de URLs para tentar
URLS = [
    "https://anttlegis.antt.gov.br/action/UrlPublicasAction.php?acao=abrirAtoPublico&num_ato=&sgl_tipo=RES&sgl_orgao=DG/ANTT/MT&vlr_ano=2025&seq_ato=000&cod_modulo=161&cod_menu=5408",
    "https://www.antt.gov.br/assuntos/atos-normativos/resolucoes",
    "https://anttlegis.antt.gov.br/",
    "https://www.antt.gov.br/assuntos/legislacao",
    "https://anttlegis.antt.gov.br/action/UrlPublicasAction.php?acao=pesquisar"
]

SAVE_FILE = "ultima_resolucao.txt"

def enviar_email(nova_res):
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print("❌ Variáveis de ambiente de e-mail não configuradas corretamente.")
        return

    msg = MIMEText(f"⚠️ Nova resolução ANTT detectada: {nova_res}\n\nConfira no site da ANTT.")
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
    maior_resolucao = None
    for url in URLS:
        print(f"🌐 Tentando acessar: {url}")
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"❌ Erro ao acessar {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        textos = soup.get_text()

        match = re.findall(r"Resoluç[aã]o\s*n[ºo]?\s*(\d+)", textos, re.IGNORECASE)
        if match:
            numeros = list(map(int, match))
            local_max = max(numeros)
            print(f"📄 Resoluções encontradas em {url}: {numeros} | Maior: {local_max}")
            if maior_resolucao is None or local_max > maior_resolucao:
                maior_resolucao = local_max
        else:
            print(f"⚠️ Nenhuma resolução encontrada em {url}.")

    return maior_resolucao

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
    MODO_TESTE = False  # Troque para True para forçar envio de e-mail

    if MODO_TESTE:
        print("🧪 MODO TESTE ATIVADO — enviando e-mail de teste.")
        enviar_email("TESTE-9999")
        return

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
