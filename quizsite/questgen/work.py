import wikipediaapi
from questgen.generator import Generator
import requests
from bs4 import BeautifulSoup


def generate_quest(keyword, src):
    generator = Generator()

    fi = None
    if src == 'wiki':
        wiki_wiki = wikipediaapi.Wikipedia(
                language='en',
                extract_format=wikipediaapi.ExtractFormat.WIKI
        )

        p_wiki = wiki_wiki.page(keyword)
        fi = p_wiki.text
    elif src == 'cust':
        htmldata = requests.get(keyword).text
        htmldata = BeautifulSoup(htmldata, 'html.parser')
        fi = ''
        for data in htmldata.find_all('p'):
            fi += data.get_text()

    if len(fi) != 0:
        if len(fi) > 1000:
            collection = generator.generate_questions(fi[:1000])
        else:
            collection = generator.generate_questions(fi)

        ls = []
        for value in collection.values():
            if value['question'] and len(value['answer']) < 25:
                ls.append(value)

        return ls
    else:
        return None

