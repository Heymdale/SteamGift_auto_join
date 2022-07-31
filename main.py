"""
Script parse steamgift.com
at  first it try to enter the pinned giveaways,
later - your wishlisted giveaway through all pages
and finally if your account points is more than threshold, script try to enter giveaway through not wishlisted pages

ga - giveaway
gas - giveaways
"""

import os.path
import re
import json
from pathlib import Path

from loguru import logger
from bs4 import BeautifulSoup

import config

session = config.session
cookies = config.cookies
headers = config.headers
headers_post = config.headers_post
url_search = "https://www.steamgifts.com/giveaways/search"
url_enter_the_ga = "https://www.steamgifts.com/ajax.php"
pages_dir = "pages/"
jsons_dir = "jsons/"
results_dir = "./results/"
save_json_for_debug = False
save_html_for_debug = False
# Loguru debug level
debug_level = "WARNING"

logger.add(
    f"{results_dir}debug.log",
    format="{time} {level} {message}",
    rotation="5MB",
    compression="zip",
    level=debug_level,
)


class DataPost:
    xsrf_token = ""

    def __init__(self, game_code):
        self.do = 'entry_insert',
        self.code = game_code  # Code there is in link to the game page

    def get_data_request(self):
        data = {
            "xsrf_token": self.xsrf_token,
            "do": self.do,
            "code": self.code
        }
        return data


# Solution from stackoverflow, i need to know how it works and what is unlink()
def delete_dir_recursively(directory):
    directory = Path(directory)
    for item in directory.iterdir():
        if item.is_dir():
            os.rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


def delete_previous_temp_dirs(json_directory=jsons_dir, html_directory=pages_dir, main_dir=results_dir):
    result_json_directory = f"{main_dir}{json_directory}"
    result_html_directory = f"{main_dir}{html_directory}"
    if os.path.exists(result_json_directory):
        delete_dir_recursively(result_json_directory)
    if os.path.exists(result_html_directory):
        delete_dir_recursively(result_html_directory)


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


def try_get_page(page: int, wishlist: bool):
    params = {"page": page}
    if wishlist:
        params["type"] = "wishlist"
    response = get_page(url_search, params)
    if response.status_code == 200:
        page_name = return_page_name(page, wishlist)
        page_file = f"page{page_name}.html"
        save_response(response.content, page_file, pages_dir)
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
        if text.find("P") != -1:
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


def parse_is_whitelist(ga: BeautifulSoup):
    element = ga.find("i", class_="fa-heart")
    whitelist = bool(element)
    return whitelist


def parse_is_need_steam_groups(ga: BeautifulSoup):
    element = ga.find("a", class_="giveaway__column--group")
    steam_groups = bool(element)
    return steam_groups


def parse_is_entered(ga: BeautifulSoup):
    element = ga.select("div.giveaway__row-inner-wrap.is-faded")
    entered = bool(element)
    return entered


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
        "whitelist": parse_is_whitelist(ga),
        # You need to be member at least one of the steam groups which sponsored it GA
        "steam_groups": parse_is_need_steam_groups(ga),
        "entered": entered,
    }
    return info_dict


def parse_gas_div(gas_div: BeautifulSoup):
    if gas_div is None:
        return []
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
        logger.info(response.text)
        parsed_json = json.loads(response.content)
        points = int(parsed_json["points"])
        return points


def enter_gas(gas_list, current_points, wishlist: bool):
    for ga in gas_list:
        if current_points >= ga["price"]:
            code = ga["game_code"]
            data = DataPost(code).get_data_request()
            points_from_response = enter_the_ga(data)
            if points_from_response is not None:
                current_points = points_from_response
                if not wishlist and current_points < 200:
                    logger.info(f"Points: {current_points}")
                    return current_points
            logger.info(f"Points: {current_points}")
    return current_points


def return_page_name(page, wishlist):
    return f"{page}{'w' if wishlist else ''}"


def find_next_page_link(soup: BeautifulSoup):
    find = soup.find("div", class_="pagination").find("span", text="Next")
    is_find = bool(find)
    return is_find


def parse_page(page: int, is_wishlist: bool):
    list_page_content = try_get_page(page, is_wishlist)
    soup = BeautifulSoup(list_page_content, "lxml")
    if DataPost.xsrf_token == "":
        xsrf_token_el = soup.select("div.nav__row.is-clickable.js__logout")[0]
        # I meet some troubles with find "input" name="xsrf_token", so i parse xsrf_token from another dom element.
        xsrf_token = xsrf_token_el["data-form"][21:]
        logger.info(f"xsrf_token = {xsrf_token}")
        DataPost.xsrf_token = xsrf_token
    current_points = 0
    current_points_dom = soup.find("span", class_="nav__points")
    if current_points_dom:
        current_points = int(current_points_dom.text)
        logger.info(f"Current points: {current_points}")
    page_name = return_page_name(page, is_wishlist)
    pinned_gas = get_pinned_list(soup)
    logger.info(f"Pinned giveaways: {pinned_gas}")
    if save_json_for_debug:
        save_json(pinned_gas, f"not_entered_pinned_gas_{page_name}.json", directory=jsons_dir)
    current_points = enter_gas(pinned_gas, current_points, wishlist=is_wishlist)
    not_pinned_gas = get_wished_list(soup)
    # If not wishlisted page, we will sort list. At this moment it sorted by remaining time,
    # in the code below list will sorted if needed be a member of the steam groups, if in the whitelist, by level,
    # after that by region restricted, but maybe will be more effective if list sort by some function of time start,
    # time remaining and entries.
    if not is_wishlist:
        not_pinned_gas.sort(key=lambda x: x["steam_groups"], reverse=True)
        not_pinned_gas.sort(key=lambda x: x["whitelist"], reverse=True)
        not_pinned_gas.sort(key=lambda x: x["level"], reverse=True)
        not_pinned_gas.sort(key=lambda x: x["region_restricted"], reverse=True)
    logger.info(f"Not pinned giveaways (wishlisted={is_wishlist}): {not_pinned_gas}")
    if save_json_for_debug:
        save_json(not_pinned_gas, f"not_entered_gas_{page_name}.json", directory=jsons_dir)
    current_points = enter_gas(not_pinned_gas, current_points, wishlist=is_wishlist)
    is_next_page_exist = find_next_page_link(soup)
    return current_points, is_next_page_exist


@logger.catch()
def main():
    delete_previous_temp_dirs()
    # Wishlist crawl
    page = 1
    while True:
        result = parse_page(page, is_wishlist=True)
        current_points = result[0]
        is_next_page_exist = result[1]
        if not is_next_page_exist or current_points == 0:
            break
        page += 1

    # If current points is over 200, crawl common pages
    page = 1
    while current_points >= 200:
        result = parse_page(page, is_wishlist=False)
        current_points = result[0]
        is_next_page_exist = result[1]
        if not is_next_page_exist or current_points < 0:
            break
        page += 1


if __name__ == '__main__':
    main()
