import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from rich.progress import track
import validators
import selenium
import time
import re
import json
import urllib.request
from os import listdir

import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")

parser = argparse.ArgumentParser(description='Download in batch videos from panopto')
parser.add_argument('-url', metavar='--panopto-course-url', nargs=1,
                    help='Url of the course')
parser.add_argument('-u', metavar='--gia-username', nargs=1,
                    help='Gia username')
parser.add_argument('-p', metavar='--gia-password', nargs=1,
                    help='Gia username')
args = parser.parse_args()

url = args.url[0]
username = args.u
password = args.p

log.info("Start login to panopto...")
browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
browser.get("https://univr.cloud.panopto.eu/Panopto/Pages/Auth/Login.aspx")

idPanoptoSignIn = 'PageContentPlaceholder_loginControl_externalLoginButton'
signInButton = browser.find_element(By.ID, idPanoptoSignIn)
signInButton.click()

log.info("Open login page with GIA credentials")

videos = WebDriverWait(browser, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".btn-login")))
userInputLogin = browser.find_element(By.ID, 'form_username')
idPwdLogin = browser.find_element(By.ID, 'form_password')
idSubmitLogin = browser.find_element(By.CSS_SELECTOR, '.btn-login')

userInputLogin.send_keys(username)
idPwdLogin.send_keys(password)
idSubmitLogin.click()

time.sleep(5)

browser.get(url)
log.info("Login succeded!")

time.sleep(5)

# WebDriverWait(browser, timeout=20000).until(lambda d: d.find_element(By.CLASS_NAME,"detail-title"))
urlsVideos = dict()
for match in WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".detail-title"))):
    try:
        key = match.find_element(By.TAG_NAME, "span").text
        url_video = str(match.get_attribute("href"))
        url_video = url_video.replace("Viewer", "Embed")
        urlsVideos[key] = url_video
    except selenium.common.exceptions.NoSuchElementException as e:
        pass

if(len(urlsVideos.keys()) == 0):
    log.error("0 videos found :(")
else:
    log.info(str(len(urlsVideos.keys())) + " videos found")

log.info("Collecting pure video urls without login ... be patient")
videos = dict()
for video in track(urlsVideos.keys(), description="Scraping..."):
    try:
        print(urlsVideos[video])
        if validators.url(urlsVideos[video]):
            browser.get(urlsVideos[video])
            source = browser.page_source
            time.sleep(1)
            panoptoConfigObj = re.search(r"PanoptoTS.Embed.EmbeddedViewer\((\{.*\}).*\)", source).group(1)
            panoptoConfigObj = json.loads(panoptoConfigObj.replace("\\/", "/"))

            videos[video] = dict()
            videos[video]['embed'] = panoptoConfigObj["VideoUrl"]
            # videos[video]['embed'] = secondaryUrl
    except selenium.common.exceptions.NoSuchElementException as e:
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

outputPath = "./panopto-lectures"
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












