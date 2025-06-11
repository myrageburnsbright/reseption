import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from urllib.parse import urljoin

# --- НАСТРОЙКИ ---
# URL страницы с каталогом товаров
TARGET_URL = 'https://re-seption.com/katalog'

# Твои селекторы
LOAD_MORE_BUTTON_SELECTOR = '.t-store__load-more-btn' 
PRODUCT_CARD_SELECTOR = '.t-store__card'
# ------------------


def setup_driver():
    """Настраивает и возвращает драйвер для Selenium."""
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except ImportError:
        print("Библиотека webdriver-manager не найдена. Установите: pip install webdriver-manager")
        service = Service()
        
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # Включи, если не хочешь видеть окно браузера
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def click_load_more_button(driver):
    """Находит и нажимает кнопку 'Загрузить ещё', пока она существует."""
    while True:
        try:
            load_more_button = driver.find_element(By.CSS_SELECTOR, LOAD_MORE_BUTTON_SELECTOR)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
            time.sleep(1)
            load_more_button.click()
            print("Нажал на кнопку 'Загрузить ещё'...")
            time.sleep(3)
        except ElementClickInterceptedException:
            print("Клик перехвачен, пробую прокрутить ниже...")
            driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(1)
        except NoSuchElementException:
            print("Кнопка 'Загрузить ещё' больше не найдена.")
            break
        except Exception as e:
            print(f"Произошла ошибка при клике: {e}")
            break


def get_and_print_product_links(driver):
    """Собирает все ссылки на товары и выводит их в консоль."""
    soup = BeautifulSoup(driver.page_source, 'lxml')
    link_tags = set() # Используем set для автоматического удаления дубликатов
    
    product_cards = soup.select(PRODUCT_CARD_SELECTOR)
    
    for card in product_cards:
        # Ищем первую попавшуюся ссылку внутри карточки
        link_tag = card.select_one('a')
        if link_tag and link_tag.get('href'):
            link_tags.add(link_tag.get('href'))
            
    print(f"\n--- Найдено {len(link_tags)} уникальных ссылок ---")
    
    # Получаем базовый URL, чтобы превратить относительные ссылки в абсолютные
    base_url = driver.current_url
    
    # Выводим каждую ссылку на новой строке
    for link in link_tags:
        absolute_link = urljoin(base_url, link)
        print(absolute_link)


# --- Основной процесс ---
if __name__ == '__main__':
    driver = setup_driver()
    try:
        # 1. Зайти на страницу каталога
        driver.get(TARGET_URL)
        print(f"Открываю страницу: {TARGET_URL}")
        time.sleep(3) 

        # 2. Нажимать на кнопку "Загрузить ещё"
        click_load_more_button(driver)
        print("Все товары на странице загружены.")

        # 3. Собрать все ссылки и вывести их в терминал
        get_and_print_product_links(driver)

    finally:
        # 4. Закрыть браузер
        driver.quit()
        print("\n--- Сбор ссылок завершен. ---")

