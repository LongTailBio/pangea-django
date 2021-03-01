

class S3MultipartUploadUtil:
    """AWS S3 Multipart Upload Util"""

    def __init__(self, api_key, s3_file_key):
        self.api_key = api_key
        self.s3 = self.api_key.s3
        self.s3_file_key = s3_file_key
        res = self.s3.create_multipart_upload(
            Bucket=self.api_key.bucket.name,
            Key=self.s3_file_key
        )
        self.upload_id = res['UploadId']
        self.part_no = 1

    def create_presigned_url(self, part_no=None, timeout_hours=24):
        part_no = self.part_no if part_no is None else part_no
        signed_url = self.s3.generate_presigned_url(
            ClientMethod='upload_part',
            Params={
                'Bucket': self.api_key.bucket.name,
                'Key': self.s3_file_key,
                'UploadId': self.upload_id,
                'PartNumber': part_no
            },
            ExpiresIn=(timeout_hours * 60 * 60)
        )
        self.part_no += 1
        return signed_url

    def create_complete_url(self, upload_id, parts, timeout_hours=24):
        self.s3.complete_multipart_upload(
            Bucket=self.api_key.bucket.name,
            Key=self.s3_file_key,
            MultipartUpload={'Parts': parts},
            UploadId=upload_id
        )
        return {'status': 'success', 'upload_id': upload_id}
