# scraper_worker.py
import time
import datetime
# Importamos a nova função de setup do driver
from scraper import run_site_scraper, setup_driver 
from database import save_products

SCRAPE_INTERVAL_SECONDS = 21600  # 6 horas

TARGET_SITES = [
    {
        'identifier': 'amazon',
        'keyword': 'presentes criativos',
        'max_pages': 2 # Reduzir para testes iniciais
    },
    {
        'identifier': 'mercadolivre',
        'keyword': 'presentes criativos',
        'max_pages': 2 # Reduzir para testes iniciais
    },
]

def main_loop():
    while True:
        print(f"\n[{datetime.datetime.now()}] +++ INICIANDO NOVO CICLO DE VARREDURA GERAL COM SELENIUM +++")
        
        # Inicializa o driver do Selenium
        driver = setup_driver()
        
        all_collected_products = []
        try:
            for config in TARGET_SITES:
                # Passa o driver para a função de scraping
                products_from_site = run_site_scraper(driver, config)
                all_collected_products.extend(products_from_site)
            
            if all_collected_products:
                save_products(all_collected_products)
            
            print(f"+++ CICLO GERAL CONCLUÍDO. Total de {len(all_collected_products)} produtos coletados. +++")
            
        except Exception as e:
            print(f"Ocorreu um erro inesperado no ciclo principal: {e}")
        finally:
            # É CRUCIAL fechar o driver no final para liberar os recursos
            if driver:
                driver.quit()
            print("Driver do Selenium fechado.")

        print(f"Próxima varredura em {SCRAPE_INTERVAL_SECONDS / 3600:.1f} horas.")
        time.sleep(SCRAPE_INTERVAL_SECONDS)

if __name__ == '__main__':
    main_loop()