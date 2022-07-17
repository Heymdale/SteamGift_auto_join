""" This file need to fill and rename to config.py"""
import requests


# Need to work with your account.
# To get it in Chrome browser you need to open developer tools, choose "Network",
# open or reload steamgift.com, click right mouse button on steamgift.com in left column,
# choose copy as curl (bash), after that use online converter (for example curlconverter.com)
# to convert params in python syntax.
cookies = {}

# You may use your own headers, it will be right.
headers = {
    'authority': 'www.steamgifts.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'referer': 'https://www.steamgifts.com/giveaways/search?type=wishlist',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="103", "Google Chrome";v="103"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
}

headers_post = {
    'authority': 'www.steamgifts.com',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://www.steamgifts.com',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="103", "Google Chrome";v="103"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

session = requests.Session()


def main():
    pass


if __name__ == "__main__":
    main()
