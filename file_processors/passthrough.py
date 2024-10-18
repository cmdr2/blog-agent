"Just mirrors the file back. Useful for copying the Dropbox files to S3 without any modifications"


def process_file(filename, content: str):
    return {filename: content}
