import json
import boto3
import botocore


def create_usable_bucket_on_s3(bucket_name, s3_client, iam_client):
    """Create an S3 bucket and a user/key-pair that can access it.

    Return info for the user/key-pair
    """
    _create_bucket(bucket_name, s3_client)
    user_info = _create_user(bucket_name, iam_client)
    policy = _create_policy(bucket_name, iam_client)
    _attach_policy_to_user(iam_client, policy, user_info)
    return user_info


def _create_bucket(bucket_name, s3_client):
    response = s3_client.create_bucket(
        ACL='private',
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'us-east-1'},
    )


def _create_user(bucket_name, iam_client):
    user_info = {}
    user_info['name'] = bucket_name + '.user'
    user = iam_client.create_user(UserName=user_info['name'])
    key = iam_client.create_access_key(UserName=user_info['name'])[u'AccessKey']
    user_info['public_key'] = key[u'AccessKeyId']
    user_info['private_key'] = key[u'SecretAccessKey']
    return user_info


def _create_policy(bucket_name, iam_client):
    policy_document = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ]
        }]
    })
    policy_name = f"{bucket_name}.access_policy"
    policy_description = f"{bucket_name} bucket pangea access policy"
    try:
        policy = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=policy_document,
            Description=policy_description
        )[u'Policy']
    except botocore.exceptions.ClientError:
        raise
    return policy


def _attach_policy_to_user(iam_client, policy, user_info):
    try:
        iam_client.attach_user_policy(
            UserName=user_info["name"],
            PolicyArn=policy[u'Arn']
        )
    except botocore.exceptions.ClientError:
        raise
