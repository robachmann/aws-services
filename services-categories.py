import json

import requests

from services import Service


def obj_dict(obj):
    return obj.__dict__


response = requests.get(
    #    'https://aws.amazon.com/api/dirs/items/search?item.directoryId=aws-products&sort_by=item.additionalFields.productCategory&sort_order=asc&size=1500&item.locale=en_US&tags.id=aws-products%23type%23service&tags.id=!aws-products%23type%23variant')
    'https://aws.amazon.com/api/dirs/items/search?item.directoryId=aws-products&sort_by=item.additionalFields.productCategory&sort_order=asc&size=1500&item.locale=en_US')

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
    service = Service()

    service.id = service_name.replace(" ", "") \
        .replace("-", "") \
        .lower() \
        .replace("amazon", "") \
        .replace("aws", "")
    service.name = service_name
    service.product_name = service_product_name
    service.category = service_category
    service.date = service_launch_date
    service.summary = service_summary
    service.url = service_url

    all_services.append(service)

    # json_string = json.dumps(all_services)
json_string = json.dumps([ob.__dict__ for ob in all_services])
print(json_string)
