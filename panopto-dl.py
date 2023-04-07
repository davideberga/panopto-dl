import os, argparse, validators, time, re, json, urllib.request, logging, string, unicodedata, hashlib
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.logging import RichHandler
from rich.progress import track
from getpass import getpass

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver import ChromeOptions
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
                    help='SSO login type')
parser.add_argument('-nh', action="store_true", help='Disable headless mode and see the browser actions')
args = parser.parse_args()

def init_browser(is_headless : bool = True) -> WebDriver:
    log.info("Initializing the webdriver...")
    options = ChromeOptions()
    options.headless = is_headless
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    log.info("[bold green blink]Initializion done![/]", extra={ "markup" : True})
    return browser

def perform_login(browser : WebDriver, u : str, p : str, login_type : str) -> None:
    log.info("Start login to panopto...")
    
    # Select the appropriate login modality
    if(login_type == "univr"):
        login_exec = LoginUnivr(browser)

    browser.get(login_exec.get_login_url())
    id_panopto_sign_in = 'PageContentPlaceholder_loginControl_externalLoginButton'
    sign_in_button = browser.find_element(By.ID, id_panopto_sign_in)
    sign_in_button.click()

    log.info(f"Open organization login page ({login_type})")
    time.sleep(2)

    if not login_exec.login(u, p):
        log.error("[bold red]Login failed![/]", extra={ "markup" : True})
        exit(12)

    time.sleep(2)
    if login_exec.is_login_failed():
        log.error("[bold red]Login failed![/]", extra={ "markup" : True})
        exit(12)

    log.info("[bold green]Login succeded![/]", extra={ "markup" : True})

def sanitize_filename(filename, replace=' '):
    for r in replace:
        filename = filename.replace(r,'_')

    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    char_limit = 255
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    
    # keep only valid chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in valid_chars)

    if len(cleaned_filename)>char_limit:
        log.warn(f"Warning, filename truncated because it was over {char_limit}. Filenames may no longer be unique")

    return cleaned_filename[:char_limit]    

def scrape_video_urls(browser: WebDriver, url: str) -> Tuple[dict, str]:
    browser.get(url)

    # Wait page loading
    time.sleep(2)

    h = hashlib.new('sha256')
    h.update(url.encode("utf-8"))
    course_title = h.hexdigest()
    try:
        course_title = browser.find_element(By.ID, "contentHeaderText").text
        log.info(f"Scraping {course_title}")
    except NoSuchElementException:
        log.warn(f"Course title not found, falling back to {course_title}")

    urls_videos = dict()
    for match in WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".detail-title"))):
        try:
            key = match.find_element(By.TAG_NAME, "span").text

            key = sanitize_filename(key)
            url_video = str(match.get_attribute("href"))

            # Request embed page version to retrieve the urls
            # of not splitted videos
            url_video = url_video.replace("Viewer", "Embed")
            urls_videos[key] = url_video
        except NoSuchElementException as e:
            pass

    if(len(urls_videos.keys()) == 0):
        log.error("0 videos found :(, exiting")
        exit(13)
    else:
        log.info(f"{str(len(urls_videos.keys()))} videos found")

    log.info("Collecting pure video urls without login ... be patient")
    videos = dict()
    for video in track(urls_videos.keys(), description="Scraping..."):
        try:
            if validators.url(urls_videos[video]):
                browser.get(urls_videos[video])
                source = browser.page_source
                time.sleep(1)

                # Extract video urls from embed page version
                panopto_config_obj = re.search(r"PanoptoTS.Embed.EmbeddedViewer\((\{.*\}).*\)", source).group(1)
                panopto_config_obj = json.loads(panopto_config_obj.replace("\\/", "/"))

                videos[video] = dict()
                # Add other infos in future versions
                videos[video]['embed'] = panopto_config_obj["VideoUrl"]

        except NoSuchElementException as e:
            log.error(e)
            pass

    return videos, sanitize_filename(course_title)

def download_file(name, url):
    name = name + ".mp4"

    if not validators.url(url):
        return False

    try:
        if not os.path.exists(name):
            log.info(f"Downloading {name}")
            urllib.request.urlretrieve(url, name)
            log.info(f"{name} downloaded correctly!")
        else:
            log.info(f"{name} already cached!")
        return True
    except:
        log.error(url + " request error")
        return False

def create_course_folder(download_dir : str, course_title : str) -> str:
    output_path = os.path.join(str(download_dir), "panopto-lectures", course_title)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    return output_path

def download(videos : dict, output_path : str) -> str:
    for video in videos:
        if not os.path.exists(os.path.join(output_path, video)):
            os.makedirs(os.path.join(output_path, video))

    log.info("Start downloading videos")
    with ThreadPoolExecutor(max_workers=4) as executor:

        future_download = [executor.submit(download_file, os.path.join(output_path, video, "complete"), videos[video]['embed']) for video in videos]
        
        for future in track(as_completed(future_download), description="Downloading..."):
            try:
                data = future.result()
            except Exception as exc:
                print(f"generated an exception: {exc}")

    log.info("[bold green blink]Done![/]", extra={ "markup" : True})

if __name__ == "__main__":

    # Retrieve credentials
    username = args.u
    if(username == None):
        username = input("GIA username: ")
    password = getpass("GIA password: ")

    browser = init_browser(False if args.nh else True)
    try:
        url = args.url[0]
        login_type = args.t
        download_dir = args.d[0]

        perform_login(browser, username, password, login_type)

        videos, course_title = scrape_video_urls(browser, url)
        output_path = create_course_folder(download_dir, course_title)

        download(videos, output_path)

    except KeyboardInterrupt:
        log.info("Aborting...")
    finally:
        browser.close()













