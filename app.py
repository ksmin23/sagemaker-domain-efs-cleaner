#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  SageMakerEFSCleanerLambdaStack,
  VpcStack
)


APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'SageMakerEFSCleanerVPC',
  env=APP_ENV)

lambda_fn = SageMakerEFSCleanerLambdaStack(app, 'SageMakerEFSCleanerLambdaFunction',
  env=APP_ENV
)
lambda_fn.add_dependency(vpc_stack)

app.synth()
