from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import sqlite3
import calendar

#Looking for artist, genre, label, year of release, reviewer, review score, review date, review_length, best_new_music

MONTH_TO_INDEX = dict((month, str(index)) for index, month in enumerate(calendar.month_abbr) if month)

def create_db(db_file_path):
    db_connection = sqlite3.connect(db_file_path)
    db_cursor = db_connection.cursor()

    create_table_command = """CREATE TABLE IF NOT EXISTS reviews(
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
        PRIMARY KEY(album_name, artist, release_year)
    )"""
    db_cursor.execute(create_table_command)
    return db_cursor

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
        review_word_count= sum(map(review_divs, lambda x: sum(x.get_text().split(' '))))
    except :
        review_word_count= 'NULL'
    return review_word_count 

def get_album_data(album_soup):
    data = []
    funcs = [get_album_name, get_album_artist, get_album_genre, get_album_label, get_album_yor, get_album_score, get_album_bnm,
            get_album_reviewer, get_album_review_date, get_album_review_length]
    for func in funcs:
        if func == get_album_review_date:
            data.extend(func(album_soup))
        else :
            data.append(func(album_soup))
    return data

if __name__=='__main__':
    db_file_path = "pitchfork_album_reviews.db"
    db_cursor = create_db(db_file_path)

    pitchfork_albums_review_url = "https://pitchfork.com/reviews/albums/?page={}"
    pager = 1
    albums_data = []
    while(True):
        page_url = pitchfork_albums_review_url.format(str(pager))
        try:
            page_html = urlopen(page_url).read().decode("utf-8")
        except:
            break
        page_soup = BeautifulSoup(page_html, 'html.parser')
        album_urls = get_album_urls(page_soup)
        for album_url in album_urls:
            try:
                album_html = urlopen(album_url).read().decode("utf-8")
            except:
                continue
            album_soup = BeautifulSoup(album_html, 'html.parser')
            album_data = get_album_data(album_soup)
            albums_data.append(album_data)
        insert_albums_command = """INSERT INTO reviews VALUES """
        commands = ','.join(["({})".format(','.join(album_data)) for album_data in albums_data])
        final_command = insert_albums_command + commands
        db_cursor.execute(final_command)
        pager+=1