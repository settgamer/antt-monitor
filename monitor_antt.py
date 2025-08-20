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

# URLs para buscar resoluções oficiais ANTT
URLS = [
    "https://anttlegis.antt.gov.br/action/UrlPublicasAction.php?acao=abrirAtoPublico&num_ato=&sgl_tipo=RES&sgl_orgao=DG/ANTT/MT&vlr_ano=2025&seq_ato=000&cod_modulo=161&cod_menu=5408",
    "https://www.antt.gov.br/assuntos/atos-normativos/resolucoes",
    "https://anttlegis.antt.gov.br/",
    "https://www.antt.gov.br/assuntos/legislacao",
    "https://anttlegis.antt.gov.br/action/UrlPublicasAction.php?acao=pesquisar"
]

# URL para notícias oficiais ANTT que vamos filtrar
URL_NOTICIAS = "https://www.gov.br/antt/pt-br/assuntos/ultimas-noticias"

SAVE_FILE_RESOLUCAO = "ultima_resolucao.txt"
SAVE_FILE_NOTICIAS = "ultima_noticia.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def enviar_email(titulo, url):
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print("❌ Variáveis de ambiente de e-mail não configuradas corretamente.")
        return

    msg = MIMEText(f"⚠️ Nova notícia/resolução ANTT detectada:\n\n{titulo}\n\nConfira no site: {url}")
    msg["Subject"] = f"Nova notícia/resolução ANTT detectada"
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

def ler_arquivo(nome_arquivo):
    if os.path.exists(nome_arquivo):
        with open(nome_arquivo, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def salvar_arquivo(nome_arquivo, texto):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"💾 Dados salvos com sucesso em {nome_arquivo}.")

def buscar_ultima_resolucao():
    maior_resolucao = None
    for url in URLS:
        print(f"🌐 Tentando acessar: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
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

def buscar_noticias():
    print(f"🌐 Acessando página de notícias: {URL_NOTICIAS}")
    try:
        resp = requests.get(URL_NOTICIAS, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erro ao acessar {URL_NOTICIAS}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Frases para filtrar os títulos que interessam (em minúsculas)
    frases_monitorar = [
        "antt reajusta tabela dos pisos mínimos de frete",
        "antt avança na fiscalização do piso mínimo de frete",
        "tabelas de frete atualizadas:"
    ]

    titulos_filtrados = []
    # Normalmente os títulos estão em <h3> ou links <a> dentro das notícias
    possiveis_titulos = soup.find_all(['h2', 'h3', 'a'])
    for t in possiveis_titulos:
        texto = t.get_text(strip=True).lower()
        if any(texto.startswith(frase) for frase in frases_monitorar):
            titulos_filtrados.append(t.get_text(strip=True))

    print(f"🔍 Notícias filtradas encontradas: {len(titulos_filtrados)}")
    return titulos_filtrados

def main():
    MODO_TESTE = False  # Troque para True para forçar envio de e-mail

    if MODO_TESTE:
        print("🧪 MODO TESTE ATIVADO — enviando e-mail de teste.")
        enviar_email("TESTE DE NOTIFICAÇÃO", URL_NOTICIAS)
        return

    # Verifica resoluções novas
    ultima_resolucao_online = buscar_ultima_resolucao()
    ultima_resolucao_local = ler_arquivo(SAVE_FILE_RESOLUCAO)
    ultima_resolucao_local_num = int(ultima_resolucao_local) if ultima_resolucao_local and ultima_resolucao_local.isdigit() else 0
    print(f"🔎 Última resolução online: {ultima_resolucao_online} | Local: {ultima_resolucao_local_num}")

    if ultima_resolucao_online and ultima_resolucao_online > ultima_resolucao_local_num:
        print(f"✅ Nova resolução detectada: {ultima_resolucao_online}")
        enviar_email(f"Resolução nº {ultima_resolucao_online}", "ANTT - site oficial")
        salvar_arquivo(SAVE_FILE_RESOLUCAO, str(ultima_resolucao_online))
        return

    # Verifica notícias novas baseadas nos títulos filtrados
    noticias = buscar_noticias()
    if noticias:
        ultima_noticia_local = ler_arquivo(SAVE_FILE_NOTICIAS)
        if noticias[0] != ultima_noticia_local:
            print(f"✅ Nova notícia detectada: {noticias[0]}")
            enviar_email(noticias[0], URL_NOTICIAS)
            salvar_arquivo(SAVE_FILE_NOTICIAS, noticias[0])
            return
        else:
            print("ℹ️ Nenhuma notícia nova detectada.")
    else:
        print("⚠️ Nenhuma notícia relevante encontrada.")

if __name__ == "__main__":
    main()
