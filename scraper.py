import re
import sqlite3
import calendar
import time
from bs4 import BeautifulSoup
from urllib.request import urlopen

MONTH_TO_INDEX = dict((month, str(index)) for index, month in enumerate(calendar.month_abbr) if month)

def create_db(db_file_path):
    db_connection = sqlite3.connect(db_file_path)
    db_cursor = db_connection.cursor()

    create_table_command = """CREATE TABLE IF NOT EXISTS reviews(
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        album_name TEXT,
        artist TEXT,
        genre TEXT,
        label TEXT,
        release_year INTEGER,
        score REAL,
        best_new_music BOOLEAN,
        reviewer_name TEXT,
        review_date_day INTEGER,
        review_date_month INTEGER,
        review_date_year INTEGER,
        review_length INTEGER,
        cover_url TEXT
    )"""
    db_cursor.execute(create_table_command)
    return db_connection, db_cursor

def get_album_urls(page_soup):
    anchors = page_soup.find_all('a', href=re.compile("/reviews/albums/.+"))
    album_urls = ["https://pitchfork.com" + anchor.get('href') for anchor in anchors]
    album_urls = list(set(album_urls))
    return album_urls

def get_album_name(album_soup):
    try : 
        name_div = album_soup.find('h1', attrs = {'data-testid' : "ContentHeaderHed"})
        name = name_div.get_text()
    except:
        name = 'NULL'
    return name

def get_album_score(album_soup):
    try:
        score_div = album_soup.find('div', class_="ScoreCircle-jAxRuP")
        score = score_div.get_text()
    except:
        score = 'NULL'
    return score

def get_album_bnm(album_soup):
    if album_soup.find('p', class_="BestNewMusicText-xXvIB") is None:
        bnm_boolean = 'FALSE'
    else :
        bnm_boolean = 'TRUE'
    return bnm_boolean

def get_album_artist(album_soup):
    try:
        artist_div = album_soup.find('div', class_="SplitScreenContentHeaderArtist-ftloCc")
        artist = artist_div.get_text()
    except:
        artist = 'NULL'
    return artist

def get_album_genre(album_soup):
    try : 
        genre_div = album_soup.find(lambda x: x.name == 'p' and 'genre:' in x.text.lower()).nextSibling
        genre = genre_div.get_text()
    except:
        genre = 'NULL'
    return genre

def get_album_label(album_soup):
    try : 
        label_div = album_soup.find(lambda x: x.name == 'p' and 'label:' in x.text.lower()).nextSibling
        label = label_div.get_text()
    except:
        label = 'NULL'
    return label

def get_album_yor(album_soup):
    try:
        year_of_release_div = album_soup.find('time', attrs={'data-testid':"SplitScreenContentHeaderReleaseYear"})
        year_of_release = year_of_release_div.get_text()
    except : 
        year_of_release = 'NULL'
    return year_of_release

def get_album_reviewer(album_soup):
    try: 
        reviewer_div = album_soup.find('span', class_="BylineName-kwmrLn")
        reviewer_name = reviewer_div.get_text().replace('By ', '')
    except:
        reviewer_name = 'NULL'
    return reviewer_name

def get_album_review_date(album_soup):
    try : 
        review_date_div = album_soup.find(lambda x: x.name == 'p' and 'reviewed:' in x.text.lower()).nextSibling
        review_date = review_date_div.get_text()
        month, day, year = review_date.replace(',', '').split(' ')
        month = MONTH_TO_INDEX[month[:3]]
    except:
        month, day, year = 'NULL', 'NULL', 'NULL'
    return [day, month, year]

def get_album_review_length(album_soup):
    try:
        review_divs = album_soup.find_all("div", class_="BodyWrapper-kufPGa cmVAut body body__container article__body")
        review_word_count = sum(map(lambda x: len(re.findall(r'\w+', x.get_text())), review_divs))
        review_word_count = str(review_word_count)
    except :
        review_word_count= 'NULL'
    return review_word_count 

def get_album_cover_url(album_soup):
    try : 
        cover_url_upper_div = album_soup.find('div', class_="SplitScreenContentHeaderLeadWrapper-jYfGAC lfiqNF")
        cover_url = cover_url_upper_div.find('img')['src']   
    except : 
        cover_url = 'NULL'
    return cover_url

def get_album_data(album_soup):
    data = []
    funcs = [get_album_name, get_album_artist, get_album_genre, get_album_label, get_album_yor, get_album_score, get_album_bnm,
            get_album_reviewer, get_album_review_date, get_album_review_length, get_album_cover_url]
    for func in funcs:
        if func == get_album_review_date:
            data.extend(func(album_soup))
        else :
            data.append(func(album_soup))
    return data

def format_for_sql(data):
    text_columns_indices = list(range(4)) + [7,12]
    for i in text_columns_indices: 
        if data[i] != "NULL":
            if "'" in data[i]:
                data[i] = data[i].replace("'", "''")
            data[i] = "'" + data[i] + "'"
    return data

if __name__=='__main__':

    # Initalizing database
    db_file_path = "pitchfork_album_reviews.db"
    db_connection, db_cursor = create_db(db_file_path)
    insert_command = """INSERT INTO reviews (album_name,artist, genre, label,release_year, score, best_new_music, reviewer_name, review_date_day, review_date_month, review_date_year, review_length, cover_url) VALUES """

    # Starting to scrape
    pitchfork_albums_review_url = "https://pitchfork.com/reviews/albums/?page={}"
    pager = 86
    n_reviews_counter = 0
    while(True):
        # Opening page, fetching html data
        page_url = pitchfork_albums_review_url.format(str(pager))
        try:
            time_i = time.time()
            page_html = urlopen(page_url).read().decode("utf-8")
            time_j = time.time()
            time_to_open_page = round((time_j - time_i)/1000, 3)
        except:
            print("Scraping stopped when tried to fetch page number {} html data. Link : {}.".format(pager, page_url))
            break

        print("Now processing page {}, which took {} seconds to open.".format(pager, round(time_to_open_page, 3)))

        # Parsing html
        page_soup = BeautifulSoup(page_html, 'html.parser')
        album_urls = get_album_urls(page_soup)
        for album_url in album_urls:
            try:
                time_i = time.time()
                album_html = urlopen(album_url).read().decode("utf-8")
                time_j = time.time()
                time_to_open_page = round((time_j - time_i)/1000, 3)
            except:
                continue
            album_soup = BeautifulSoup(album_html, 'html.parser')
            album_data = get_album_data(album_soup)
            album_data = format_for_sql(album_data)
            print("\tAlbum data retrieved from page {}, which took {} seconds to open.".format(album_url, time_to_open_page ))

            # Inserting data in database
            insert_values = "({})".format(','.join(album_data))
            final_command = insert_command + insert_values
            db_cursor.execute(final_command)
            db_connection.commit()

        # Printing status
        n_reviews_counter += len(album_urls)
        print('\nThe database now contains {} reviews.\n'.format(n_reviews_counter))
        pager+=1

    db_connection.close()