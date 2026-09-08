from io import BytesIO

from werkzeug.datastructures import FileStorage

# tiny valid-enough PNG header + filler; content is not inspected by the
# in-memory test storage, only its size/name matter
IMAGE_DATA = b"\x89PNG\r\n\x1a\n" + b"0" * 64


class FakeFileStorage(FileStorage):
    """A ``werkzeug`` upload the ``files`` extension will accept."""

    def __init__(self, stream=None, filename="image.png", content_type="image/png"):
        if stream is None:
            stream = BytesIO(IMAGE_DATA)
        super().__init__(stream, filename, "upload", content_type=content_type)
