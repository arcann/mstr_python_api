from selenium.common.exceptions import NoSuchElementException


def find_optional_elements_by_xpath(driver, xpath) -> list:
    try:
        return driver.find_elements_by_xpath(xpath)
    except NoSuchElementException:
        return []
