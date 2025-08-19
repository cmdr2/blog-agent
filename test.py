import os

os.environ.update({"IS_LOCAL_TEST": "1"})

import workflow

base_dir = "~/Dropbox/Apps/journal-public/"
base_dir = os.path.expanduser(base_dir)

files = []
for file in os.listdir(base_dir + "/notes"):
    if file.lower().endswith(".txt"):
        files.append(f"notes/{file}")

files_iterator = []
for file in files:
    with open(base_dir + "/" + file, "rb") as f:
        files_iterator.append((file, f.read()))

workflow.download_from_dropbox = lambda x: files_iterator
workflow.unzip_files = lambda x: x  # No-op since files are already in the correct format
workflow.publish_to_github = lambda x, config: print("uploading", config, len(x)) or []  # No-op for local testing

workflow.run()

# for file_path, content in d:
#     out_path = f"tmp/{file_path}"

#     dir_name = os.path.dirname(out_path)
#     if dir_name:
#         os.makedirs(dir_name, exist_ok=True)

#     with open(out_path, "w") as f2:
#         print(out_path, len(content), "bytes")
#         f2.write(content)
