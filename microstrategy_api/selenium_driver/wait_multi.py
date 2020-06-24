# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import time

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

POLL_FREQUENCY = 0.5  # How long to sleep inbetween calls to the method
IGNORED_EXCEPTIONS = (NoSuchElementException,)  # exceptions ignored during calls to the method


class WebDriverWaitMulti(object):
    def __init__(self, driver, timeout, poll_frequency=POLL_FREQUENCY, ignored_exceptions=None):
        """Constructor, takes a WebDriver instance and timeout in seconds.

           :Args:
            - driver - Instance of WebDriver (Ie, Firefox, Chrome or Remote)
            - timeout - Number of seconds before timing out
            - poll_frequency - sleep interval between calls
              By default, it is 0.5 second.
            - ignored_exceptions - iterable structure of exception classes ignored during calls.
              By default, it contains NoSuchElementException only.

           Example:
            from selenium.webdriver.support.ui import WebDriverWait \n
            element = WebDriverWait(driver, 10).until(lambda x: x.find_element_by_id("someId")) \n
            is_disappeared = WebDriverWait(driver, 30, 1, (ElementNotVisibleException)).\ \n
                        until_not(lambda x: x.find_element_by_id("someId").is_displayed())
        """
        self._driver = driver
        self._timeout = timeout
        self._poll = poll_frequency
        # avoid the divide by zero
        if self._poll == 0:
            self._poll = POLL_FREQUENCY
        exceptions = list(IGNORED_EXCEPTIONS)
        if ignored_exceptions is not None:
            try:
                exceptions.extend(iter(ignored_exceptions))
            except TypeError:  # ignored_exceptions is not iterable
                exceptions.append(ignored_exceptions)
        self._ignored_exceptions = tuple(exceptions)

    def __repr__(self):
        return '<{0.__module__}.{0.__name__} (session="{1}")>'.format(
            type(self), self._driver.session_id)

    def until(self, method, locators, message=''):
        """
        Calls the method provided with the driver as an argument until the
        return value is not False.

        Note: If a locator finds multiple matches, it evaluates on the first match.
        """
        screen = None
        stacktrace = None

        end_time = time.time() + self._timeout
        while True:
            counter = -1
            for locator in locators:
                counter += 1
                try:
                    m = method(locator)
                    value = m(self._driver)
                    if value:
                        return counter, value
                except self._ignored_exceptions as exc:
                    screen = getattr(exc, 'screen', None)
                    stacktrace = getattr(exc, 'stacktrace', None)
            time.sleep(self._poll)
            if time.time() > end_time:
                break
        raise TimeoutException(message, screen, stacktrace)

    def until_not(self, method, locators, message=''):
        """
        Calls the method provided with the driver as an argument until the return value is False.

        Note: If a locator finds multiple matches, it evaluates on the first match.
        """
        end_time = time.time() + self._timeout
        while True:
            l = -1
            for locator in locators:
                l += 1
                try:
                    m = method(locator)
                    value = m(self._driver)
                    if not value:
                        return l, value
                except self._ignored_exceptions as exc:
                    # screen = getattr(exc, 'screen', None)
                    # stacktrace = getattr(exc, 'stacktrace', None)
                    pass
            time.sleep(self._poll)
            if time.time() > end_time:
                break
        raise TimeoutException(message)

    def until_in_iframe(self, method, locators_w_iframes, message=''):
        """
        Calls the method provided with the driver as an argument until the return value is not False.

        Note: If a locator finds multiple matches, it evaluates on the first match.
        """
        screen = None
        stacktrace = None

        end_time = time.time() + self._timeout
        while True:
            counter = -1
            for tupl in locators_w_iframes:
                counter += 1
                try:
                    if tupl[0] > -1:
                        self._driver.switch_to.frame(self._driver.find_elements_by_tag_name('iframe')[tupl[0]])
                    else:
                        self._driver.switch_to.parent_frame()
                    m = method(tupl[1])
                    value = m(self._driver)
                    if value:
                        return counter, value
                except self._ignored_exceptions as exc:
                    screen = getattr(exc, 'screen', None)
                    stacktrace = getattr(exc, 'stacktrace', None)
            time.sleep(self._poll)
            if time.time() > end_time:
                break
        raise TimeoutException(message, screen, stacktrace)

    def until_not_in_iframe(self, method, locators_w_iframes, message=''):
        """
        Calls the method provided with the driver as an argument until the return value is False.

        Note: If a locator finds multiple matches, it evaluates on the first match.
        """
        end_time = time.time() + self._timeout
        while True:
            counter = -1
            for tupl in locators_w_iframes:
                counter += 1
                try:
                    self._driver.switch_to.frame(self._driver.find_elements_by_tag_name('iframe')[tupl[0]])
                    m = method(tupl[1])
                    value = m(self._driver)
                    if not value:
                        return counter, value
                except self._ignored_exceptions as exc:
                    # screen = getattr(exc, 'screen', None)
                    # stacktrace = getattr(exc, 'stacktrace', None)
                    pass
            time.sleep(self._poll)
            if time.time() > end_time:
                break
        raise TimeoutException(message)
