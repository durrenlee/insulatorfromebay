# to create json file based on filtered images
import json
import os.path

filtered_images_dir = "C:\\Users\\86131\\Desktop\\ebaydata\\filteredimgs\\"
ebay_data_base_dir = "C:\\Users\\86131\\Desktop\\ebaydata\\"
image_info_json_files = ["images_info.json", "images_info_2.json", "images_info_3.json",
                         "images_info_4.json", "images_info_5.json", "images_info_6.json",
                         "images_info_glass.json", "images_info_glass_2.json"]


def create_filtered_images_json():
    final_filtered_list = []
    if os.path.exists(ebay_data_base_dir) and os.path.exists(filtered_images_dir):
        # load each json file
        json_list = []
        for json_file in image_info_json_files:
            with open(ebay_data_base_dir + json_file, "rb") as file:
                json_list.append(json.load(file))

        print("json list size:" + str(len(json_list)))
        # iterating each filtered image name to look up json code piece
        if len(json_list) > 0:
            filtered_images_names = os.listdir(filtered_images_dir)
            for img_name in filtered_images_names:
                is_img_name_exist = 0

                for each_json in json_list:
                    # iterating each json file
                    for each_image_code in each_json:
                        if each_image_code["image_name"] == img_name:
                            is_img_name_exist = 1
                            # check if same item exists
                            is_exist = 0
                            for each_exist_item in final_filtered_list:
                                if each_exist_item["image_name"] == each_image_code["image_name"]:
                                    is_exist = 1
                                    break

                            if is_exist == 0:
                                item = {}
                                item["item_url"] = each_image_code["item_url"]
                                item["image_text"] = each_image_code["image_text"]
                                item["img_url"] = each_image_code["img_url"]
                                item["image_name"] = each_image_code["image_name"]
                                final_filtered_list.append(item)
                                break

                if is_img_name_exist == 0:
                    print(img_name + " not in json files.")
    return final_filtered_list


final_list = create_filtered_images_json()
if len(final_list) > 0:
    with open(ebay_data_base_dir + "images.json", "w") as f:
        json.dump(final_list, f)
