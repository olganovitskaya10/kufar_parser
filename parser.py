import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from tenacity import retry, wait_fixed

from  models import Notebook

class KufarParser:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }

    @classmethod
    @retry(wait=wait_fixed(0.2))
    def get_soup(cls, url: str) -> BeautifulSoup | None:
        response = requests.get(url, headers=cls.HEADERS)
        print(f'{response.status_code != 200}')
        if response.status_code == 200:
            raise ValueError(f'response status not 200, {response.status_code}')


        soup = BeautifulSoup(response.text, 'lxml')
        return soup

    @staticmethod
    def __get_notebook_list(soup: BeautifulSoup) -> list:
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

        return links


    @staticmethod
    def __get_notebook_data(url: str, soup: BeautifulSoup): ->
        notebook = Notebook(url)
        title = soup.find('h1',  class_='styles_brief_wrapper__title__Ksuxa')
        if title:
            title = title.text
            notebook.title = title

        price = soup.find('span', class_='styles_main__vIwzP')

        description = soup.find('div', class_='')
        if description:
            description = description.text
            notebook.description = description

            params =

            for param in params:
                key = param.find('div', class_='styles_pa')
                value = param.find('div', class_='')
                if key == 'Производитель':
                    notebook.manufacturer = value
                elif key == 'Диагональ экрана':
                    notebook.diagonal = value
                elif key == 'Разрешение экрана':
                    notebook.screen_resolution = value
                elif key == 'Операционная система':
                    notebook.os = value
                elif key == 'Процесор':
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

        images = soup.find_all('img', claass_='tyles_slide__image__AV4nX styles_slide__image__vertical__okVaq')
        images = [i['src']for i in images]
        notebook.images = images

        return

class Notebook:
    url: str
    title: str = ''
    price: float = 0.0
    description: str = ''
    manufacturer: str = ''
    diagonal: str = ''
    screen_resolution: str = ''
    os: str = ''
    processor: str = ''
    op_men: str = ''
    type_video_card: str = ''
    video_card: str = ''
    type_drive: str = ''
    capacity_drive: str = ''
    auto_work_time: str = ''
    state: str = ''
    images: list = field(default_factory=list)

    def run(self):
        url = 'https://www.kufar.by/l/r~minsk/noutbuki'
        links = self.__get_notebook_list(self.get_soup(url))
        for link in tqdm(links):
            soup = self.get_soup(link)
            notebook = self.__get_notebook_data(link, soup)
            print(notebook)



parse = KufarParser()
parse.run()
