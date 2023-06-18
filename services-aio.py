import json

import boto3
import jsonpickle as jsonpickle
import requests

from services import Service

ssm = boto3.client('ssm')


def obj_dict(obj):
    return obj.__dict__


def get_all_services():
    paginator = ssm.get_paginator('get_parameters_by_path')

    response_iterator = paginator.paginate(
        Path="/aws/service/global-infrastructure/services"
    )

    parameters = []
    for page in response_iterator:
        for entry in page['Parameters']:
            parameters.append(entry['Value'])

    return parameters


def lookup_service_name(service_key):
    parameter = ssm.get_parameters_by_path(Path=f"/aws/service/global-infrastructure/services/{service_key}")

    service_name = 'unknown'
    service_url = 'unknown'
    if parameter is not None and len(parameter['Parameters']) > 0:
        service_name = parameter['Parameters'][0]['Value']
        if len(parameter['Parameters']) > 1:
            service_url = parameter['Parameters'][1]['Value']

    return service_name, service_url


def get_services_ssm() -> [Service]:
    all_services = get_all_services()

    service_list = []
    for service_key in all_services:
        service_name, service_url = lookup_service_name(service_key)
        service = Service()
        service.product_name = service_name
        service.id = service_key
        service.url = service_url.removesuffix("/")
        service_list.append(service)

    return service_list


def get_services_categories() -> [Service]:
    response = requests.get(
        'https://aws.amazon.com/api/dirs/items/search?item.directoryId=aws-products&sort_by=item.additionalFields.productCategory&sort_order=asc&size=1500&item.locale=en_US&tags.id=aws-products%23type%23service&tags.id=!aws-products%23type%23variant')
    # 'https://aws.amazon.com/api/dirs/items/search?item.directoryId=aws-products&sort_by=item.additionalFields.productCategory&sort_order=asc&size=1500&item.locale=en_US')

    json_dict = response.json()
    all_services = []
    for json_obj in json_dict['items']:
        item = json_obj['item']
        service_name = item.get('name')
        additional_fields = item.get('additionalFields')
        service_product_name = additional_fields.get('productName').replace(" (Preview)", "")
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
        service.launch_date = service_launch_date
        service.summary = service_summary
        service.url = service_url.removesuffix("/")

        all_services.append(service)

    return all_services


def lambda_handler(event, context):
    services_ssm: [Service] = get_services_ssm()
    services_categories: [Service] = get_services_categories()

    # print(json.dumps([ob.__dict__ for ob in services_ssm]))
    # print(json.dumps([ob.__dict__ for ob in services_categories]))

    merged_services = [Service]
    for service_1 in services_ssm:
        for service_2 in services_categories:
            if service_1.product_name == service_2.product_name or service_1.url == service_2.url:
                service = Service()
                service.id = service_1.id
                service.name = service_2.name
                if service_1.product_name == service_2.product_name \
                        or len(service_1.product_name) > len(service_2.product_name):
                    service.product_name = service_1.product_name
                else:
                    service.product_name = service_2.product_name

                service.category = service_2.category
                service.launch_date = service_2.launch_date
                service.summary = service_2.summary
                service.url = service_2.url

                if hasattr(service_2, 'regions'):
                    service.regions = service_2.regions
                merged_services.append(service)

    print(jsonpickle.encode(merged_services))

    return {
        'statusCode': 200,
        'body': json.dumps(f"found {len(services_ssm)} services.")
    }


if __name__ == "__main__":
    lambda_handler(None, None)
