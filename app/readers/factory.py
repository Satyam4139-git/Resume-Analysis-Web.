from app.readers.pdf_reader import PDFReader
from app.readers.docx_reader import DOCXReader


class FileReaderFactory:
    """
    Returns the appropriate reader
    based on the file extension.
    """

    @staticmethod
    def get_reader(file_path):

        extension = file_path.lower().split(".")[-1]

        readers = {
            "pdf": PDFReader,
            "docx": DOCXReader,
        }

        reader_class = readers.get(extension)

        if reader_class is None:
            raise ValueError(
                f"Unsupported file format: {extension}"
            )

        return reader_class()