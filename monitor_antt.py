import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import re
import os

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

URLS = [
    "https://anttlegis.antt.gov.br/action/UrlPublicasAction.php?acao=abrirAtoPublico&num_ato=&sgl_tipo=RES&sgl_orgao=DG/ANTT/MT&vlr_ano=2025&seq_ato=000&cod_modulo=161&cod_menu=5408",
    "https://www.antt.gov.br/assuntos/atos-normativos/resolucoes",
    "https://anttlegis.antt.gov.br/",
    "https://www.antt.gov.br/assuntos/legislacao",
    "https://anttlegis.antt.gov.br/action/UrlPublicasAction.php?acao=pesquisar"
]

SAVE_FILE = "ultima_resolucao.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/114.0.0.0 Safari/537.36"
}

def enviar_email(nova_res, url_usada):
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print("❌ Variáveis de ambiente de e-mail não configuradas corretamente.")
        return

    msg = MIMEText(f"⚠️ Nova resolução ANTT detectada: {nova_res}\n\nConfira no site: {url_usada}")
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

def ler_ultima_local():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return int(f.read().strip())
    return 0

def salvar_ultima_resolucao(numero):
    with open(SAVE_FILE, "w") as f:
        f.write(str(numero))
    print("💾 Última resolução salva com sucesso.")

def buscar_resolucao_em_texto(texto):
    # busca padrões comuns de "Resolução nº 1234"
    match = re.findall(r"Resoluç[aã]o\s*n[ºo]?\s*(\d+)", texto, re.IGNORECASE)
    if match:
        numeros = list(map(int, match))
        return max(numeros)
    return None

def buscar_no_site(url):
    print(f"🌐 Tentando acessar: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erro ao acessar {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    texto = soup.get_text(separator=" ")

    # Para o site oficial ANTT (resolucoes), tentar algo mais específico:
    if "www.antt.gov.br/assuntos/atos-normativos/resolucoes" in url:
        # Buscar links ou títulos que possam conter resoluções
        links = soup.find_all("a", href=True)
        resol_nums = []
        for link in links:
            text = link.get_text(strip=True)
            res_num = buscar_resolucao_em_texto(text)
            if res_num:
                resol_nums.append(res_num)
        if resol_nums:
            print(f"📄 Resoluções encontradas na página: {resol_nums}")
            return max(resol_nums)
        else:
            # Se não encontrou em links, tenta no texto normal
            return buscar_resolucao_em_texto(texto)

    # Para os outros sites, busca direto no texto geral:
    res = buscar_resolucao_em_texto(texto)
    if res:
        print(f"📄 Resoluções encontradas: {res}")
        return res

    print(f"⚠️ Nenhuma resolução encontrada em {url}.")
    return None

def main():
    ultima_local = ler_ultima_local()

    for url in URLS:
        resolucao = buscar_no_site(url)
        if resolucao and resolucao > ultima_local:
            print(f"✅ Nova resolução detectada: {resolucao} no site {url}")
            enviar_email(resolucao, url)
            salvar_ultima_resolucao(resolucao)
            return

    print("🚫 Interrompendo: nenhuma resolução válida foi encontrada.")

if __name__ == "__main__":
    main()
