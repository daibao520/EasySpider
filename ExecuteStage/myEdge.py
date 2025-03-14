from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException, InvalidSelectorException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import Select
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium import webdriver


class MyEdge(webdriver.Ie):
    def __init__(self, *args, **kwargs):
        self.iframe_env = False  # 现在的环境是root还是iframe
        super().__init__(*args, **kwargs)  # 调用父类的 __init__

    def find_element_recursive(self, by, value, frames):
        for frame in frames:
            try:
                try:
                    self.switch_to.frame(frame)
                except StaleElementReferenceException:
                    # If the frame has been refreshed, we need to switch to the parent frame first,
                    self.switch_to.parent_frame()
                    self.switch_to.frame(frame)
                try:
                    # !!! Attempt to find the element in the current frame, not the context (iframe environment will not change to default), therefore we use super().find_element instead of self.find_element
                    element = super(MyEdge, self).find_element(by=by, value=value)
                    return element
                except NoSuchElementException:
                    # Recurse into nested iframes
                    nested_frames = super(MyEdge, self).find_elements(By.CSS_SELECTOR, "iframe")
                    if nested_frames:
                        element = self.find_element_recursive(by, value, nested_frames)
                        if element:
                            return element
            except Exception as e:
                print(f"Exception while processing frame: {e}")

        raise NoSuchElementException(f"Element {value} not found in any frame or iframe")

    def find_element(self, by=By.ID, value=None, iframe=False):
        self.switch_to.default_content()  # Switch back to the main document
        self.iframe_env = False
        if iframe:
            frames = self.find_elements(By.CSS_SELECTOR, "iframe")
            if not frames:
                raise NoSuchElementException(f"No iframes found in the current page while searching for {value}")
            self.iframe_env = True
            element = self.find_element_recursive(by, value, frames)
        else:
            # Find element in the main document as normal
            element = super(MyEdge, self).find_element(by=by, value=value)
        return element

    def find_elements_recursive(self, by, value, frames):
        for frame in frames:
            try:
                try:
                    self.switch_to.frame(frame)
                except StaleElementReferenceException:
                    # If the frame has been refreshed, we need to switch to the parent frame first,
                    self.switch_to.parent_frame()
                    self.switch_to.frame(frame)
                # Directly find elements in the current frame
                elements = super(MyEdge, self).find_elements(by=by, value=value)
                if elements:
                    return elements
                # Recursively search for elements in nested iframes
                nested_frames = super(MyEdge, self).find_elements(By.CSS_SELECTOR, "iframe")
                if nested_frames:
                    elements = self.find_elements_recursive(by, value, nested_frames)
                    if elements:
                        return elements
            except Exception as e:
                print(f"Exception while processing frame: {e}")

        raise NoSuchElementException(f"Elements with {value} not found in any frame or iframe")

    def find_elements(self, by=By.ID, value=None, iframe=False):
        self.switch_to.default_content()  # Switch back to the main document
        self.iframe_env = False
        if iframe:
            frames = self.find_elements(By.CSS_SELECTOR, "iframe")
            if not frames:
                return []  # Return an empty list if no iframes are found
            self.iframe_env = True
            elements = self.find_elements_recursive(by, value, frames)
        else:
            # Find elements in the main document as normal
            elements = super(MyEdge, self).find_elements(by=by, value=value)
        return elements
