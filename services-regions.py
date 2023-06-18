import json

import boto3

from services import Service

ssm = boto3.client('ssm')


def get_regional_services(region):
    paginator = ssm.get_paginator('get_parameters_by_path')

    response_iterator = paginator.paginate(
        Path=f"/aws/service/global-infrastructure/regions/{region}/services"
    )

    parameters = []
    for page in response_iterator:
        for entry in page['Parameters']:
            parameters.append(entry)

    return parameters


def lookup_service_name(service_key):
    parameter = ssm.get_parameters_by_path(Path=f"/aws/service/global-infrastructure/services/{service_key}")
    if parameter is not None and len(parameter['Parameters']) > 0:
        return parameter['Parameters'][0]['Value']
    else:
        return 'unknown'


def lambda_handler(event, context):
    regions = ['us-east-1', 'eu-central-1', 'eu-central-2']

    regional_services_dict = {}
    for region in regions:
        regional_services_dict[region] = get_regional_services(region)

    all_services = {}
    for region_key in regional_services_dict:
        regional_services = regional_services_dict[region_key]
        for regional_service in regional_services:
            service_key = regional_service['Value']
            srv = all_services.get(service_key, {'key': service_key, 'regions': []})
            srv['regions'].append(region_key)
            all_services[service_key] = srv

    service_list = []
    for service_key in all_services:
        service = all_services[service_key]
        service_name = lookup_service_name(service_key)
        service['name'] = service_name
        all_services[service_key] = service
        s = Service()
        s.id = service_key
        s.name = service['name']
        s.regions = service['regions']
        service_list.append(s)

    json_string = json.dumps([ob.__dict__ for ob in service_list])
    print(json_string)

    return {
        'statusCode': 200,
        'body': json.dumps(f"found {len(service_list)} services.")
    }


if __name__ == "__main__":
    lambda_handler(None, None)
