"Just mirrors the file back. Useful for copying the Dropbox files to S3 without any modifications"


def process_files(file_iterator, config={}):
    file_list = {}

    for filename, content in file_iterator:
        file_list.append((filename, content))

    return file_list
