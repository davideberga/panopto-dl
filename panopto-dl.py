import argparse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import socketserver
import http.server
import urllib.request
from multiprocessing import Process
import selenium
import time

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

PROXY_PORT = 8889
PROXY_URL = 'localhost:%d' % PROXY_PORT

class Proxy(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        sys.stdout.write('%s → %s\n' % (self.headers.get('Referer', 'NO_REFERER'), self.path))
        self.copyfile(urllib.request.urlopen(self.path), self.wfile)
        sys.stdout.flush()

    @classmethod
    def target(cls):
        httpd = socketserver.ThreadingTCPServer(('', PROXY_PORT), cls)
        httpd.serve_forever()

p_proxy = Process(target=Proxy.target)
p_proxy.start()

options = webdriver.ChromeOptions() ;
prefs = {"download.default_directory" : "./downloads"};
options.add_experimental_option("prefs",prefs);

webdriver.DesiredCapabilities.CHROME['proxy'] = {
    "httpProxy":PROXY_URL,
    "ftpProxy":None,
    "sslProxy":None,
    "noProxy":None,
    "proxyType":"MANUAL",
    "class":"org.openqa.selenium.Proxy",
    "autodetect":False
}

browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
browser.delete_all_cookies()
browser.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Linux; Android 10; Generic Android-x86_64 Build/QD1A.190821.014.C2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/79.0.3945.36 Safari/537.36'})
browser.get("https://univr.cloud.panopto.eu/Panopto/Pages/Auth/Login.aspx")

# browser.maximize_window()

idPanoptoSignIn = 'PageContentPlaceholder_loginControl_externalLoginButton'
signInButton = browser.find_element(By.ID, idPanoptoSignIn)
signInButton.click()

videos = WebDriverWait(browser, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".btn-login")))
userInputLogin = browser.find_element(By.ID, 'form_username')
idPwdLogin = browser.find_element(By.ID, 'form_password')
idSubmitLogin = browser.find_element(By.CSS_SELECTOR, '.btn-login')

userInputLogin.send_keys(username)
idPwdLogin.send_keys(password)
idSubmitLogin.click()

time.sleep(5)

browser.get(url)
browser.maximize_window()
time.sleep(5)

# WebDriverWait(browser, timeout=20000).until(lambda d: d.find_element(By.CLASS_NAME,"detail-title"))
urlsVideos = dict()
for match in WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".detail-title"))):
    try:
        key = match.find_element(By.TAG_NAME, "span").text
        urlsVideos[key] = match.get_attribute("href")  
    except selenium.common.exceptions.NoSuchElementException as e:
        pass

print(urlsVideos)

videos = dict()
for video in urlsVideos.keys():
    try:
        if urlsVideos[video] != None:
            browser.get(urlsVideos[video])
            time.sleep(5)
            primaryUrl = browser.find_element(By.ID, 'primaryVideo').get_attribute("src")
            secondaryUrl = browser.find_element(By.ID, 'secondaryVideo').get_attribute("src")

            videos[video]['primary'] = primaryUrl
            videos[video]['secondary'] = secondaryUrl
    except selenium.common.exceptions.NoSuchElementException as e:
        pass

print(videos)

import os

def downloadfile(name,url):
    name = name + ".mp4"
    r = requests.get(url)
    with open(name,'wb') as file:
        for chunk in r.iter_content(chunk_size=255): 
            if chunk: # filter out keep-alive new chunks
                file.write(chunk)

outputPath = "./panopto-lectures"
if not os.path.exists(outputPath):
    os.makedirs(outputPath)

for video in videos:
    if not os.path.exists(os.path.join(outputPath, video)):
        os.makedirs(os.path.join(outputPath, video))
    downloadfile(os.path.join(outputPath, video, "primary"), videos[video]['primary'])
    downloadfile(os.path.join(outputPath, video, "secondary"), videos[video]['secondary'])








