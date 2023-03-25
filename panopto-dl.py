import argparse
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

browser = webdriver.Firefox(service=Service(GeckoDriverManager().install()))
browser.delete_all_cookies()
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

# WebDriverWait(browser, timeout=20000).until(lambda d: d.find_element(By.CLASS_NAME,"detail-title"))
videos = dict()
for match in WebDriverWait(browser, 2000000).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".detail-title"))):
    try:
        key = match.find_element(By.TAG_NAME, "span").text
        videos[key] = match.get_attribute("href")  
    except selenium.common.exceptions.NoSuchElementException as e:
        pass


print(videos)







