from bs4 import BeautifulSoup, Comment
import requests
from pymongo import MongoClient
import time

# Create Mongo connection objects; a separate collection for each website 
client = MongoClient()
database = client['hockey_stats']
nhl_mongo_connect = database['nhl']
espn_mongo_connect = database['espn']
hockeyref_mongo_connect = database['hockeyref']


def scrape(url, stall, site='nhl'):
    """Scrape a given site and store data.

    The function takes a given URL and scrapes the site for 
    pre-determined html elements. Then BeautifulSoup is used for
    preliminary parsing before the elements are formatted and stored
    in a mongo database.

    Parameters
    ----------
    url: str
        The http website to be scraped

    stall: int
        An integer that represents the number of seconds
        between website get requests
    
    site: str
        An indicator used in other functions to easily
        identify the URL domain for particular handling

    """
    
    #Use requests to get and create website object
    try:
        website = requests.get(str(url))
    except:
        print("Requests error with url")
    
    #Append request notes to a log file for reference and diagnosis
    with open('scrape_records.log', 'a+') as log:
        log.write(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        log.write('URL: {}, Status: {}\n'.format(url,website.status_code))

    #Call the relevant site parsing function
    if site == 'nhl':
        try:
            parsed_site = nhl_parser(website, url)
        except:
            print("Parse error with nhl.com url")
    elif site == 'espn':
        try:
            parsed_site = espn_parser(website, url)
        except:
            print("Parse error with espn.com url")
    else:
        try:
            parsed_site = hockeyref_parser(website, url)
        except:
            print("Parse error with hockey-reference.com url")
    
    #Store parsed data object using relevant mongo connection
    try:
        if site == 'nhl':
            store(parsed_site, 'nhl')
            print("URL data successfully stored in database.")
        elif site == 'espn':
            store(parsed_site, 'espn')
            print("URL data successfully stored in database.")
        else:
            store(parsed_site, 'hockeyref')
            print('URL data successfully stored in database.')
    except:
        print("Store error with url")
    
    #Pause in scraping
    time.sleep(stall)
    pass

def nhl_parser(website, url):
    """Parse website and create data object.

    Parameters
    ----------
    website: response object
        Generated by the get request in the scrape() function
    
    url: str
        Used to help identify where the data is from once stored

    Returns
    -------
    parsed_site: list
        A list of dictionaries containing single key-value pairs
        that represent a table element and the site they were 
        taken from

    """

    #Parse site and find relevant elements
    nhl_soup = BeautifulSoup(website.text, 'html.parser')
    nhl_tbodies = nhl_soup.find_all('tbody')

    #Store formatted elements into a list of dictionaries
    parsed_site = [{str(ind).replace('.', '_'): ''.join(str(val).strip('[').strip(']'))} \
        for ind, val in enumerate([obj.find_all('td') for obj in nhl_tbodies])]
    
    return parsed_site

def espn_parser(website, url):
    """Parse website and create data object.

    Parameters
    ----------
    website: response object
        Generated by the get request in the scrape() function
    
    url: str
        Used to help identify where the data is from once stored

    Returns
    -------
    parsed_site: list
        A list of dictionaries containing single key-value pairs
        that represent a table element and the site they were 
        taken from

    """

    #Parse site and find relevant elements
    espn_soup = BeautifulSoup(website.text, 'html.parser')
    espn_tbodies = espn_soup.find_all('tbody', class_='Table2__tbody')

    #Store formatted elements into a list of dictionaries
    parsed_site = [{str(url).replace('.', '_'): ''.join(str(val).strip('[').strip(']'))} \
       if val != [] else {str(url).replace('.', '_'): 'no value'} \
            for ind, val in enumerate([obj.find_all('td') for obj in espn_tbodies])]
    
    return parsed_site

def hockeyref_parser(website, url):
    """Parse website and create data object.

    Parameters
    ----------
    website: response object
        Generated by the get request in the scrape() function
    
    url: str
        Used to help identify where the data is from once stored

    Returns
    -------
    parsed_site: list
        A list of dictionaries containing single key-value pairs
        that represent a table element and the site they were 
        taken from

    """
    
    #Parse site and find relevant elements
    soup = BeautifulSoup(website.text, 'lxml')
    table_soup = soup.find('div', {'id':'all_stats'})


    table_lists = []
    for comment in table_soup.find_all(string=lambda text:isinstance(text,Comment)):
        data = BeautifulSoup(comment,"lxml")
        for items in data.select("table.stats_table tr"):
            tds = [item.get_text(strip=True) for item in items.select("th,td")]
            table_lists.append(tds)

    #Store formatted elements into a list of dictionaries
    parsed_site = [{str(url).replace('.', '_'): ', '.join(lst)} for lst in table_lists]
    
    return parsed_site

def store(parsed_site, site):
    """Insert data object into mongo database"""

    if site == 'nhl':
        nhl_mongo_connect.insert_many(parsed_site)
    elif site == 'espn':
        espn_mongo_connect.insert_many(parsed_site)
    else:
        hockeyref_mongo_connect.insert_many(parsed_site)
    pass

if __name__ == '__main__':
    #rounds = ['2', '3', '4', '5', '6', '7']
    
    # for i in rounds:
    #     scrape('http://www.nhl.com/ice/draftsearch.htm?year=&team=&position=&round=' + i, 20, 'nhl')
    
    # teams = ['buf', 'car', 'mtl', 'ott', 'ari', 'det', 'van', 'chi', 'nyr', 'edm', 'nyi', 'dal',\
    #      'phi', 'fla', 'col', 'njd', 'cbj', 'lak', 'sjs', 'ana', 'min', 'stl', 'tor', 'wsh', 'bos',\
    #     'tbl', 'nsh', 'wpg', 'pit', 'cgy', 'vgk']
    # seasons = ['1', '2', '3']
    # years = ['2003', '2004', '2003', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', \
    #     '2013', '2014', '2015', '2016', '2017', '2018', '2019']
    
    # for i in teams:
    #     for k in years:
    #         for j in seasons:
    #             scrape('http://www.espn.com/nhl/team/schedule/_/name/{}/season/{}/seasontype/{}'.format(i,k,j),\
    #                 15, 'espn')

    for i in range(1963, 2020):
        scrape('https://www.hockey-reference.com/leagues/NHL_{}.html'.format(str(i)),15, site='hockeyref')
