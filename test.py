import config
import main


def test():
    result = main.parse_page(6, wishlist=False)
    current_points = result[0]
    is_next_page_exist = result[1]



if __name__ == "__main__":
    test()