import requests
import json
import os

with open("conf.json", 'r') as f:
    content = json.load(f)
    file_id = content['id']
    ignore_ls = content['ignore']
    if 'passwd' in content:
        passwd = content['passwd']
    else:
        passwd = ""
    

FILE_ID = file_id
IGNORE_LS = ignore_ls
URL = f"https://cloud.tsinghua.edu.cn/api/v2.1/share-links/{FILE_ID}/dirents/"
DOWNLOAD_URL = f"https://cloud.tsinghua.edu.cn/d/{FILE_ID}/files/"
LOGIN_URL = f"https://cloud.tsinghua.edu.cn/d/{FILE_ID}/"

total_file_ls = []
client = requests.session()


def login():
    client.get(LOGIN_URL)
    csrftoken = client.cookies['sfcsrftoken']
    payload = {
        'password': passwd,
        'csrfmiddlewaretoken': csrftoken
    }
    client.post(LOGIN_URL, data=payload, headers=dict(Referer="https://cloud.tsinghua.edu.cn/"))

def get_dirents(file_path: str=""):
    payload = { 'thumbnail_size': 48,
                'path': '/' + file_path.strip('/')}

    r = client.get(URL, params=payload)
    content = json.loads(r.text)
    return content['dirent_list']


def make_path(path):
    downloads_path = "Downloads/" + path.strip('/') + '/'
    if not os.path.exists(downloads_path):
        os.makedirs(downloads_path)
    
    return downloads_path


def gen_file_ls(root_path: str=""):
    global total_file_ls

    file_ls = get_dirents(root_path)

    folders = [i['folder_path'] for i in file_ls if i['is_dir']]
    files = [i['file_path'] for i in file_ls if not i['is_dir']]

    total_file_ls += files

    if folders:
        for i in folders:
            gen_file_ls(i)


def remove_ignores():
    ignores = [f"/{i.lstrip('/')}" for i in IGNORE_LS]
    
    remove_ls = []
    for i in ignores:
        if not i.endswith('/') and i in total_file_ls:
            remove_ls.append(i)
        else:
            for j in total_file_ls:
                if j.startswith(i):
                    remove_ls.append(j)
    
    return [i for i in total_file_ls if i not in remove_ls]


def download(name: str, folder: str):
    print(f"downloading {name}")
    payloads = { 'p': folder + name,
                 'dl': 1}

    r = client.get(DOWNLOAD_URL, params=payloads, stream=True)
    download_path = make_path(folder)

    with open(download_path + name, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def get_download_ls():
    gen_file_ls()
    download_ls = remove_ignores()
    return download_ls


def download_all(download_ls):
    for i in download_ls:
        name = i.split('/')[-1]
        path = "/".join(i.split('/')[:-1]) + '/'
        download(name, path)


if __name__ == "__main__":
    if passwd:
        login()
    download_all(get_download_ls())
