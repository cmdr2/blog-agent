import zipfile


def run(data, **kwargs):
    unzipped_files = []  # tuple of (filename, contents)

    with zipfile.ZipFile(data, "r") as zip_ref:
        for file_info in zip_ref.infolist():
            file_name = file_info.filename

            with zip_ref.open(file_info) as file:
                unzipped_files.append((file_name, file.read()))

    return unzipped_files
