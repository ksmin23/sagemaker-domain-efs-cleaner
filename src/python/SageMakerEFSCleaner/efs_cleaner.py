#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import sys
import boto3
from botocore.exceptions import ClientError
import json
import time


def get_active_sagemaker_domains(region='us-east-1'):
  sm_client = boto3.client('sagemaker', region_name=region)

  response = sm_client.list_domains()
  active_domain_arn_list = [e['DomainArn'] for e in response['Domains']]
  return active_domain_arn_list


def get_unused_efs_file_system_ids(active_domain_arn_list=[], region='us-east-1'):
  efs_client = boto3.client('efs', region_name=region)
  response = efs_client.describe_file_systems()
  file_systems = response['FileSystems']

  file_system_id_list = []
  for elem in file_systems:
    tags = elem.get('Tags', {})
    tags = [t for t in tags if t['Key'] == 'ManagedByAmazonSageMakerResource' and t['Value'] not in active_domain_arn_list]
    if tags:
      file_system_id_list.append(elem['FileSystemId'])

  return file_system_id_list


def delete_efs(file_system_id, region='us-east-1'):
  efs_client = boto3.client('efs', region_name=region)

  try:
    mount_targets = efs_client.describe_mount_targets(FileSystemId=file_system_id)['MountTargets']
    for mount_target in mount_targets:
      efs_client.delete_mount_target(MountTargetId=mount_target['MountTargetId'])

    for _ in range(12):
      mount_targets = efs_client.describe_mount_targets(FileSystemId=file_system_id)['MountTargets']
      if len(mount_targets) == 0:
        break
      time.sleep(5)

    efs_client.delete_file_system(FileSystemId=file_system_id)
    print(f"EFS {file_system_id} is completely deleted")
    return True
  except ClientError as e:
    print(f"EFS Deletion Error occurred: {e}")
    return False


def lambda_handler(event, context):
  region = boto3.Session().region_name
  active_domain_arn_list = get_active_sagemaker_domains(region)
  file_system_id_list = get_unused_efs_file_system_ids(active_domain_arn_list, region)
  for file_system_id in file_system_id_list:
    delete_efs(file_system_id, region)


if __name__ == '__main__':
  region = boto3.Session().region_name
  event_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
  event = {
    "id": "cdc73f9d-aea9-11e3-9d5a-835b769c0d9c",
    "detail-type": "Scheduled Event",
    "source": "aws.events",
    "account": "123456789012",
    "time": event_time, # ex) "2020-02-28T03:05:00Z"
    "region": region, # ex) "us-east-1"
    "resources": [
      f"arn:aws:events:{region}:123456789012:rule/ExampleRule"
    ],
    "detail": {}
  }
  print(f'[DEBUG] event:\n{json.dumps(event, indent=4)}', file=sys.stderr)
  lambda_handler(event, {})
