import logging

import PyPDF2


logger = logging.getLogger("ResumeAnalyzer")


class PDFReader:
    """
    Reads text from PDF files.
    """

    def read(self, file_path):

        text_parts = []

        try:

            with open(
                file_path,
                "rb"
            ) as file:

                reader = PyPDF2.PdfReader(
                    file
                )

                logger.info(
                    "PDF contains %s pages.",
                    len(reader.pages)
                )

                for page_number, page in enumerate(
                    reader.pages,
                    start=1
                ):

                    try:

                        page_text = page.extract_text()

                    except Exception as error:

                        logger.warning(
                            "Could not extract page %s: %s",
                            page_number,
                            error
                        )

                        continue

                    if page_text:

                        text_parts.append(
                            page_text
                        )

        except Exception as error:

            logger.exception(
                "Failed to read PDF."
            )

            raise

        text = "\n".join(
            text_parts
        )

        logger.info(
            "PDF text extraction completed. "
            "Characters extracted: %s",
            len(text)
        )

        return text