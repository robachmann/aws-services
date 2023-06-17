import json

import requests


def obj_dict(obj):
    return obj.__dict__


class Service:
    name: str
    product_name: str
    category: str
    launch_date: str
    summary: str
    url: str

    def __init__(self, name, product_name, category, date, summary, url):
        self.id = name.replace(" ", "") \
            .replace("-", "") \
            .lower() \
            .replace("amazon", "") \
            .replace("aws", "")
        self.name = name
        self.product_name = product_name
        self.category = category
        self.date = date
        self.summary = summary
        self.url = url


response = requests.get(
    'https://aws.amazon.com/api/dirs/items/search?item.directoryId=aws-products&sort_by=item.additionalFields.productCategory&sort_order=asc&size=1500&item.locale=en_US&tags.id=aws-products%23type%23service&tags.id=!aws-products%23type%23variant')

json_dict = response.json()
all_services = []
for json_obj in json_dict['items']:
    item = json_obj['item']
    service_name = item.get('name')
    additional_fields = item.get('additionalFields')
    service_product_name = additional_fields.get('productName')
    service_category = additional_fields.get('productCategory')
    service_launch_date = additional_fields.get('launchDate')
    service_summary = additional_fields.get('productSummary').replace("\r", "") \
        .replace("\n", "").replace("<p>", "").replace("</p>", "")
    service_url = additional_fields.get('productUrl').removesuffix("?did=ap_card&trk=ap_card")
    service = Service(service_name, service_product_name, service_category,
                      service_launch_date, service_summary, service_url)
    all_services.append(service)

    # json_string = json.dumps(all_services)
json_string = json.dumps([ob.__dict__ for ob in all_services])
print(json_string)
