import os.path
from parsel import Selector
import httpx
import requests

# establish our HTTP2 client with browser-like headers
session2 = httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
    http2=True,
    follow_redirects=True,
)

def parse_product(response: httpx.Response) -> dict:
    """Parse Ebay's product listing page for core product data"""
    sel = Selector(response.text)
    # define helper functions that chain the extraction process
    css_join = lambda css: "".join(sel.css(css).getall()).strip()  # join all CSS selected elements
    css = lambda css: sel.css(css).get(
        "").strip()  # take first CSS selected element and strip of leading/trailing spaces

    item = {}
    item["url"] = css('link[rel="canonical"]::attr(href)')
    item["id"] = item["url"].split("/itm/")[1].split("?")[0]  # we can take ID from the URL
    # item["id"] = item["url"].split("/itm/")[1]
    item["price"] = css('.x-price-primary>span::text')
    item["name"] = css_join("h1 span::text")
    item["seller_name"] = css_join("[data-testid=str-title] a ::text")
    item["seller_url"] = css("[data-testid=str-title] a::attr(href)").split("?")[0]
    item["photos"] = sel.css('.ux-image-filmstrip-carousel-item.image img::attr("src")').getall()  # carousel images
    item["photos"].extend(sel.css('.ux-image-carousel-item.image img::attr("src")').getall())  # main image
    # description is an iframe (independant page). We can keep it as an URL or scrape it later.
    item["description_url"] = css("div.d-item-description iframe::attr(src)")
    if not item["description_url"]:
        item["description_url"] = css("div#desc_div iframe::attr(src)")
    # feature details from the description table:
    feature_table = sel.css("div.ux-layout-section--features")
    features = {}
    for ft_label in feature_table.css(".ux-labels-values__labels"):
        # iterate through each label of the table and select first sibling for value:
        label = "".join(ft_label.css(".ux-textspans::text").getall()).strip(":\n ")
        ft_value = ft_label.xpath("following-sibling::div[1]")
        value = "".join(ft_value.css(".ux-textspans::text").getall()).strip()
        features[label] = value
    item["features"] = features
    # get additional photos
    additional_photos = []
    additional_photos = sel.css('.image-treatment>img::attr("src")').getall()
    extend_filename = ""
    filter_additional_photos_list = []
    if len(additional_photos) > 0:
        if str(additional_photos).lower().__contains__('.jpg'):
            extend_filename = ".jpg"
        if str(additional_photos).lower().__contains__('.png'):
            print(item["id"] + ":this is png image")
            extend_filename = ".png"

        for one_url in additional_photos:
            if one_url.__contains__('.webp'):
                last_index = one_url.rfind('/')
                pre_file_name = one_url[0:last_index + 1]
                # print(pre_file_name)
                if extend_filename == "":
                    extend_filename = ".png"
                file_name = "s-l1600" + extend_filename
                filter_additional_photos_list.append(pre_file_name + file_name)
    # the first item is same as the last one in additional_photos, it will not be included.
    item["additional_photos"] = filter_additional_photos_list[0:len(filter_additional_photos_list) - 1]

    return item


def get_all_products_detail(product_list):
    details_list = []

    for one in product_list:
        print(one['url'])
        response = session2.get(one['url'])
        item = parse_product(response)
        print(item["id"])
        # print(item["name"])
        # print(item["description_url"])
        print(str(item["additional_photos"]))
        if len(item["additional_photos"]) > 0:
            details_list.append(item)
    return details_list


def get_all_images(products_details):
    base_dir = "C:\\Users\\86131\\Desktop\\ebaydata\\images\\"
    base_dir_glass = "C:\\Users\\86131\\Desktop\\ebaydata\\images_glass\\"

    images_list = []

    for one_detail in products_details:
        # get product description
        # detail_resp = session2.get(one_detail["description_url"])
        # sel = Selector(detail_resp.text)
        print("------------------")
        print(one_detail["url"])
        # print(one_detail["name"])
        # print(desc)

        additional_img_count = 0
        for one_img_url in one_detail["additional_photos"]:
            print(one_img_url)

            item = {}
            item["item_url"] = one_detail["url"]
            item["image_text"] = one_detail["name"]
            item["img_url"] = one_img_url
            # item["desc"] = sel.css(".x-item-description-child>div::text").getall()
            # if len(item["desc"]) == 0:
            #     item["text"] = item["name"] + "."
            # else:
            #     text_str = str(item["name"] + ".")
            #     text_str = text_str.join([str(temp_desc) for temp_desc in item["desc"]])
            #     item["text"] = text_str

            dot_index = str(one_img_url).rfind(".")
            print("additional_img_count:" + str(additional_img_count))
            new_file_name = one_detail["id"] + "_" + str(additional_img_count) + str(one_img_url)[dot_index:]
            full_new_file = base_dir_glass + new_file_name
            item["image_name"] = new_file_name

            # local file name list in base image folder for checking if file exists
            porcelain_insulator_img_file_list = os.listdir(base_dir)
            glass_insulator_img_file_list = os.listdir(base_dir_glass)

            # check if the image exists
            if porcelain_insulator_img_file_list.count(new_file_name) > 0 or not glass_insulator_img_file_list.count(
                    new_file_name) <= 0:
                print(new_file_name + " exists.")
            else:
                local_file = open(full_new_file, 'wb')
                resp = requests.get(one_img_url, stream=True, verify=True, timeout=60)
                local_file.write(resp.content)
                local_file.close()

            # if not os.path.exists(full_new_file):
            #     local_file = open(full_new_file, 'wb')
            #     resp = requests.get(one_img_url, stream=True, verify=True, timeout=60)
            #     local_file.write(resp.content)
            #     local_file.close()
            # else:
            #     print(full_new_file + " exists.")

            print("item before append:" + str(item))
            images_list.append(item)
            additional_img_count = additional_img_count + 1

    return images_list
