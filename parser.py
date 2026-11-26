import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from urllib.parse import urljoin


BASE_URL = 'https://habr.com'
START_URL = 'https://habr.com/ru/articles/'
KEYWORDS = ['дизайн', 'фото', 'web', 'python']
MAX_PAGES = 2
DELAY = 1

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8'
}


def fetch_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f'[WARN] Страница {url} вернула статус {resp.status_code}')
            return None
        return resp.text
    except requests.RequestException as e:
        print(f'[WARN] Ошибка при загрузке {url}: {e}')
        return None


def parse_articles_list(html):
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.find_all('article', class_='tm-articles-list__item')
    result = []

    for article in articles:
        try:
            title_tag = article.find('h2').find('a', class_='tm-title__link').find('span')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            time_tag = article.find('time')
            if not time_tag or not time_tag.has_attr('datetime'):
                continue
            raw_date = time_tag['datetime'].rstrip('Z')
            dt = datetime.fromisoformat(raw_date)
            date_str = dt.strftime('%Y-%m-%d')

            link_tag = article.find('a', class_='tm-title__link')
            if not link_tag or not link_tag.has_attr('href'):
                continue
            rel_link = link_tag['href']
            full_link = urljoin(BASE_URL, rel_link)

            result.append({
                'title': title,
                'date': date_str,
                'link': full_link
            })
        except (AttributeError, ValueError, KeyError) as e:
            print(f'[WARN] Ошибка при разборе preview: {e}')
            continue

    return result


def parse_full_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.select_one('.article-formatted-body.article-formatted-body_version-2')
    if body:
        return body.get_text(strip=True)
    return None


def check_keywords(text, keywords):
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False


def main():
    print('Запуск парсера habr.com')
    print(f'Ключевые слова: {KEYWORDS}')
    print('---')

    total_found = 0

    for page in range(1, MAX_PAGES + 1):
        if page == 1:
            url = START_URL
        else:
            url = f'{START_URL}page{page}/'

        print(f'[INFO] Обрабатываю страницу {page}: {url}')
        html = fetch_page(url)
        if not html:
            print(f'[WARN] Не удалось загрузить страницу {page}, пропускаю')
            continue

        articles = parse_articles_list(html)
        print(f'[INFO] Найдено статей на странице: {len(articles)}')

        for art in articles:
            print(f'  -> {art["title"][:50]}...')
            article_html = fetch_page(art['link'])
            if not article_html:
                print(f'  [WARN] Не удалось загрузить статью, пропускаю')
                continue

            full_text = parse_full_text(article_html)
            if not full_text:
                print(f'  [WARN] Не удалось извлечь текст статьи')
                continue

            if check_keywords(full_text, KEYWORDS):
                print(f'{art["date"]} | {art["title"]} | {art["link"]}')
                total_found += 1
            else:
                print(f'  [SKIP] Ключевые слова не найдены')

            time.sleep(DELAY)

    if total_found == 0:
        print('Совпадений не найдено.')
    else:
        print(f'---\nВсего найдено статей с совпадениями: {total_found}')


if __name__ == '__main__':
    main()