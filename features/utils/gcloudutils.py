import os
from typing import List

from google.cloud import storage
from google.cloud.storage import Blob


def copy_gcs_path(bucket_name: str) -> bool:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Create a local directory with the bucket name
    local_dir = f"data/{bucket_name}"
    os.makedirs(local_dir, exist_ok=True)
    
    # Download all blobs (files) from the bucket
    blobs: List[Blob] = list(bucket.list_blobs())
    for blob in blobs:
        if blob.name is None:
            continue
        
        # Create the full local path
        local_path: str = os.path.join(local_dir, blob.name)
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Download the file
        blob.download_to_filename(local_path)
    
    return True
