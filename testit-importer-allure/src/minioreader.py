"""The module provides functionality for reading result files from Minio"""
import io
import os

import minio.error
from interface import implements
from minio import Minio

from .filedto import FileDto
from .reader import Reader


class MinioReader(implements(Reader)):
    """Class representing a reader"""

    def __init__(self, host: str, access_key: str, secret_key: str, bucket: str):
        self.__bucket = bucket
        self.__client = Minio(host, access_key=access_key,
                              secret_key=secret_key, secure=False)

    def get_all_files(self):
        """Function returns all result files."""
        files = []
        objects = self.__client.list_objects(self.__bucket, recursive=True)
        for obj in objects:
            name = obj.object_name
            if 'json' in name or 'xml' in name:
                files.append(name)

        return files

    def read_file(self, file_name: str):
        """Function reads result file by name."""
        file = self.__client.get_object(self.__bucket, file_name)
        return FileDto(file_name, io.BytesIO(file.data))

    def read_attachment(self, file_name: str):
        """Function reads attachment by name."""
        try:
            file = self.__client.get_object(self.__bucket, file_name)
            with open(file_name, 'wb') as local_file:
                local_file.write(file.data)
            return open(file_name, 'rb')
        except minio.error.S3Error:
            return None

    def remove_attachment(self, file_name: str):
        """Function removes attachment by name."""
        os.remove(file_name)
