
import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://my_hostname/"
LANDING = "Landing/"


def login_pano(driver, username, password, timeout=30):
    driver.get(BASE_URL + LANDING + '#login')
    wait = WebDriverWait(driver, timeout)
    short_wait = WebDriverWait(driver, 2)
    # //*[@id=\"GovtBanner\"]/div/div/div
    # "close-systemuse"
    short_wait.until(EC.visibility_of_element_located((By.XPATH, "//*[@id=\"GovtBanner\"]/div/div/div")))
    try:
        driver.find_element_by_xpath("//*[@id=\"GovtBanner\"]/div/div/div").click()
    except NoSuchElementException:
        pass
    wait.until(EC.visibility_of_element_located((By.XPATH, "//*[@id=\"loginSubmit\"]")))
    username_field = driver.find_element_by_xpath("//*[@id=\"username\"]")
    username_field.clear()
    username_field.send_keys(username)
    password_field = driver.find_element_by_xpath("//*[@id=\"password\"]")
    password_field.clear()
    password_field.send_keys(password)
    driver.find_element_by_xpath("//*[@id=\"loginSubmit\"]").click()
    try:
        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(@id,\"-topnav\")]/ul/li[6]/a/span")))
        time.sleep(1)
    except TimeoutException:
        return False
    return True


def home(driver, timeout=30):
    try:
        driver.switch_to.parent_frame()
        driver.find_element_by_xpath("//*[@id=\"left_toolbar_selector_home\"]/img").click()
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.CLASS_NAME, "map")))
    except TimeoutException:
        return False
    except NoSuchElementException:
        return False
    return True


def dashboards(driver, timeout=30):
    try:
        driver.switch_to.parent_frame()
        driver.find_element_by_xpath("//*[@id=\"left_toolbar_selector2\"]/img").click()
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, "//*[@id=\"searchTextBar\"]")))
    except TimeoutException:
        return False
    except NoSuchElementException:
        return False
    return True


def applications(driver, timeout=30):
    try:
        driver.switch_to.parent_frame()
        driver.find_element_by_xpath("//*[@id=\"left_toolbar_selector1\"]/img").click()
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.CLASS_NAME, "thumbnail-row")))
    except TimeoutException:
        return False
    except NoSuchElementException:
        return False
    return True


def knowledge(driver, timeout=30):
    try:
        driver.switch_to.parent_frame()
        driver.find_element_by_xpath("//*[@id=\"left_toolbar_selector3\"]/img").click()
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, "//*[@id=\"leftmenu_home_li\"]/a")))
    except TimeoutException:
        return False
    except NoSuchElementException:
        return False
    return True


def connect(driver, timeout=30):
    try:
        driver.switch_to.parent_frame()
        driver.find_element_by_xpath("//*[@id=\"left_toolbar_selector4\"]/img").click()
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.CLASS_NAME, "modal-title")))
    except TimeoutException:
        return False
    except NoSuchElementException:
        return False
    return True


def support(driver, timeout=30):
    try:
        driver.switch_to.parent_frame()
        driver.find_element_by_xpath("//*[@id=\"left_toolbar_selector5\"]/img").click()
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, "//*[@id=\"query\"]")))
    except TimeoutException:
        return False
    except NoSuchElementException:
        return False
    return True


def logout(driver):
    driver.switch_to.parent_frame()
    driver.find_element_by_xpath("//*[contains(@id,\"-topnav\")]/ul/li[6]/a").click()
