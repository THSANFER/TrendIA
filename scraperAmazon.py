# scraper.py
import time
import random
import datetime
from bs4 import BeautifulSoup

# Importações do Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# <<< NOVA IMPORTAÇÃO >>>
from selenium_stealth import stealth

def setup_driver():
    """Configura o driver do Chrome com técnicas anti-detecção."""
    chrome_options = Options()
    # Roda o navegador em modo "headless" (sem interface gráfica visível)
    # IMPORTANTE: Alguns sites detectam o modo headless. Se continuar falhando,
    # comente a linha abaixo para ver o que o navegador está realmente vendo.
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") # Remove o flag de automação
    
    # Instala e gerencia o ChromeDriver automaticamente
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # <<< APLICAÇÃO DO STEALTH >>>
    # Esta é a parte mágica.
    stealth(driver,
            languages=["pt-BR", "pt"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    return driver


def fetch_page_with_selenium(driver, url, site_identifier):
    """Carrega uma página e espera por elementos específicos de cada site."""
    try:
        driver.get(url)
        
        # <<< LÓGICA DE ESPERA MELHORADA >>>
        # Define o seletor de espera com base no site.
        if site_identifier == 'amazon':
            wait_selector = "div[data-component-type='s-search-result']"
        elif site_identifier == 'mercadolivre':
            wait_selector = "li.ui-search-layout__item" # Corrigindo o seletor do ML para a tag 'li'
        else:
            return None # Site não suportado

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
        )
        # Salva um screenshot para depuração (opcional, mas muito útil)
        # driver.save_screenshot(f"debug_screenshot_{site_identifier}.png")
        return driver.page_source
    except TimeoutException:
        print(f"Tempo de espera esgotado. A página de {site_identifier} pode ter um CAPTCHA ou mudou radicalmente.")
        # Salva um screenshot para vermos o que o navegador viu
        driver.save_screenshot(f"error_screenshot_{site_identifier}.png")
        return None
    except Exception as e:
        print(f"Erro ao carregar a página {url} com Selenium: {e}")
        return None

# --- Funções de parse (atualizando seletor do Mercado Livre) ---
def parse_amazon(soup):
    # ... (código do parse_amazon da resposta anterior, sem alterações)
    products_on_page = []
    product_list = soup.find_all('div', {'data-component-type': 's-search-result'})
    for item in product_list:
        try:
            link_tag = item.find('a', class_='a-link-normal', href=True)
            if not link_tag or not link_tag.find('span', class_='a-text-normal'): continue
            product_url = "https://www.amazon.com.br" + link_tag['href']
            title = link_tag.find('span', class_='a-text-normal').text.strip()
            image_url = item.find('img', class_='s-image')['src']
            price_whole = item.find('span', class_='a-price-whole')
            price_fraction = item.find('span', class_='a-price-fraction')
            price = 0.0
            if price_whole and price_fraction:
                price_str = f"{price_whole.text.replace('.', '')}{price_fraction.text}"
                price = float(price_str.replace(',', '.'))
            if title and price > 0:
                products_on_page.append({'product_url': product_url, 'title': title, 'price_brl': price, 'image_url': image_url, 'source': 'amazon.com.br'})
        except Exception: continue
    return products_on_page

def parse_mercado_livre(soup):
    products_on_page = []
    # <<< CORREÇÃO DO SELETOR PRINCIPAL DO MERCADO LIVRE >>>
    # A estrutura mais confiável é a tag <ol> com a classe de lista.
    product_list = soup.select("ol.ui-search-layout li.ui-search-layout__item")

    for item in product_list:
        try:
            link_tag = item.find('a', class_='ui-search-link', href=True)
            if not link_tag: continue
            
            product_url = link_tag['href']
            title = item.find('h2', class_='ui-search-item__title').text.strip()
            image_tag = item.find('img', class_='ui-search-result-image__image')
            # Imagens podem ser carregadas de forma "preguiçosa" (lazy-loading)
            image_url = image_tag.get('data-src') or image_tag.get('src')

            price_symbol = item.find('span', class_='andes-money-amount__currency-symbol').text.strip()
            price_fraction = item.find('span', class_='andes-money-amount__fraction').text.replace('.', '')
            price_cents = item.find('span', class_='andes-money-amount__cents')
            
            if price_symbol == "R$":
                price_str = f"{price_fraction}.{price_cents.text if price_cents else '00'}"
                price = float(price_str)
            else: price = 0.0

            if title and price > 0:
                products_on_page.append({'product_url': product_url, 'title': title, 'price_brl': price, 'image_url': image_url, 'source': 'mercadolivre.com.br'})
        except Exception: continue
            
    return products_on_page

PARSERS = {
    'amazon': parse_amazon,
    'mercadolivre': parse_mercado_livre,
}

# --- O orquestrador agora passa o 'site_identifier' para a função de fetch ---
def run_site_scraper(driver, site_config):
    site_identifier = site_config['identifier']
    keyword = site_config['keyword']
    max_pages = site_config['max_pages']
    
    print(f"\n--- Iniciando varredura para o site: {site_identifier} com o termo '{keyword}' ---")
    
    parser_func = PARSERS[site_identifier]
    all_products = []

    for page_num in range(1, max_pages + 1):
        if site_identifier == 'amazon':
            keyword_formatted = keyword.replace(' ', '+')
            current_url = f"https://www.amazon.com.br/s?k={keyword_formatted}&page={page_num}"
        elif site_identifier == 'mercadolivre':
            keyword_formatted = keyword.replace(' ', '-')
            if page_num == 1:
                current_url = f"https://lista.mercadolivre.com.br/{keyword_formatted}"
            else:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "a.andes-pagination__link[title='Seguinte']")
                    current_url = next_button.get_attribute('href')
                except:
                    print("Botão 'Seguinte' não encontrado. Finalizando a busca neste site.")
                    break
        else: continue

        print(f"Coletando dados da página {page_num}: {current_url}")
        # Passa o identificador para a função de fetch
        page_html = fetch_page_with_selenium(driver, current_url, site_identifier)

        if not page_html: break

        soup = BeautifulSoup(page_html, 'html.parser')
        products_from_page = parser_func(soup)

        if not products_from_page:
            print("Nenhum produto encontrado na página após o carregamento. A estrutura pode ter mudado.")
            break
        
        for product in products_from_page:
            product['scraped_at'] = datetime.datetime.now().isoformat()
            product['innovation_score'] = None
        
        all_products.extend(products_from_page)
        time.sleep(random.uniform(5, 10)) # Aumentar ainda mais o tempo de espera

    print(f"--- Varredura para '{site_identifier}' concluída. {len(all_products)} produtos encontrados. ---")
    return all_products