import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os
import time
import random

# Configurações de ambiente
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

# URLs de busca no site da ANTT
SEARCH_URLS = [
    "https://www.gov.br/antt/pt-br/search?origem=form&SearchableText=Tabelas+de+frete+atualizadas+ANTT",
    "https://www.gov.br/antt/pt-br/search?origem=form&SearchableText=ANTT+reajusta+tabela+dos+pisos+m%C3%ADnimos+de+frete"
]

DATA_LIMITE = datetime.strptime("18/07/2025", "%d/%m/%Y")

TITULOS_FILTRO = [
    "Tabelas de frete atualizadas",
    "ANTT reajusta tabela dos pisos mínimos de frete"
]

# Lista de User-Agents para rotação
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
]

def salvar_html(texto, nome_arquivo):
    """Salva o HTML retornado em um arquivo para depuração."""
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"📝 HTML salvo em: {nome_arquivo}")

def enviar_email(titulo, link, data):
    if not all([EMAIL_USER, EMAIL_PASS, EMAIL_TO]):
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

def buscar_noticias_antt(url):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.gov.br/antt/pt-br",
        "Connection": "keep-alive"
    }

    print(f"🌐 Pesquisando no site da ANTT: {url}")
    try:
        time.sleep(random.uniform(3, 6))  # Atraso para evitar bloqueio
        session = requests.Session()
        resp = session.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erro ao acessar o site da ANTT: {e}")
        print(f"Resposta do servidor (primeiros 500 caracteres): {resp.text[:500]}...")
        salvar_html(resp.text, f"error_response_antt_{url.split('=')[-1].replace('+', '_')}.html")
        return []

    # Salvar o HTML para depuração
    salvar_html(resp.text, f"response_antt_{url.split('=')[-1].replace('+', '_')}.html")

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    # Log do HTML retornado
    print(f"📝 HTML retornado (primeiros 200 caracteres): {soup.prettify()[:200]}...")
    # Log das classes dos primeiros divs
    print(f"🔍 Primeiros divs encontrados: {[div.get('class') for div in soup.find_all('div')[:5]]}")

    # Verificar se a página contém mensagem de "nenhum resultado"
    no_results = soup.find(string=re.compile(r'(nenhum resultado|sem resultados|não encontrado)', re.I))
    if no_results:
        print(f"⚠️ Mensagem encontrada: '{no_results}' - Nenhum resultado retornado pela busca.")
        return []

    # Seletores ajustados para resultados de busca
    for item in soup.find_all(['div', 'article'], class_=re.compile(r'search-result|article|content|item|noticia|result')):
        titulo_tag = item.find(['h2', 'h3', 'a'])
        link_tag = item.find('a', href=True)
        data_tag = item.find(['span', 'time', 'div'], class_=re.compile(r'date|data|published|time|metadata'))

        if not titulo_tag or not link_tag:
            print(f"⚠️ Resultado sem título ou link: {item.get_text(strip=True)[:50]}...")
            continue

        titulo = titulo_tag.get_text(strip=True)
        link = link_tag['href']
        # Completar o link se for relativo
        if link.startswith('/'):
            link = f"https://www.gov.br{link}"

        data_texto = data_tag.get_text(strip=True) if data_tag else item.get_text(strip=True)
        data = extrair_data(data_texto)

        print(f"📄 Encontrado: {titulo} | Data: {data} | Link: {link}")

        resultados.append({
            "titulo": titulo,
            "link": link,
            "data": data,
            "snippet": item.get_text(strip=True)[:200]
        })

    if not resultados:
        print("⚠️ Nenhum resultado válido encontrado para esta busca.")
    return resultados

def extrair_data(texto):
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }

    # Formato DD/MM/YYYY
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', texto)
    if match:
        try:
            return datetime.strptime(match.group(0), "%d/%m/%Y")
        except:
            pass

    # Formato "DD de mês de YYYY"
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

    # Formato "DD mês YYYY"
    match = re.search(r'(\d{1,2}) (\w+) (\d{4})', texto.lower())
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

    print(f"⚠️ Nenhuma data extraída do texto: {texto[:100]}...")
    return None

def main():
    todas_noticias = []
    for url in SEARCH_URLS:
        resultados = buscar_noticias_antt(url)
        todas_noticias.extend(resultados)

    if not todas_noticias:
        print("⚠️ Nenhuma notícia encontrada na pesquisa ANTT.")
        return

    # Eliminar duplicatas com base no link
    seen_links = set()
    noticias_unicas = []
    for noticia in todas_noticias:
        if noticia['link'] not in seen_links:
            seen_links.add(noticia['link'])
            noticias_unicas.append(noticia)

    # Ordenar por data, ignorando None, colocando None no fim
    noticias_unicas = sorted(
        noticias_unicas, 
        key=lambda n: n['data'] or datetime.min, 
        reverse=True
    )

    ultima = noticias_unicas[0]
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
