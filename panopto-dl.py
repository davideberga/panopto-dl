import argparse, validators, time, re, json, urllib.request, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.logging import RichHandler
from rich.progress import track
from getpass import getpass

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from login_service.login_univr import LoginUnivr

# Login types supported
login_types = { "univr" }

# Setup logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")

parser = argparse.ArgumentParser(description='Download in batch videos from panopto')
parser.add_argument('-url', metavar='--panopto-course-url', nargs=1, required=True,
                    help='Url of the course')
parser.add_argument('-u', metavar='--gia-username', nargs=1,
                    help='Gia username')
parser.add_argument('-d', metavar='--download-directory', nargs=1, default="./",
                    help='Download Directory')
parser.add_argument('-t', metavar='--login-type', nargs=1, default="univr", choices=login_types,
                    help='Login sso type')
args = parser.parse_args()

url = args.url[0]
login_type = args.t
download_dir = args.d

username = args.u
if(username == None):
    username = input("GIA username: ")
password = getpass("GIA password: ")

log.info("Start login to panopto...")
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

if(login_type == "univr"):
    login_exec = LoginUnivr(browser)

browser.get(login_exec.get_login_url())
idPanoptoSignIn = 'PageContentPlaceholder_loginControl_externalLoginButton'
signInButton = browser.find_element(By.ID, idPanoptoSignIn)
signInButton.click()

log.info(f"Open organization login page ({args.t})")
time.sleep(2)

if not login_exec.login(username, password):
    log.error("Login failed!")
    exit(12)

time.sleep(2)
if login_exec.is_login_failed():
    log.error("Login failed!")
    exit(12)

log.info("Login succeded!")
browser.get(url)

time.sleep(2)

# WebDriverWait(browser, timeout=20000).until(lambda d: d.find_element(By.CLASS_NAME,"detail-title"))
urlsVideos = dict()
for match in WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".detail-title"))):
    try:
        key = match.find_element(By.TAG_NAME, "span").text
        url_video = str(match.get_attribute("href"))
        url_video = url_video.replace("Viewer", "Embed")
        urlsVideos[key] = url_video
    except NoSuchElementException as e:
        pass

if(len(urlsVideos.keys()) == 0):
    log.error("0 videos found :(")
else:
    log.info(str(len(urlsVideos.keys())) + " videos found")

log.info("Collecting pure video urls without login ... be patient")
videos = dict()
for video in track(urlsVideos.keys(), description="Scraping..."):
    try:
        if validators.url(urlsVideos[video]):
            browser.get(urlsVideos[video])
            source = browser.page_source
            time.sleep(1)

            panoptoConfigObj = re.search(r"PanoptoTS.Embed.EmbeddedViewer\((\{.*\}).*\)", source).group(1)
            panoptoConfigObj = json.loads(panoptoConfigObj.replace("\\/", "/"))

            videos[video] = dict()
            videos[video]['embed'] = panoptoConfigObj["VideoUrl"]

    except NoSuchElementException as e:
        log.error(e)
        pass

import os

def downloadfile(name, url):
    name = name + ".mp4"

    if not validators.url(url):
        return False
    log.info("start downloading {}".format(name))

    try:
        urllib.request.urlretrieve(url, name)
    except:
        log.error(url + " request error")
        return False
    
    log.info("{} downloaded correctly!".format(name))
    return True

outputPath = os.path.join(download_dir, "panopto-lectures")
if not os.path.exists(outputPath):
    os.makedirs(outputPath)

browser.close()

# Create paths if not exists
for video in videos:
    if not os.path.exists(os.path.join(outputPath, video)):
        os.makedirs(os.path.join(outputPath, video))

log.info("Start downloading videos")
with ThreadPoolExecutor(max_workers=4) as executor:

    future_download = [executor.submit(downloadfile, os.path.join(outputPath, video, "complete"), videos[video]['embed']) for video in videos]
    
    for future in track(as_completed(future_download), description="Downloading..."):
        try:
            data = future.result()
        except Exception as exc:
            print('%r generated an exception: %s' % (url, exc))

log.info("[bold green blink]Done![/]", extra={ "markup" : True})












