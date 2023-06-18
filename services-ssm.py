import json

import boto3

from services import Service

ssm = boto3.client('ssm')


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


def lambda_handler(event, context):
    all_services = get_all_services()

    service_list = []
    for service_key in all_services:
        service_name, service_url = lookup_service_name(service_key)
        service = Service()
        service.product_name = service_name
        service.id = service_key
        service.url = service_url
        service_list.append(service)

    json_string = json.dumps([ob.__dict__ for ob in service_list])
    print(json_string)

    return {
        'statusCode': 200,
        'body': json.dumps(f"found {len(service_list)} services.")
    }


if __name__ == "__main__":
    lambda_handler(None, None)
