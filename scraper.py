# scraper.py
import time
import random
import datetime
from bs4 import BeautifulSoup
import os

# <<< MUDANÇA NAS IMPORTAÇÕES >>>
# Importamos a nova biblioteca e removemos as antigas do Selenium/webdriver-manager
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# A biblioteca selenium-stealth não é mais necessária

def setup_driver():
    """
    Configura o driver usando undetected-chromedriver para máxima discrição.
    """
    options = uc.ChromeOptions()
    profile_path = os.path.join(os.getcwd(), "chrome_profile")
    options.add_argument(f'--user-data-dir={profile_path}')
    
    # É ESSENCIAL RODAR SEM HEADLESS NA PRIMEIRA VEZ
    # options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    print("Inicializando o Undetected Chromedriver...")
    # <<< USA O DRIVER DA NOVA BIBLIOTECA >>>
    driver = uc.Chrome(options=options)
    
    return driver

# A função handle_initial_popups continua útil
def handle_initial_popups(driver, site_identifier):
    try:
        wait = WebDriverWait(driver, 5)
        if site_identifier == 'googleshopping':
            cookie_button_xpath = "//button[.//span[contains(text(), 'Aceitar tudo')]]"
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, cookie_button_xpath)))
        elif site_identifier == 'mercadolivre':
            cookie_button_selector = "button.cookie-consent-banner__cta.cookie-consent-banner__cta--accept"
            cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, cookie_button_selector)))
        else: return
        cookie_button.click()
        print(f"Banner de cookies em '{site_identifier}' foi tratado com sucesso.")
        time.sleep(2)
    except TimeoutException:
        print(f"Nenhum banner de cookies encontrado em '{site_identifier}'. Procedendo...")
    except Exception as e:
        print(f"Erro ao tentar lidar com pop-up em '{site_identifier}': {e}")

#
# O RESTO DO CÓDIGO (fetch_page_with_selenium, parsers, run_site_scraper)
# PODE CONTINUAR EXATAMENTE O MESMO.
# A única mudança foi como o 'driver' é criado.
#
def fetch_page_with_selenium(driver, url, site_identifier):
    try:
        driver.get(url)
        handle_initial_popups(driver, site_identifier)
        if site_identifier == 'googleshopping':
            wait_selector = "div.sh-pr__product-results-grid"
        elif site_identifier == 'mercadolivre':
            wait_selector = "li.ui-search-layout__item"
        else: return None
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector)))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        return driver.page_source
    except TimeoutException:
        print(f"Tempo de espera esgotado. A página de {site_identifier} pode ter um CAPTCHA ou mudou radicalmente.")
        driver.save_screenshot(f"error_screenshot_{site_identifier}.png")
        with open(f"error_page_source_{site_identifier}.html", "w", encoding="utf-8") as f: f.write(driver.page_source)
        return None
    except Exception as e:
        print(f"Erro ao carregar a página {url} com Selenium: {e}")
        return None

def parse_google_shopping(soup):
    products_on_page = []
    product_list = soup.select("div.sh-dgr__content")
    for item in product_list:
        try:
            link_tag = item.find('a', class_='sh-dgr__offer-content')
            if not link_tag: continue
            product_url = "https://www.google.com" + link_tag['href']
            title_tag = item.find('h3', class_='XjK3Mb')
            title = title_tag.text.strip() if title_tag else "N/A"
            image_tag = item.find('img.TL92Hc')
            image_url = image_tag['src'] if image_tag else "N/A"
            price_tag = item.find('span', class_='a8Pemb')
            price_str = price_tag.text.replace("R$", "").replace(".", "").strip()
            price = float(price_str.replace(',', '.')) if price_str else 0.0
            if title and price > 0:
                products_on_page.append({'product_url': product_url, 'title': title, 'price_brl': price, 'image_url': image_url, 'source': 'google.com/shopping'})
        except Exception: continue
    return products_on_page

def parse_mercado_livre(soup):
    products_on_page = []
    product_list = soup.select("ol.ui-search-layout li.ui-search-layout__item")
    for item in product_list:
        try:
            link_tag = item.find('a', class_='ui-search-link', href=True)
            if not link_tag: continue
            product_url = link_tag['href']
            title = item.find('h2', class_='ui-search-item__title').text.strip()
            image_tag = item.find('img', class_='ui-search-result-image__image')
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

PARSERS = { 'googleshopping': parse_google_shopping, 'mercadolivre': parse_mercado_livre }

# Dentro de scraper.py

def run_site_scraper(driver, site_config):
    site_identifier = site_config['identifier']
    keyword = site_config['keyword']
    max_pages = site_config['max_pages']
    
    print(f"\n--- Iniciando varredura para o site: {site_identifier} com o termo '{keyword}' ---")
    
    # Verifica se temos um parser para este site antes de continuar
    if site_identifier not in PARSERS:
        print(f"ERRO: Nenhum parser definido para '{site_identifier}'. Pulando.")
        return []
        
    parser_func = PARSERS[site_identifier]
    all_products = []

    for page_num in range(1, max_pages + 1):
        # <<< CORREÇÃO PRINCIPAL: Definir 'current_url' dentro de cada bloco >>>
        current_url = "" # Inicializa como string vazia

        if site_identifier == 'googleshopping':
            keyword_formatted = keyword.replace(' ', '+')
            # A paginação do Google é complexa, focamos na primeira página
            if page_num > 1:
                print("Finalizando busca no Google Shopping (max_pages=1).")
                break
            current_url = f"https://www.google.com/search?tbm=shop&q={keyword_formatted}"
            
        elif site_identifier == 'mercadolivre':
            keyword_formatted = keyword.replace(' ', '-')
            if page_num == 1:
                current_url = f"https://lista.mercadolivre.com.br/{keyword_formatted}"
            else:
                try:
                    # Tenta encontrar o botão "Seguinte" para ir para a próxima página
                    next_button = driver.find_element(By.CSS_SELECTOR, "a.andes-pagination__link[title='Seguinte']")
                    current_url = next_button.get_attribute('href')
                except:
                    print("Botão 'Seguinte' não encontrado. Finalizando a busca neste site.")
                    break
        
        # Se, por algum motivo, a URL não for definida, pula para o próximo ciclo
        if not current_url:
            print(f"ERRO: Não foi possível gerar a URL para '{site_identifier}' na página {page_num}. Pulando.")
            continue

        print(f"Coletando dados da página {page_num}: {current_url}")
        page_html = fetch_page_with_selenium(driver, current_url, site_identifier)

        if not page_html: break

        soup = BeautifulSoup(page_html, 'html.parser')
        products_from_page = parser_func(soup)

        if not products_from_page:
            print("Nenhum produto encontrado na página após o carregamento.")
            driver.save_screenshot(f"no_products_found_{site_identifier}_page_{page_num}.png")
            break
        
        for product in products_from_page:
            product['scraped_at'] = datetime.datetime.now().isoformat()
            product['innovation_score'] = None
        
        all_products.extend(products_from_page)
        time.sleep(random.uniform(5, 8))

    print(f"--- Varredura para '{site_identifier}' concluída. {len(all_products)} produtos encontrados. ---")
    return all_products