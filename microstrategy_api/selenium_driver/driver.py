import os
import os.path
import zipfile
from urllib import request

import requests
from win32com.client import Dispatch


def get_version_via_com(filename):
    parser = Dispatch("Scripting.FileSystemObject")
    version = parser.GetFileVersion(filename)
    return version


def download_from_web(dir_path, chrome_drive_version):
    link = "http://chromedriver.storage.googleapis.com/LATEST_RELEASE_"+chrome_drive_version
    f = requests.get(link)
    chromedriver_version = f.text

    driver_path = os.path.join(dir_path, 'chromedriver.exe')
    if os.path.isfile(driver_path):
        try:
            os.remove(driver_path)
        except OSError:
            raise OSError(f'Cannot delete file chromedriver.exe from {dir_path}')

    request.urlretrieve(f"http://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_win32.zip", f"{dir_path}\\chromedriver_win32.zip")
    zip_ref = zipfile.ZipFile(f"{dir_path}\\chromedriver_win32.zip", "r")
    zip_ref.extractall(f"{dir_path}")
    zip_ref.close()
    if os.path.isfile(os.path.join(dir_path, 'chromedriver_win32.zip')):
        os.remove(f"{dir_path}\\chromedriver_win32.zip")
    os.environ['PATH'] += os.pathsep + os.path.join(f"{dir_path}")
    print(f"New Chrome Driver downloaded into {dir_path} folder")


def download_chrome_driver(driver_dir):

    dir_path = driver_dir
    if driver_dir is None:
        dir_path = os.path.join(os.path.dirname(__file__), 'drivers')

    chrome_drive_version = 0
    curr_chrome_drive_version = 1
    # path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    if os.path.isfile(path):
        chrome_version = get_version_via_com(path)
        chrome_drive_version = chrome_version[:chrome_version.rfind(".")]

    driver_path = os.path.join(dir_path, 'chromedriver.exe')
    if os.path.isfile(driver_path):
        my_cmd = f'{driver_path} --version'
        # os.system(my_cmd)
        with os.popen(my_cmd) as proc:
            full_curr_chrome_drive_version = proc.read()
        curr_chrome_drive_version = full_curr_chrome_drive_version[full_curr_chrome_drive_version.find(' ')+1:full_curr_chrome_drive_version.rfind(".")]

    # print(f'Existing Chrome Driver dir:{dir_path}')
    print(f'Chrome Driver Version New ####{chrome_drive_version}#### Existing ####{curr_chrome_drive_version}####')
    if chrome_drive_version != curr_chrome_drive_version:
        download_from_web(dir_path, chrome_drive_version)


