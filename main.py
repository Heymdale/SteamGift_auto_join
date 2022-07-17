import os.path
import re
import json

from bs4 import BeautifulSoup

import config

session = config.session
cookies = config.cookies
headers = config.headers
headers_post = config.headers_post
url_search = "https://www.steamgifts.com/giveaways/search"
url_enter_the_ga = "https://www.steamgifts.com/ajax.php"
wishlisted_page_file = "wishlist_page.html"
wishlisted_dir = "wishlisted/"
results_dir = "./results/"
params_wishlist = {
    'type': 'wishlist',
}


class DataPost:

    def __init__(self, xsrf_token, game_code):
        self.xsrf_token = xsrf_token,
        self.do = 'entry_insert',
        self.code = game_code  # Code there is in link to the game page

    def get_data_request(self):
        data = {
            "xsrf_token": self.xsrf_token,
            "do": self.do,
            "code": self.code
        }
        return data


def get_page(url, params):
    response = session.get(url, headers=headers, cookies=cookies, params=params)
    return response


def check_dir(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)


def save_response(response, file_name, directory="./", main_dir=results_dir):
    result_directory = f"{main_dir}{directory}"
    check_dir(result_directory)
    with open(f"{result_directory}{file_name}", "wb") as file:
        file.write(response)


def save_json(data, file_name, directory="./", main_dir=results_dir):
    result_directory = f"{main_dir}{directory}"
    check_dir(result_directory)
    with open(f"{result_directory}{file_name}", "w") as file:
        json.dump(data, file, indent=4)


def try_get_wishlisted_page():
    # try:
    #     with open(f"{results_dir}{wishlisted_dir}{wishlisted_page_file}", "r") as file:
    #         response = file.read()
    # except IOError:
    response = get_page(url_search, params_wishlist)
    if response.status_code == 200:
        save_response(response.content, wishlisted_page_file, wishlisted_dir)
    response = response.content
    return response


def parse_name(ga: BeautifulSoup):
    name = ga.find("a", class_="giveaway__heading__name").text
    return name


def text_to_int(text):
    int_text = re.sub(r"\D", "", text)
    return int(int_text)


def parse_copies(ga: BeautifulSoup):
    copies = 1
    headers_spans = ga.find_all("span", class_="giveaway__heading__thin")
    for el in headers_spans:
        text = el.text
        if text.find("Copies"):
            copies = text_to_int(text)
    return copies


def parse_price(ga: BeautifulSoup):
    headers_spans = ga.find_all("span", class_="giveaway__heading__thin")
    for el in headers_spans:
        text = el.text
        if text.find("P"):
            price = text_to_int(text)
            return price


def parse_entries(ga: BeautifulSoup):
    entries_el = ga.find("div", class_="giveaway__links").find("span")
    entries = text_to_int(entries_el.text)
    return entries


def parse_game_code(ga: BeautifulSoup):
    link_el = ga.find("a", class_="giveaway__heading__name")
    link = link_el["href"]
    game_code = link[10:15]
    return game_code


def parse_finish_timestamp(ga: BeautifulSoup):
    ts_el = ga.find("div", class_="giveaway__columns").find("span")
    if ts_el:
        ts = ts_el["data-timestamp"]
        return ts


def parse_added_timestamp(ga: BeautifulSoup):
    ts_el = ga.find("div", class_="giveaway__column--width-fill").find("span")
    if ts_el:
        ts = ts_el["data-timestamp"]
        return ts


def parse_level(ga: BeautifulSoup):
    level = 0
    level_el = ga.select("div.giveaway__column--contributor-level.giveaway__column--contributor-level--positive")
    if level_el:
        level_text = level_el[0].text
        level = text_to_int(level_text)
    return level


def parse_is_region_restrict(ga: BeautifulSoup):
    element = ga.find("i", class_="fa-globe")
    restricted = bool(element)
    return restricted


def parse_is_entered(ga: BeautifulSoup):
    element = ga.select("div.giveaway__row-inner-wrap.is-faded")
    entered = bool(element)
    return entered


# ga - giveaway
def parse_ga(ga: BeautifulSoup):
    entered = parse_is_entered(ga)
    if entered:
        return {"entered": True}
    info_dict = {
        "name": parse_name(ga),
        "copies": parse_copies(ga),
        "price": parse_price(ga),
        "entries": parse_entries(ga),
        "game_code": parse_game_code(ga),
        "finish_timestamp": parse_finish_timestamp(ga),
        "added_timestamp": parse_added_timestamp(ga),
        "region_restricted": parse_is_region_restrict(ga),
        "level": parse_level(ga),
        "entered": entered,
    }
    return info_dict


def parse_gas_div(gas_div: BeautifulSoup):
    elements = gas_div.find_all("div", class_="giveaway__row-outer-wrap")
    gas_list = [parse_ga(ga) for ga in elements if not parse_ga(ga)["entered"]]
    return gas_list


def get_pinned_list(soup):
    pinned_gas_el = soup.find("div", class_="pinned-giveaways__inner-wrap")
    pinned_list = parse_gas_div(pinned_gas_el)
    return pinned_list


def get_wished_list(soup):
    header_before = soup.find("div", class_="page__heading")
    wished_gas_el = header_before.find_next_sibling("div")
    wished_list = parse_gas_div(wished_gas_el)
    return wished_list


def enter_the_ga(data):
    response = session.post(url_enter_the_ga, headers=headers_post, data=data)
    if response.status_code == 200 and not response.text == "":
        print(response.text)
        parsed_json = json.loads(response.content)
        points = int(parsed_json["points"])
        return points


def enter_gas(gas_list, current_points):
    for ga in gas_list:
       if current_points >= ga["price"]:
            token = config.xsrf_token
            code = ga["game_code"]
            data = DataPost(token, code).get_data_request()
            points_from_response = enter_the_ga(data)
            if not points_from_response is None:
                current_points = points_from_response
            print(f"Points: {current_points}")
    return current_points


def main():
    wish_list_page = try_get_wishlisted_page()
    soup = BeautifulSoup(wish_list_page, "lxml")
    current_points = 0
    current_points_dom = soup.find("span", class_="nav__points")
    if current_points_dom:
        current_points = int(current_points_dom.text)
        print(f"Current points: {current_points}")
    # gas - giveaways
    pinned_gas = get_pinned_list(soup)
    print(f"Pinned giveaways: {pinned_gas}")
    save_json(pinned_gas, "pinned.json")
    current_points = enter_gas(pinned_gas, current_points)
    wished_gas = get_wished_list(soup)
    print(f"Wished giveaways: {wished_gas}")
    save_json(wished_gas, "wished.json")
    current_points = enter_gas(wished_gas, current_points)


if __name__ == '__main__':
    main()
