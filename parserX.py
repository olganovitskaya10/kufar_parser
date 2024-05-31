import json
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from tenacity import retry, wait_fixed
from environs import Env
from dataclasses import astuple

from db_client_p import DBPostgres
from models import Notebook

env = Env()
env.read_env()

DBNAME = env('DBNAME')
DBUSER = env('DBUSER')
DBPASSWORD = env('DBPASSWORD')
DBHOST = env('DBHOST')
DBPORT = env('DBPORT')


class KufarDB(DBPostgres):
    def create_table(self):
        self.execute_query(
            """CREATE TABLE IF NOT EXISTS notebook(
        id SERIAL PRIMARY KEY ,
        url varchar(160) unique ,
        title varchar(500),
        price NUMERIC(10, 2),
        description TEXT,
        manufacture varchar(100),
        diagonal varchar(100),
        screen_resolution varchar(100),
        os varchar(100),
        processor varchar(100),
        op_mem varchar(100),
        type_video_card varchar(100),
        video_card varchar(100),
        type_drive varchar(100),
        capacity_drive varchar(100),
        auto_work_time varchar(100),
        state varchar(100)
);

CREATE TABLE IF NOT EXISTS image(
    id serial primary key ,
    image_url varchar(160) unique ,
    notebook_id INTEGER REFERENCES notebook(id) ON DELETE CASCADE                                                            
);
""")

    def insert_data(self, data):
        data = [astuple(i) for i in data]
        self.execute_query("""WITH note_id as (
        INSERT INTO core_app_notebook(url, title, price, description, manufacturer, diagonal, screen_resolution, os, processor, 
        op_mem, type_video_card, video_card, type_drive, capacity_drive, auto_work_time, state) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s, %s) 
        ON CONFLICT (url) DO UPDATE SET price = excluded.price RETURNING id) 
        INSERT INTO core_app_image(image_url, notebook_id) VALUES (
        unnest(COALESCE(%s, ARRAY[]::text[])), (SELECT id FROM note_id)
        ) ON CONFLICT (image_url) DO NOTHING 
        """, data)


class KufarParser:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }

    DB = KufarDB(
        dbname=DBNAME,
        user=DBUSER,
        password=DBPASSWORD,
        host=DBHOST,
        port=DBPORT
    )

    @classmethod
    @retry(wait=wait_fixed(0.2))
    def get_soup(cls, url: str) -> BeautifulSoup:
        response = requests.get(url, headers=cls.HEADERS)
        print(f'{response.status_code} | {url}')
        if response.status_code != 200:
            raise ValueError(f'response status not 200, {response.status_code}')

        soup = BeautifulSoup(response.text, 'lxml')
        return soup

    @staticmethod
    def __get_notebook_list(soup: BeautifulSoup) -> tuple:
        links = []
        sections = soup.find_all('section')
        for section in sections:
            link = section.find('a', href=True)['href'].split('?')[0]
            price = section.find('p', class_='styles_price__G3lbO')
            if not price:
                price = section.find('span', class_='styles_price__vIwzP')
            price = price.text
            price = re.sub(r'[^0-9]', '', price)
            if price.isdigit():
                links.append(link)

        json_data = soup.find('script', id='__NEXT_DATA__').text
        json_data = json.loads(json_data)
        tokens = json_data['props']['initialState']['listing']['pagination']
        next_page = list(filter(lambda el: el['label'] == 'next', tokens))[0]
        if next_page:
            token = next_page['token']
        else:
            token = None

        return links, token

    @staticmethod
    def __get_notebook_data(url: str, soup: BeautifulSoup) -> Notebook:
        notebook = Notebook(url)
        title = soup.find('h1', class_='styles_brief_wrapper__title__Ksuxa')
        if title:
            title = title.text
            notebook.title = title

        price = soup.find('span', class_='styles_main__eFbJH').find('div', class_='styles_discountPrice__WuQiu')
        if not price:
            price = soup.find('span', class_='styles_main__eFbJH')

        price = price.text.replace(' ', '').replace('р.', '')
        price = float(price)
        notebook.price = price

        description = soup.find('div', itemprop="description")
        if description:
            description = description.text
            notebook.description = description

        params = soup.find_all('div',
                               class_='styles_parameter_wrapper__L7UfK')

        for param in params:
            key = param.find('div', class_='styles_parameter_label__i_OkS').text
            value = param.find('div', class_='styles_parameter_value__BkYDy').text
            if key == 'Производитель':
                notebook.manufacturer = value
            elif key == 'Диагональ экрана':
                notebook.diagonal = value
            elif key == 'Разрешение экрана':
                notebook.screen_resolution = value
            elif key == 'Операционная система':
                notebook.os = value
            elif key == 'Процессор':
                notebook.processor = value
            elif key == 'Оперативная память':
                notebook.op_mem = value
            elif key == 'Тип видеокарты':
                notebook.type_video_card = value
            elif key == 'Видеокарта':
                notebook.video_card = value
            elif key == 'Тип накопителя':
                notebook.type_drive = value
            elif key == 'Ёмкость накопителя':
                notebook.capacity_drive = value
            elif key == 'Время автономной работы':
                notebook.auto_work_time = value
            elif key == 'Состояние':
                notebook.state = value

        images = soup.find_all('img', class_='styles_slide__image__AV4nX styles_slide__image__vertical__okVaq')
        images = [i['src'] for i in images]
        notebook.images = images

        return notebook

    def run(self):

        url = 'https://www.kufar.by/l/r~minsk/noutbuki'
        flag = True
        while flag:

            links_and_token = self.__get_notebook_list(self.get_soup(url))
            links = links_and_token[0]
            token = links_and_token[1]
            notebooks = []
            for link in tqdm(links):
                soup = self.get_soup(link)
                notebook = self.__get_notebook_data(link, soup)
                notebooks.append(notebook)

            self.DB.insert_data(notebooks)
            if token:
                url = f'https://www.kufar.by/l/r~minsk/noutbuki?cursor={token}'
            else:
                flag = False


if __name__ == '__main__':
    parse = KufarParser()
    parse.run()