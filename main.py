from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from time import sleep
import to_json
import json_worker
from infoparser import InfoGetter


class GrabberApp:

    def __init__(self, city, org_type, many):
        self.city = city
        self.org_type = org_type
        self.many = many

    def grab_data(self):
        
        # chrome_options = webdriver.ChromeOptions
        # chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--window-size=1420,1080")
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-gpu")

        # Создаем result.json
        # json_worker.JSONWorker("get", "")

        print("Парсинг начат")

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        
        driver = webdriver.Chrome(options=chrome_options)
        # driver.maximize_window()
        driver.get('https://yandex.ru/maps')

        # Вводим данные поиска
        driver.find_element(By.CLASS_NAME,'input__control').send_keys(self.city + ' ' + self.org_type)

        # Нажимаем на кнопку поиска
        driver.find_element(By.CLASS_NAME,'small-search-form-view__icon').click()
        sleep(2)

        slider = driver.find_element(By.CLASS_NAME,'scroll__scrollbar-thumb')
        # Основная вкладка со списком всех организаций
        parent_handle = driver.window_handles[0]

        org_id = 0
        organizations_href = ""
        try:
            for i in range(self.many):
                # Симулируем прокрутку экрана на главной странице поиска
                ActionChains(driver).click_and_hold(slider).move_by_offset(0, 100).release().perform()

                # Подгружаем ссылки на организации каждые 5 итераций
                if (org_id == 0) or (org_id % 5 == 0):
                    organizations_href = driver.find_elements(By.CLASS_NAME,'link-overlay')
                organization_url = organizations_href[i].get_attribute("href")

                # Открываем карточку организации в новой вкладке
                driver.execute_script(f'window.open("{organization_url}","org_tab");')
                child_handle = [x for x in driver.window_handles if x != parent_handle][0]
                driver.switch_to.window(child_handle)
                sleep(1)

                soup = BeautifulSoup(driver.page_source, "lxml")
                org_id += 1
                name = InfoGetter.get_name(soup)
                address = InfoGetter.get_address(soup)
                website = InfoGetter.get_website(soup)
                opening_hours = InfoGetter.get_opening_hours(soup)
                ypage = driver.current_url
                rating = InfoGetter.get_rating(soup)

                # Формирование ссылки на отзывы
                current_url_split = ypage.split('/')

                goods = ""
                try:
                    menu = driver.find_element(By.CLASS_NAME,'card-feature-view__main-content')
                    menu_text = driver.find_element(By.CLASS_NAME,'card-feature-view__main-content').text

                    if ('товары и услуги' in menu_text.lower()) or ('меню' in menu_text.lower()):
                        # Нажимаем на кнопку "Меню"/"Товары и услуги"
                        menu.click()
                        sleep(2)
                        soup = BeautifulSoup(driver.page_source, "lxml")
                        goods = InfoGetter.get_goods(soup)
                except NoSuchElementException:
                    pass

                #  Переходим на вкладку "Отзывы"
                reviews_url = 'https://yandex.ru/maps/org/' + current_url_split[5] + '/' + current_url_split[6] + \
                              '/reviews'
                driver.get(reviews_url)
                sleep(2)

                reviews = InfoGetter.get_reviews(soup, driver)

                # Записываем данные в OUTPUT.json
                output = to_json.into_json(org_id, name, address, website, opening_hours, ypage, goods, rating,
                                                reviews)
                json_worker.JSONWorker("set", output)
                print(f'Данные добавлены, id - {org_id}')

                # Закрываем вторичную вкладу и переходим на основную
                driver.close()
                driver.switch_to.window(parent_handle)
                sleep(1)

        except Exception as e:
            pass

        print('Данные сохранены в out/OUTPUT.json')
        driver.quit()


def main():
    city = input("Введите город : ")
    org_type = input("Введите тип организации : ")
    many = int(input("Количество : "))
    grabber = GrabberApp(city, org_type, many)
    grabber.grab_data()


if __name__ == '__main__':
    main()
