#!/usr/bin/env python3
from constructs import Construct

import aws_cdk as cdk
from aws_cdk import aws_kms as kms


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
