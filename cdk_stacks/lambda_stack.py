
#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_lambda,
  aws_logs,
  aws_events,
  aws_events_targets
)
from constructs import Construct


class SageMakerEFSCleanerLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    efs_cleaner_lambda_fn = aws_lambda.Function(self, "SageMakerEFSCleaner",
      runtime=aws_lambda.Runtime.PYTHON_3_11,
      function_name="SageMakerEFSCleaner",
      handler="efs_cleaner.lambda_handler",
      description="Clean up unused EFS by SageMaker Domains",
      code=aws_lambda.Code.from_asset('./src/python/SageMakerEFSCleaner'),
      timeout=cdk.Duration.minutes(15)
    )

    efs_cleaner_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=[
        "elasticfilesystem:DescribeMountTargets",
        "elasticfilesystem:DescribeFileSystems",
        "elasticfilesystem:DeleteMountTarget",
        "elasticfilesystem:DeleteFileSystem"
      ]))

    efs_cleaner_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=[
        "sagemaker:List*"
      ]))

    lambda_fn_target = aws_events_targets.LambdaFunction(efs_cleaner_lambda_fn)
    aws_events.Rule(self, "ScheduleRule",
      schedule=aws_events.Schedule.cron(hour="19", minute="10"),
      targets=[lambda_fn_target]
    )

    log_group = aws_logs.LogGroup(self, "SageMakerEFSCleanerLogGroup",
      log_group_name=f"/aws/lambda/{self.stack_name}/SageMakerEFSCleanerLogGroup",
      removal_policy=cdk.RemovalPolicy.DESTROY,
      retention=aws_logs.RetentionDays.THREE_DAYS)
    log_group.grant_write(efs_cleaner_lambda_fn)


    cdk.CfnOutput(self, 'LambdaFuncName',
      value=efs_cleaner_lambda_fn.function_name,
      export_name=f'{self.stack_name}-LambdaFuncName')
