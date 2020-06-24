import logging
import time
import winsound
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, \
    UnexpectedAlertPresentException, ElementClickInterceptedException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from microstrategy_api.selenium_driver.find_elements import find_optional_elements_by_xpath
from microstrategy_api.selenium_driver.wait_multi import WebDriverWaitMulti

log = logging.getLogger('microstrategy_selenium.microstrategy_selenium.dashboard_functions')


def search(driver, name):
    try:  
        search_box = driver.find_element_by_xpath("//*[@id=\"searchTextBar\"]")
        search_box.clear()
        search_box.send_keys(name)
        search_box.send_keys(Keys.ENTER)
        time.sleep(1)
        WebDriverWait(
            driver,
            timeout=30,
        ).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[@id=\"centerLocation\"]/div")
            )
        )
    except NoSuchElementException:
        return False
    return True

    
def list_dashboards_shown(driver):
    elements = driver.find_elements_by_xpath("//*[@id=\"centerLocation\"]/div")
    return elements


def beep():
    try:
        winsound.Beep(1000, 250)
    except RuntimeError:
        pass


def open_dashboard_by_name(driver, name, ou='Angola', timeout=30):
    search(driver, name)
    dashboard_list = list_dashboards_shown(driver)
    for dashboard_element in dashboard_list:
        entry_dashboard_name = dashboard_element.find_element_by_xpath('.//h4').text.strip()
        if entry_dashboard_name.lower() == name.lower():
            link = dashboard_element.find_element_by_xpath(".//div/div[1]/a/div")
            link.click()
            WebDriverWait(driver, timeout).until(EC.invisibility_of_element((By.XPATH, "//*[@id=\"searchTextBar\"]")))
            try:
                result, result_element = WebDriverWaitMulti(
                    driver,
                    (timeout*2)*20).until_in_iframe(
                        EC.visibility_of_element_located,
                        [
                            (3, (By.XPATH, "//div[contains(@class,'mstrmojo-coverpage')]/div[1]/img")),
                            (-1, (By.XPATH, "//*[@id=\"navbarDropdownMenuLink\"]"))
                        ]
                    )
            except TimeoutException:
                return False
            # If found navbarDropdownMenuLink
            if result == 1:
                cs = driver.find_element_by_id('CountrySelection')
                for col in cs.find_elements_by_xpath(".//div"):
                    for country in col.find_elements_by_xpath(".//label"):
                        if country.text.lower() == ou.lower():
                            country.click()
                            driver.find_element_by_id('MultiOU').click()
                            # Wait for js code to create iframe
                            time.sleep(0.5)
                            driver.switch_to.frame(driver.find_elements_by_tag_name('iframe')[3])
                            WebDriverWait(
                                driver,
                                timeout,
                            ).until(
                                EC.visibility_of_element_located(
                                    (By.XPATH, "//div[contains(@class,'mstrmojo-coverpage')]/div[1]/img")
                                )
                            )
                            beep()
                            return True
            beep()
            return True
    return False


def driver_wait_for_load(driver: webdriver, timeout=15*60):
    done = False
    start_time = datetime.now()
    while not done:
        try:
            title = driver.title.lower()
        except UnexpectedAlertPresentException:
            js_alert = driver.switch_to.alert
            alert_text = 'Alert: ' + js_alert.text
            # accept the alert
            js_alert.accept()
            raise ValueError('JS Alert: ' + alert_text)

        if 'executing' not in title:
            if 'Bad Request' in title:
                raise ValueError(title)
            elif 'welcome. microstrategy' in title:
                raise ValueError('Got welcome page')
            elif 'login. microstrategy' in title:
                raise ValueError('Got login page!')

            elapsed_time = datetime.now() - start_time
            if timeout:
                if elapsed_time.total_seconds() > timeout:
                    raise TimeoutError()

            try:
                error_box = driver.find_element_by_xpath("//div[contains(@class, 'alert-content')]")
                raise ValueError('alert-content=' + error_box.text)
            except NoSuchElementException:
                pass
            #

            try:
                driver.find_element_by_xpath("//div[contains(@class, 'mstrPromptEditorBookContainer')]")
                raise ValueError('Has un-answered prompts')
            except NoSuchElementException:
                pass

            try:
                error_box = driver.find_element_by_xpath("//div[contains(@class, 'mstrAlert')]")
                raise ValueError('mstrAlert=' + error_box.text)
            except NoSuchElementException:
                pass

            try:
                wait_sub_box = driver.find_element_by_xpath("//div[@id='waitBox']//div")
                if wait_sub_box.value_of_css_property('display') == 'none':
                    done = True
            except NoSuchElementException:
                done = True
        if not done:
            time.sleep(0.5)


def wait_dash_data_loaded(driver, timeout=30):
    try:
        # mstrWait -> mstrTitle -> Processing Request
        # //div[contains(@class,'vitara') and not(contains(@class,'vitara-'))  ]

        # Note: visibility_of_element_located does not work with mstrmojo-VIBox since there can be multiple of those
        # and it only finds the first

        done = False
        debug_msg_count = 0
        while not done:
            try:
                try:
                    title = driver.title.lower()
                except UnexpectedAlertPresentException:
                    js_alert = driver.switch_to.alert
                    alert_text = 'Alert: ' + js_alert.text
                    # accept the alert
                    js_alert.accept()
                    raise ValueError('JS Alert: ' + alert_text)

                if 'Bad Request' in title:
                    raise ValueError(title)
                elif 'welcome. microstrategy' in title:
                    raise ValueError('Got welcome page')
                elif 'login. microstrategy' in title:
                    raise ValueError('Got login page!')

                loading_element_found = False
                waitbox_list = find_optional_elements_by_xpath(
                    driver,
                    '//div[contains(@class, "mstrWaitBox")]'
                )
                for element in waitbox_list:
                    if element.is_displayed():
                        loading_element_found = True
                        break

                if not loading_element_found:
                    spinner_list = find_optional_elements_by_xpath(
                        driver,
                        "//*[contains(@class, 'spinner')]"
                    )
                    for element in spinner_list:
                        if element.is_displayed():
                            loading_element_found = True
                            break

                if not loading_element_found:
                    # Check for class mstrmojo-VIBox which appears on dossier pages with visuals
                    # Check for class mstrmojo-DocTextfield which appears on cover page type pages
                    # Check for mstrmojo-portlet-container or gm-main-container which appears on old VI style docs
                    # If any are found to be visible then assume we are done
                    # Note: Later check for vitara can change done to False
                    vi_box_list = find_optional_elements_by_xpath(
                        driver,
                        "//div[contains(@class,'mstrmojo-VIBox')]"
                        "|//div[contains(@class,'mstrmojo-portlet-container')]"
                        "|//div[contains(@class,'mstrmojo-DocTextfield')]"
                    )
                    shown_vi_box_count = 0
                    shown_vi_box_list = list()
                    hidden_vi_box_count = 0
                    for element in vi_box_list:
                        if element.is_displayed():
                            shown_vi_box_count += 1
                            shown_vi_box_list.append(element)
                            done = True
                        else:
                            hidden_vi_box_count += 1
                    if hidden_vi_box_count:
                        if debug_msg_count < 6:
                            debug_msg_count += 1
                            # log.debug(f'{hidden_vi_box_count} instances of mstrmojo-VIBox found but not displayed ({shown_vi_box_count} are shown)')

                    vitara_chart_list = list()
                    # Only look in visible vi_boxes for vitara_charts
                    for vi_vbox in shown_vi_box_list:
                        vitara_chart_list.extend(
                            find_optional_elements_by_xpath(
                                vi_vbox,
                                './/div[contains(@class, "vitara-chart-container")]'
                            )
                        )
                    for element in vitara_chart_list:
                        if element.is_displayed():
                            # Detect if vitara-chart spinner is gone but charts have not yet loaded
                            chart_contents = find_optional_elements_by_xpath(
                                driver,
                                './*'
                            )
                            if len(chart_contents) > 0:
                                done = True
                            else:
                                done = False
                                if debug_msg_count < 6:
                                    debug_msg_count += 1
                                    log.debug(f'vitara-chart-container found is empty')
                        else:
                            if debug_msg_count < 6:
                                debug_msg_count += 1
                                log.debug(f'vitara-chart-container found but is not displayed')
                            done = False
            except StaleElementReferenceException:
                done = False
                # Note: Must not be done if the DOM changed
            if not done:
                time.sleep(0.5)

            """
            <div class="mstrmojo-UnitContainer-content" style="height: 373px; width: 1749px;">
                <div id="mstr607" class="ctrlOverlay or-h ghost-tall ghost-grey" style="display: block; height: 373px; width: 1749px;">
                    <div class="error-msg"><div class="error-content" style="visibility: visible">
                        No data returned for this view. This might be because the applied filter excludes all data.
                    </div>
                </div>
            </div>
            """
    except TimeoutException:
        return False
    return True


def content_categories(driver) -> list:
    try:
        categories_list = driver.find_elements_by_xpath(
            '//div[contains(@class, "mstrmojo-VIPanelContents")]/div'
        )
    except NoSuchElementException:
        return []
    return categories_list


def category_name(category_element) -> str:
    title = category_element.find_elements_by_xpath(
        './div[1]'
    )
    if len(title) == 1:
        return title[0].text
    else:
        raise ValueError('Title not found')


def content_category_sections(category_element) -> list:
    try:
        sections_list = category_element.find_elements_by_xpath(
            './div[contains(@class, "mstrmojo-VIPanel-content")]'
            '/div[2]/div/div'
        )
    except NoSuchElementException:
        return []
    return sections_list


def horizontal_tabs(driver) -> list:
    try:
        tab_list = driver.find_elements_by_xpath(
            '//div[contains(@class, "mstrmojo-OIVMPage-layout")]'
            '/div[contains(@class, "mstrmojo-tabcontainer")]'
            '/div[1]/div/div//span'
        )
    except NoSuchElementException:
        return []
    return tab_list


def select_content_section_and_wait(driver, section_element, timeout=60):
    start_time = datetime.now()
    done = False
    while not done:
        try:
            driver.execute_script("arguments[0].scrollIntoView();", section_element)
            section_element.click()
            wait_dash_data_loaded(driver, timeout)
            done = True
        except NoSuchElementException as e:
            if (datetime.now() - start_time).total_seconds() > timeout:
                raise WebDriverException(
                    f'select_content_section_and_wait timed out waiting for {e} to clear.  '
                    f'Waited {(datetime.now() - start_time).total_seconds()} seconds'
                )
            else:
                time.sleep(1)
        except ElementClickInterceptedException as e:
            if (datetime.now() - start_time).total_seconds() > timeout:
                raise WebDriverException(
                    f'select_content_section_and_wait timed out waiting for {e} to clear.  '
                    f'Waited {(datetime.now() - start_time).total_seconds()} seconds')
            else:
                time.sleep(1)
    return True


def get_html(element) -> str:
    return element.get_attribute('innerHTML')
