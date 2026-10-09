"""Uploaded files. Local folder for development, S3 when deployed (UPLOADS_BUCKET is set by template.yaml)."""
import os
import shutil
from pathlib import Path

class LocalFiles:
    def __init__(self):
        self.root = Path(os.environ.get("LOCAL_STATE_DIR", ".state")) / "files"

    def put(self, pid: str, name: str, data: bytes, content_type: str):
        p = self.root / pid
        p.mkdir(parents=True, exist_ok=True)
        (p / name).write_bytes(data)

    def get(self, pid: str, name: str) -> bytes | None:
        p = self.root / pid / name
        return p.read_bytes() if p.exists() else None

    def delete(self, pid: str, name: str):
        (self.root / pid / name).unlink(missing_ok=True)

    def delete_project(self, pid: str):
        shutil.rmtree(self.root / pid, ignore_errors=True)

class S3Files:
    def __init__(self, bucket: str):
        import boto3
        self.bucket, self.s3 = bucket, boto3.client("s3")

    def put(self, pid, name, data, content_type):
        self.s3.put_object(Bucket=self.bucket, Key=f"{pid}/{name}", Body=data, ContentType=content_type,
                           ServerSideEncryption="AES256")

    def get(self, pid, name):
        try:
            return self.s3.get_object(Bucket=self.bucket, Key=f"{pid}/{name}")["Body"].read()
        except self.s3.exceptions.NoSuchKey:
            return None

    def delete(self, pid, name):
        self.s3.delete_object(Bucket=self.bucket, Key=f"{pid}/{name}")

    def delete_project(self, pid):
        pages = self.s3.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=f"{pid}/")
        for page in pages:
            keys = [{"Key": o["Key"]} for o in page.get("Contents", [])]
            if keys:
                self.s3.delete_objects(Bucket=self.bucket, Delete={"Objects": keys})

def get_files():
    bucket = os.environ.get("UPLOADS_BUCKET")
    return S3Files(bucket) if bucket else LocalFiles()
