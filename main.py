import os.path

from bs4 import BeautifulSoup

import config


session = config.session
cookies = config.cookies
headers = config.headers
headers_post = config.headers_post
url_search = "https://www.steamgifts.com/giveaways/search"
wishlisted_page_file = "wishlist_page.html"
wishlisted_dir = "./wishlisted/"
params_wishlist = {
    'type': 'wishlist',
}
data_post = {
    'xsrf_token': 'aa86d08e9b956246197a9c5ff6bbfbe9',  # There is on the game page name: 'xsrf_token'
    'do': 'entry_insert',
    'code': 'zM6WM',  # Code there is in link to the game page
}


def get_page(url, params):
    response = session.get(url, headers=headers, cookies=cookies, params=params)
    return response


def save_response(response, file_name, directory="./"):
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open(f"{directory}{file_name}", "wb") as file:
        file.write(response)


def try_get_wishlisted_page():
    try:
        with open(f"{wishlisted_dir}{wishlisted_page_file}", "r") as file:
            response = file.read()
    except IOError:
        response = get_page(url_search, params_wishlist)
        if response.status_code == 200:
            save_response(response.content, wishlisted_page_file, wishlisted_dir)
    return response


def get_wish_list(soup):

    return ["link"]


def main():
    wish_list_page = try_get_wishlisted_page()
    soup = BeautifulSoup(wish_list_page)
    current_point_dom = soup.find("span", class_="nav__points")
    if current_point_dom:
        current_point = int(current_point_dom.text)
    wish_list = get_wish_list(soup)


if __name__ == '__main__':
    main()
