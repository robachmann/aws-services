import json

import boto3
import requests

ssm = boto3.client('ssm')


class Service:
    id: str
    name: str
    product_name: str
    category: str
    launch_date: str
    summary: str
    url: str
    regions: []


def get_all_services():
    paginator = ssm.get_paginator('get_parameters_by_path')

    response_iterator = paginator.paginate(Path="/aws/service/global-infrastructure/services")

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


def get_regions() -> [str]:
    paginator = ssm.get_paginator('get_parameters_by_path')

    response_iterator = paginator.paginate(Path=f"/aws/service/global-infrastructure/regions")

    parameters = []
    for page in response_iterator:
        for entry in page['Parameters']:
            parameters.append(entry['Value'])

    return parameters


def get_regional_services(region):
    paginator = ssm.get_paginator('get_parameters_by_path')

    response_iterator = paginator.paginate(Path=f"/aws/service/global-infrastructure/regions/{region}/services")

    parameters = []
    for page in response_iterator:
        for entry in page['Parameters']:
            parameters.append(entry['Value'])

    return parameters


def get_services_regions() -> {}:
    regional_services_dict = {}

    for region in get_regions():
        regional_services_dict[region] = get_regional_services(region)

    all_services = {}
    for region_key in regional_services_dict:
        regional_services = regional_services_dict[region_key]
        for service_key in regional_services:
            regions = all_services.get(service_key, [])
            regions.append(region_key)
            all_services[service_key] = regions

    return all_services


def lambda_handler(event, context):
    print(f"Fetching services...")
    services_ssm: [Service] = get_services_ssm()
    print(f"Fetching services... {len(services_ssm)} services from SSM params")
    services_regions: {str, [str]} = get_services_regions()
    print(f"Fetching services... {len(services_regions)} services from regions")
    services_categories: [Service] = get_services_categories()
    print(f"Fetching services... {len(services_categories)} services from AWS website")

    merged_services = []
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
                service_regions = services_regions.get(service_1.id, [])
                service_regions.sort()
                service.regions = service_regions
                merged_services.append(service)

    json_string = json.dumps([ob.__dict__ for ob in merged_services])

    file_path = 'aws-services.json'
    with open(file_path, 'w') as f:
        f.write(json_string)

    print(f"Merged {len(merged_services)} services.")

    return {
        'statusCode': 200,
        'body': json.dumps(f"found {len(services_ssm)} services.")
    }


if __name__ == "__main__":
    lambda_handler(None, None)
