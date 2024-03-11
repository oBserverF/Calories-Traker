import requests
import fake_useragent
import bs4
from database import add_product_in_db

ua = fake_useragent.UserAgent().random
headers = {'user-agent': ua}

for i in range(83):
    url = f'https://calorizator.ru/product/all?page={i}'
    content = requests.get(url, headers=headers).text
    soap = bs4.BeautifulSoup(content, 'html.parser')
    table_products = soap.find('tbody').find_all('tr')
    for product in table_products:
        title = product.find_all('td')[1].text[1:]
        calories = product.find_all('td')[-1].text[1:]
        add_product_in_db(title, calories)
