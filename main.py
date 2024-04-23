# last update: 2023-10-10
import asyncio
import math
import os.path

import httpx
from typing import TypedDict, List, Literal
from urllib.parse import urlencode

from parsel import Selector
from parse_product import get_all_products_detail
from parse_product import get_all_images
import json

session = httpx.AsyncClient(
    # for our HTTP headers we want to use a real browser's default headers to prevent being blocked
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
    # Enable HTTP2 version of the protocol to prevent being blocked
    http2=True,
    # enable automatic follow of redirects
    follow_redirects=True
)

# this is scrape result we'll receive
class ProductPreviewResult(TypedDict):
    """type hint for search scrape results for product preview data"""

    url: str  # url to full product page
    title: str
    price: str
    shipping: str
    list_date: str
    subtitles: List[str]
    condition: str
    photo: str  # image url
    rating: str
    rating_count: str


def parse_search(response: httpx.Response) -> List[ProductPreviewResult]:
    """parse ebay's search page for listing preview details"""
    previews = []
    # each listing has it's own HTML box where all of the data is contained
    sel = Selector(response.text)
    listing_boxes = sel.css(".srp-results li.s-item")
    for box in listing_boxes:
        # quick helpers to extract first element and all elements
        css = lambda css: box.css(css).get("").strip()
        css_all = lambda css: box.css(css).getall()
        previews.append(
            {
                "url": css("a.s-item__link::attr(href)").split("?")[0],
                "title": css(".s-item__title>span::text"),
                "price": css(".s-item__price::text"),
                "shipping": css(".s-item__shipping::text"),
                "list_date": css(".s-item__listingDate span::text"),
                "subtitles": css_all(".s-item__subtitle::text"),
                "condition": css(".s-item__subtitle .SECONDARY_INFO::text"),
                "photo": css(".s-item__image img::attr(src)"),
                "rating": css(".s-item__reviews .clipped::text"),
                "rating_count": css(".s-item__reviews-count span::text"),
            }
        )
    return previews


SORTING_MAP = {
    "best_match": 12,
    "ending_soonest": 1,
    "newly_listed": 10,
}

async def scrape_search(
    query,
    page,
    max_pages=1,
    category=0,
    items_per_page=240,
    sort: Literal["best_match", "ending_soonest", "newly_listed"] = "best_match",
) -> List[ProductPreviewResult]:
    """Scrape Ebay's search for product preview data for given"""

    def make_request(page):
        return "https://www.ebay.com/sch/i.html?" + urlencode(
            {
                "_nkw": query,
                "_sacat": category,
                "_ipg": items_per_page,
                "_sop": SORTING_MAP[sort],
                "_pgn": page,
            }
        )
        print('max_pages:' + str(max_pages))
        print('items_per_page:' + str(items_per_page))
        print('page:' + page)

    first_page = await session.get(make_request(page))
    results = parse_search(first_page)
    print('results length:' + str(len(results)))
    for one in results:
        print(one)

    if max_pages == 1:
        return results
    # find total amount of results for concurrent pagination
    # total_results = first_page.selector.css(".srp-controls__count-heading>span::text").get()
    # total_results = int(total_results.replace(",", ""))
    # total_pages = math.ceil(total_results / items_per_page)
    # if total_pages > max_pages:
    #     total_pages = max_pages
    # other_pages = [session.get(make_request(page=i)) for i in range(2, total_pages + 1)]
    # for response in asyncio.as_completed(other_pages):
    #     response = await response
    #     try:
    #         results.extend(parse_search(response))
    #     except Exception as e:
    #         print(f"failed to scrape search page {response.url}")
    return results

if __name__ == "__main__":
    product_list_path = "C:\\Users\\86131\\Desktop\\ebaydata\\products_glass_2.json"
    if not os.path.exists(product_list_path):
        print(product_list_path + " does not exist")
        # get products by search keyword
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        result = asyncio.run(scrape_search("glass insulator", 2))
        with open(product_list_path, 'w') as f:
            json.dump(result, f)

    # load data from json file
    products_details_list_path = "C:\\Users\\86131\\Desktop\\ebaydata\\products_details_glass_2.json"
    if not os.path.exists(products_details_list_path):
        with open(product_list_path, 'r') as f:
            product_list = json.load(f)
            # get ebay product details and save to json file
            product_details = get_all_products_detail(product_list)
            if len(product_details) > 0:
                with open(products_details_list_path, 'w') as f:
                    json.dump(product_details, f)

    # get images from ebay and create corresponding markings json
    images_info_list_path = "C:\\Users\\86131\\Desktop\\ebaydata\\images_info_glass_2.json"
    if not os.path.exists(images_info_list_path):
        with open(products_details_list_path, 'r') as f:
            products_details = json.load(f)
            products_images = get_all_images(products_details)
            if len(products_images) > 0:
                with open(images_info_list_path, 'w') as f:
                    json.dump(products_images, f)