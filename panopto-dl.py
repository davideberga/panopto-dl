import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

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

browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
browser.get("https://univr.cloud.panopto.eu/Panopto/Pages/Auth/Login.aspx")

browser.maximize_window()

idPanoptoSignIn = 'PageContentPlaceholder_loginControl_externalLoginButton'
signInButton = browser.find_element(By.ID, idPanoptoSignIn)
signInButton.click()

userInputLogin = browser.find_element(By.ID, 'form_username')
idPwdLogin = browser.find_element(By.ID, 'form_password')
idSubmitLogin = browser.find_element(By.CSS_SELECTOR, '.btn-login')

userInputLogin.send_keys(username)
idPwdLogin.send_keys(password)
idSubmitLogin.click()

browser.get(url)

# WebDriverWait(browser, timeout=20000).until(lambda d: d.find_element(By.CLASS_NAME,"detail-title"))

videos = browser.find_elements(By.CSS_SELECTOR, ".detail-title")
toDownload = dict()
print(videos)

for video in videos:
    title = video.text
    href = video.get_attribute('href')
    toDownload[title] = href

print(toDownload)





