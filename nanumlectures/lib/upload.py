from google.cloud import storage


def upload_blob(source_file, destination_blob_name, content_type):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket_name = 'nanumlectures-167211.appspot.com'
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(source_file, content_type=content_type)

    return True


def download_blob(source_file_name, dst_obj):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket_name = 'nanumlectures-167211.appspot.com'
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(source_file_name)
    blob.download_to_file(dst_obj)

    return True


def delete_blob(blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket_name = 'nanumlectures-167211.appspot.com'
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.delete()
