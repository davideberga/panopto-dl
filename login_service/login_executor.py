import abc
import logging
from selenium.webdriver.chrome.webdriver import WebDriver

class LoginExecutor(abc.ABC):

    def __init__(self, browser : WebDriver):
        self.browser = browser
        self.logger = logging.getLogger("rich")

    @abc.abstractmethod
    def get_login_url(self) -> str:
        raise NotImplementedError
    
    @abc.abstractmethod
    def login(self, username: str, password: str) -> bool:
        raise NotImplementedError
    
    @abc.abstractmethod
    def is_login_failed(self) -> bool:
        raise NotImplementedError
        
