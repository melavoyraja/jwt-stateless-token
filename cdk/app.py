#!/usr/bin/env python3
from constructs import Construct

import aws_cdk as cdk
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam


class MyCdkStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a KMS key for signing operations (SIGN_VERIFY purpose)
        kms_key = kms.Key(
            self,
            "JWTSigningKey",
            enabled=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
            key_spec=kms.KeySpec.RSA_3072,
            key_usage=kms.KeyUsage.SIGN_VERIFY,
        )

        # Add an alias for the KMS key
        kms.CfnAlias(
            self,
            "JWTSigningKeyAlias",
            alias_name="alias/JWTSigningKey",  # Set your desired alias name
            target_key_id=kms_key.key_id,
        )

        # Create an IAM role
        lambda_role = iam.Role(
            self,
            "JWTSigningLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Allow IAM role to use the KMS key for signing and verification
        kms_key.grant(lambda_role, "kms:Sign", "kms:Verify")

        # Allow IAM role to use the KMS key for signing and verification
        kms_key.add_to_resource_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["kms:Sign", "kms:Verify"],
                principals=[lambda_role],
                resources=["*"],
            )
        )

        # Define the Lambda function
        my_lambda = lambda_.Function(
            self,
            "JWTSigningLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="main.handler",
            role=lambda_role,
            code=lambda_.Code.from_asset(
                "./application",
                bundling={
                    "image": cdk.DockerImage.from_registry("python:3.9"),
                    "command": [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output --platform manylinux2014_x86_64 --only-binary=:all: && cp -r . /asset-output",  # noqa: E501
                    ],
                },
            ),
        )

        # add function url
        my_lambda.add_function_url(auth_type=lambda_.FunctionUrlAuthType.NONE)


app = cdk.App()
MyCdkStack(
    app,
    "CdkStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.
    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.
    # env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    # region=os.getenv('CDK_DEFAULT_REGION')),
    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */
    # env=cdk.Environment(account='123456789012', region='us-east-1'),
    # For more information,
    # see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
)

app.synth()
