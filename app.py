import jwt
from flask import Flask, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from usp.tree import sitemap_tree_for_homepage

app = Flask(__name__)

JWT_SECRET = "adsfasdgasdg"

def url_scrapper(website_url): 
    raw_url_list = url_raw_scrapper(website_url)
    xml_url_list = url_xml_scrapper(website_url)
    raw_url_list.extend(xml_url_list)
    all_url_set = set(raw_url_list)
    return list(all_url_set)

def url_raw_scrapper(website_url):
    page = requests.get(website_url, verify=False)
    soup = BeautifulSoup(page.content, "html.parser")
    links = set([website_url])
    for link in soup.find_all("a", href=True):
        href = link.get("href")
        full_url = urljoin(website_url, href)
        print(full_url)
        if full_url.startswith(website_url):
            if full_url.endswith('/'):
                full_url = full_url[:-1]
            if "." in full_url.split("/")[-1] and full_url.split("/")[-1] != website_url.split("/")[-1]:
                continue
            links.add(full_url)
    return list(links)

def url_xml_scrapper(website_url):
    urls_xml = set()
    tree = sitemap_tree_for_homepage(website_url)
    for page in tree.all_pages():
        full_url = page.url
        if full_url.startswith(website_url):
            if full_url.endswith('/'):
                full_url = full_url[:-1]
            if "." in full_url.split("/")[-1] and full_url.split("/")[-1] != website_url.split("/")[-1]:
                continue
            urls_xml.add(full_url)
    return urls_xml

def scrap_url(url):
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')
    for script in soup(['script', 'style', 'header', 'footer']):
        script.extract()
    text = soup.get_text(separator=' ')
    text = ' '.join(text.split())
    count = 0
    for i in range(0, len(text)):  
        if(text[i] != ' '):  
            count += 1
    return url, text, count

def authorize_token(token, secret_key):
    try:
        payload = jwt.decode(token, secret_key)
        print("Token authorized successfully.")
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired.")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token.")
        return None

def encrypt_data(payload, secretkey):
    token = jwt.encode(payload, secretkey)
    return token

@app.route('/', methods=['GET'])
def scrap_website():
    print("$$$$$$$$$$$$$$$$$$$$$$$")
    URL_TOKEN = request.args.get('url_token')
    print(URL_TOKEN)
    decoded_payload = authorize_token(URL_TOKEN, JWT_SECRET)
    print(decoded_payload)
    website_url = decoded_payload["url"]
    all_url_list = url_scrapper(website_url)
    user_data_json = dict()
    user_data_json["user_id"] = decoded_payload["user_id"]
    user_data_json["scrapped_data"] = dict()
    for sub_url in all_url_list:
        url, text, chars = scrap_url(sub_url)
        user_data_json["scrapped_data"][url] = [text, chars]
    api_data_token = encrypt_data(user_data_json, JWT_SECRET)
    return api_data_token

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)