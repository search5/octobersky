import boto3
from nanumlectures.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME


def get_client():
    client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    return client

def upload_blob(source_file, destination_blob_name, content_type):
    """Uploads a file to the bucket."""
    storage_client = get_client()
    storage_client.upload_fileobj(source_file, S3_BUCKET_NAME, destination_blob_name)

    return True


def download_blob(source_file_name, dst_obj):
    """Uploads a file to the bucket."""
    storage_client = get_client()
    storage_client.download_fileobj(S3_BUCKET_NAME, source_file_name, dst_obj)

    return True


def delete_blob(blob_name):
    """Deletes a blob from the bucket."""
    storage_client = get_client()
    storage_client.delete_object(Bucket=S3_BUCKET_NAME, Key=blob_name)
