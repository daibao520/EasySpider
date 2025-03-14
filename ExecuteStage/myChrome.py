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
from selenium.webdriver.common.keys import Keys
import sys
import json


desired_capabilities = DesiredCapabilities.CHROME
desired_capabilities["pageLoadStrategy"] = "none"

global_use_my_sloution = True

if global_use_my_sloution:
    from seleniumwire import webdriver
else:
    from selenium import webdriver


def parse_agent_info(sourceStr: str):
    # sourceStr = "socks5://coin2023static_ip-200.234.175.195:14a2e60b137a0@55a37a48a0:12324"
    sourceStr = "socks5://coin2023static_ip-203.166.129.40:14a903beb24a6@1d60fc7cb4:12324"
    sIndex = sourceStr.index("-")
    subStr = sourceStr[sIndex + 1 :]
    sIndex = subStr.index(":")
    ipStr = subStr[:sIndex]
    sIndex2 = subStr.index("@")
    accountStr = subStr[sIndex + 1 : sIndex2]
    sIndex3 = subStr.index(":", sIndex2)
    passwrodStr = subStr[sIndex2 + 1 : sIndex3]
    portStr = subStr[sIndex3 + 1 :]
    # resultStr = (
    #     f"socks5://{accountStr}:{passwrodStr}@{ipStr}:{portStr}",
    # )  # 例如 "socks5://john:pass123@45.76.123.88:1080"
    result = {
        "account": accountStr,
        "password": passwrodStr,
        "ip": ipStr,
        "port": portStr,
    }
    return result

def parse_agent_info2(sourceStr: str):
    strArr = sourceStr.split("@")
    accountArr = strArr[0].split(":")
    addressArr = strArr[1].split(":")
    result = {
        "account": accountArr[0],
        "password": accountArr[1],
        "ip": addressArr[0],
        "port": addressArr[1],
    }
    return result

class MyChrome(webdriver.Chrome):

    def __init__(self, mode="local_driver", user_info: dict = None, *args, **kwargs):
        self.iframe_env = False  # 现在的环境是root还是iframe
        self.mode = mode

        seleniumwire_options = None
        if global_use_my_sloution:
            proxy = user_info.get("result").get("proxy")
            if len(proxy) > 0:
                agent_info = parse_agent_info2(proxy)
                seleniumwire_options = {
                    "proxy": {
                        "http": f'socks5://{agent_info["account"]}:{agent_info["password"]}@{agent_info["ip"]}:{agent_info["port"]}',
                        "https": f'socks5://{agent_info["account"]}:{agent_info["password"]}@{agent_info["ip"]}:{agent_info["port"]}',
                    },
                }
            super().__init__(*args, seleniumwire_options=seleniumwire_options, **kwargs)
        else:
            super().__init__(*args, **kwargs)

        # LW修改，添加指纹
        if global_use_my_sloution:
            fingerprint = user_info.get("result").get("fingerprint").get("fingerprint")

            if fingerprint.get("navigator"):
                self.fake_navigator_data(fingerprint.get("navigator"))
            if fingerprint.get("battery"):
                self.fake_battery_data(fingerprint.get("battery"))
            if fingerprint.get("videoCard"):
                self.fake_video_card_data(fingerprint.get("videoCard"))
            if fingerprint.get("audioCodecs"):
                self.fake_audio_codecs_data(fingerprint.get("audioCodecs"))
            if fingerprint.get("pluginsData"):
                # 基本没用
                self.fake_plugins_data(fingerprint.get("pluginsData"))
            if fingerprint.get("multimediaDevices"):
                self.fake_multimedia_devices_data(fingerprint.get("multimediaDevices"))
            if fingerprint.get("fonts"):
                self.fake_fonts_data(fingerprint.get("fonts"))

    def fake_navigator_data(self, config: dict) -> None:

        # 设置UserAgent相关参数
        user_agent = config.get("userAgent", "")
        accept_language = config.get("language", "en-US")
        platform = config.get("platform", "Win32")

        # 处理UserAgent元数据
        user_agent_data = config.get("userAgentData", {})
        ua_metadata = {
            "brands": user_agent_data.get("brands", []),
            "fullVersion": user_agent_data.get("uaFullVersion", ""),
            "fullVersionList": user_agent_data.get("fullVersionList", []),
            "platform": user_agent_data.get("platform", "Windows"),
            "platformVersion": user_agent_data.get("platformVersion", "10.0.0"),
            "architecture": user_agent_data.get("architecture", "x86"),
            "model": user_agent_data.get("model", ""),
            "mobile": user_agent_data.get("mobile", False),
        }

        # 执行CDP命令设置UA覆盖
        self.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": user_agent,
                "acceptLanguage": accept_language,
                "platform": platform,
                "userAgentMetadata": ua_metadata,
            },
        )

        # 构建属性覆盖脚本
        script = ""
        properties = {
            "deviceMemory": config.get("deviceMemory"),
            "hardwareConcurrency": config.get("hardwareConcurrency"),
            "maxTouchPoints": config.get("maxTouchPoints"),
            "language": config.get("language"),
            "languages": config.get("languages"),
            "webdriver": config.get("webdriver"),
            "doNotTrack": config.get("doNotTrack"),
            "vendor": config.get("vendor"),
            "appName": config.get("appName"),
            "appVersion": config.get("appVersion"),
            "product": config.get("product"),
            "productSub": config.get("productSub"),
            "vendorSub": config.get("vendorSub"),
            "oscpu": config.get("oscpu"),
        }

        for prop, value in properties.items():
            if value is not None:
                value_str = json.dumps(value)
                script += f"""
                Object.defineProperty(navigator, '{prop}', {{
                    get: () => {value_str}
                }});
                """

        # 处理额外属性
        extra_props = config.get("extraProperties", {})
        for prop, value in extra_props.items():
            value_str = json.dumps(value)
            script += f"""
            Object.defineProperty(navigator, '{prop}', {{
                get: () => {value_str}
            }});
            """

        # 注入脚本到所有新页面
        if script.strip():
            self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})

    def fake_battery_data(self, config: dict) -> None:
        # 基础参数，必须启用电池覆盖
        cdp_params = {"enabled": True}

        # 验证并映射字段
        if "level" not in config or "charging" not in config:
            return

        level = config["level"]
        if not (0 <= level <= 1):
            return

        cdp_params["batteryLevel"] = level

        cdp_params["charging"] = config["charging"]

        # 处理充电/放电时间（单位：秒）
        charging_time = config.get("chargingTime")
        if charging_time is not None:
            if charging_time < 0:
                return
            cdp_params["chargingTime"] = charging_time

        discharging_time = config.get("dischargingTime")
        if discharging_time is not None:
            if discharging_time < 0:
                return
            cdp_params["dischargingTime"] = discharging_time

        # 执行CDP命令
        try:
            self.execute_cdp_cmd("Emulation.setBatteryOverride", cdp_params)
        except Exception as e:
            js_script = f"""
                Object.defineProperty(navigator, 'getBattery', {{
                    value: () => Promise.resolve({{
                        level: {cdp_params["batteryLevel"]},
                        charging: {cdp_params["charging"]},
                        chargingTime: {cdp_params.get("chargingTime", "Infinity")},
                        dischargingTime: {cdp_params["dischargingTime"]}
                    }}),
                    configurable: false
                }});
            """
            self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_script})

    def fake_video_card_data(self, config: dict) -> None:
        vendor = config["vendor"]
        renderer = config["renderer"]

        # 参数校验
        if not isinstance(vendor, str) or not vendor.strip():
            return
        if not isinstance(renderer, str) or not renderer.strip():
            return

        # 构造覆盖显卡属性的JS脚本
        js_script = f"""
            Object.defineProperty(navigator.gpu, 'vendor', {{
                get: () => "{vendor}",
                configurable: true,
                enumerable: true
            }});
            Object.defineProperty(navigator.gpu, 'renderer', {{
                get: () => "{renderer}",
                configurable: true,
                enumerable: true
            }});
        """

        # 拦截WebGL上下文创建
        js_script += """
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(...args) {
            const context = originalGetContext.apply(this, args);
            if (context && context.getParameter) {
                const originalGetParameter = context.getParameter;
                context.getParameter = function(pname) {
                    if (pname === 37445) { // UNMASKED_VENDOR_WEBGL
                        return "%s";
                    }
                    if (pname === 37446) { // UNMASKED_RENDERER_WEBGL
                        return "%s";
                    }
                    return originalGetParameter.apply(this, arguments);
                };
            }
            return context;
        };
        """ % (
            vendor,
            renderer,
        )

        # 通过CDP在页面加载前注入脚本
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_script})

    def fake_audio_codecs_data(self, config: dict) -> None:

        # 预定义编解码器名称到MIME类型的映射
        MIME_MAPPING = {
            "aac": ["audio/aac", 'audio/mp4; codecs="aac"'],
            "m4a": ["audio/mp4", "audio/x-m4a"],
            "mp3": ["audio/mpeg"],
            "ogg": ["audio/ogg", 'audio/ogg; codecs="vorbis"'],
            "wav": ["audio/wav"],
        }

        # 验证输入数据
        invalid_keys = [k for k in config if k not in MIME_MAPPING]
        if invalid_keys:
            return

        # 构建MIME类型到伪造值的映射
        codec_map = {}
        for codec_name, fake_value in config.items():
            for mime_type in MIME_MAPPING[codec_name]:
                codec_map[mime_type] = fake_value

        # 生成覆盖脚本
        js_script = f"""
        (function() {{
            const originalCanPlayType = HTMLAudioElement.prototype.canPlayType;
            const codecMap = {json.dumps(codec_map)};

            HTMLAudioElement.prototype.canPlayType = function(type) {{
                return codecMap[type] || originalCanPlayType.call(this, type);
            }};
        }})();
        """
        # 注入脚本到所有新页面
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_script})

    def fake_plugins_data(self, config: dict) -> None:
        # 转换mimeTypes字符串为对象
        mime_type_objects = []
        for mt_str in config.get("mimeTypes", []):
            if "~~" in mt_str:
                desc, mime_type, suffixes = mt_str.split("~~")
                mime_type_objects.append(
                    {
                        "type": mime_type,
                        "suffixes": suffixes,
                        "description": desc,
                        "enabledPlugin": next(
                            (
                                p["name"]
                                for p in config["plugins"]
                                if any(mt["type"] == mime_type for mt in p["mimeTypes"])
                            ),
                            None,
                        ),
                    }
                )

        # 合并配置中的mimeTypes
        for plugin in config["plugins"]:
            mime_type_objects.extend(plugin["mimeTypes"])

        # 生成注入脚本
        js_script = f"""
        (function() {{
            // 保存原始插件引用（用于回退）
            const origPlugins = navigator.plugins;
            const origMimeTypes = navigator.mimeTypes;

            // 生成伪造插件对象
            const fakePlugins = {json.dumps(config['plugins'])}.map(p => {{
                const plugin = new Plugin(
                    p.name,
                    p.description,
                    p.filename,
                    p.mimeTypes.length
                );

                // 伪造 MIME 类型数组
                plugin.mimeTypes = new MimeTypeArray();
                Object.defineProperty(plugin.mimeTypes, 'length', {{ value: p.mimeTypes.length }});

                p.mimeTypes.forEach((mt, index) => {{
                    plugin.mimeTypes[index] = new MimeType(
                        mt.type,
                        mt.description,
                        mt.suffixes,
                        plugin  // enabledPlugin
                    );
                }});

                return plugin;
            }});

            // 重写 navigator.plugins 的访问逻辑
            Object.defineProperty(navigator, 'plugins', {{
                get: () => new Proxy(fakePlugins, {{
                    get(target, prop) {{
                        return Reflect.get(target, prop) || origPlugins[prop];
                    }}
                }}),
                configurable: true,
                enumerable: true
            }});

            // 重写 navigator.mimeTypes 的访问逻辑
            Object.defineProperty(navigator, 'mimeTypes', {{
                get: () => new Proxy({json.dumps(mime_type_objects)}, {{
                    get(target, prop) {{
                        return Reflect.get(target, prop) || origMimeTypes[prop];
                    }}
                }}),
                configurable: true,
                enumerable: true
            }});
        }})();
        """

        # 注入伪造逻辑
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_script})

    def fake_multimedia_devices_data(self, config: dict) -> None:

        # 合并所有设备数据
        all_devices = []
        for category in ["micros", "webcams", "speakers"]:
            all_devices.extend(config.get(category, []))

        # 生成设备枚举脚本
        js_script = f"""
        (function() {{
            // 保存原始方法引用
            const origEnumerateDevices = navigator.mediaDevices.enumerateDevices;
            const origGetUserMedia = navigator.mediaDevices.getUserMedia;

            // 伪造设备列表
            const fakeDevices = {json.dumps(all_devices)};

            // 覆盖设备枚举方法
            navigator.mediaDevices.enumerateDevices = async function() {{
                // 返回伪造设备列表
                return fakeDevices.map(d => ({{
                    ...d,
                    // 自动填充缺失字段
                    deviceId: d.deviceId || Math.random().toString(36).substr(2),
                    groupId: d.groupId || Math.random().toString(36).substr(2),
                    label: d.label || (d.kind === 'audioinput' ? 'Default Microphone'
                        : d.kind === 'videoinput' ? 'Default Camera'
                        : 'Default Speaker')
                }}));
            }};

            // 覆盖权限检查逻辑
            navigator.permissions.query = async (permissionDesc) => {{
                const permissionMap = {{
                    'microphone': 'granted',
                    'camera': 'granted'
                }};
                return {{
                    state: permissionMap[permissionDesc.name] || 'prompt',
                    onchange: null
                }};
            }};

            // 覆盖getUserMedia方法以匹配伪造设备
            navigator.mediaDevices.getUserMedia = function(constraints) {{
                const deviceKindMap = {{
                    audio: 'audioinput',
                    video: 'videoinput'
                }};
                const requestedKind = deviceKindMap[Object.keys(constraints)[0]];
                const device = fakeDevices.find(d => d.kind === requestedKind);

                if (!device) {{
                    return Promise.reject(new DOMException('No device found', 'NotFoundError'));
                }}

                // 返回虚拟媒体流
                return Promise.resolve({{
                    getTracks: () => [{{
                        stop: () => {{}},
                        getSettings: () => ({{
                            deviceId: device.deviceId,
                            groupId: device.groupId
                        }})
                    }}]
                }});
            }};
        }})();
        """

        # 注入脚本到所有新页面
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_script})

    def fake_fonts_data(self, config: list) -> None:

        # 生成字体对象结构
        font_objects = [{"family": font, "postscriptName": font.replace(" ", "")} for font in config]

        # 构建注入脚本
        js_script = f"""
        (function() {{
            // 保存原始方法引用
            const origEnumerate = navigator.fonts ? navigator.fonts.enumerate : null;
            const origCheckFont = window.CanvasRenderingContext2D?.prototype?.checkFont || null;

            // 伪造字体枚举（现代API）
            if (navigator.fonts) {{
                navigator.fonts.enumerate = async function() {{
                    return {json.dumps(font_objects)};
                }};
            }}

            // 伪造Flash检测方式
            Object.defineProperty(document, 'fonts', {{
                get: () => ({{
                    ready: Promise.resolve(),
                    check: (font, text) => true,
                    values: {json.dumps(font_objects)}.map(f => ({{
                        family: f.family,
                        postscriptName: f.postscriptName,
                        status: "loaded"
                    }}))
                }}),
                configurable: true
            }});

            // 覆盖Canvas字体检测
            if (origCheckFont) {{
                CanvasRenderingContext2D.prototype.checkFont = function(font) {{
                    return {json.dumps(config)}.includes(font);
                }};
            }}

            // 覆盖原生字体列表
            const origGetFonts = window.CSS?.getFonts || null;
            if (origGetFonts) {{
                window.CSS.prototype.getFonts = async function() {{
                    return {json.dumps(font_objects)};
                }};
            }}
        }})();
        """

        # 注入伪造逻辑
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_script})

    def fake_screen_data(self, screen_config: dict) -> None:

        # 基础CDP参数设置
        self.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": screen_config["width"],
                "height": screen_config["height"],
                "deviceScaleFactor": screen_config.get("devicePixelRatio", 1),
                "mobile": False,
                "viewport": {
                    "x": screen_config.get("screenX", 0),
                    "y": screen_config.get("screenY", 0),
                    "width": screen_config["width"],
                    "height": screen_config["height"],
                    "scale": 1,
                },
            },
        )

        # 构建屏幕覆盖脚本
        js_script = f"""
        (function() {{
            // 覆盖原生screen对象
            const fakeScreen = {{
                width: {screen_config["width"]},
                height: {screen_config["height"]},
                availWidth: {screen_config["availWidth"]},
                availHeight: {screen_config["availHeight"]},
                colorDepth: {screen_config["colorDepth"]},
                pixelDepth: {screen_config["pixelDepth"]},
                availTop: {screen_config.get("availTop", 0)},
                availLeft: {screen_config.get("availLeft", 0)}
            }};

            Object.defineProperty(window, 'screen', {{
                value: new Proxy(fakeScreen, {{
                    get(target, prop) {{
                        // 动态计算滚动偏移量
                        if (prop === 'availTop') return window.scrollY;
                        if (prop === 'availLeft') return window.scrollX;
                        return Reflect.get(target, prop);
                    }},
                    set() {{ return false; }}
                }}),
                configurable: false,
                enumerable: true
            }});

            // 覆盖视口相关参数
            Object.defineProperties(window, {{
                innerWidth: {{ value: {screen_config.get("innerWidth", 0)} }},
                outerWidth: {{ value: {screen_config["width"]} }},
                innerHeight: {{ value: {screen_config.get("innerHeight", 0)} }},
                outerHeight: {{ value: {screen_config["availHeight"]} }},
                pageXOffset: {{ value: {screen_config.get("pageXOffset", 0)} }},
                pageYOffset: {{ value: {screen_config.get("pageYOffset", 0)} }}
            }});

            // 覆盖文档尺寸参数
            Object.defineProperties(document.documentElement, {{
                clientWidth: {{ value: {screen_config.get("clientWidth", 0)} }},
                clientHeight: {{ value: {screen_config.get("clientHeight", 0)} }}
            }});

            // 覆盖HDR检测支持
            if (window.matchMedia) {{
                const origMatchMedia = window.matchMedia;
                window.matchMedia = function(media) {{
                    if (media === '(dynamic-range: high)') {{
                        return {{
                            matches: {str(screen_config.get("hasHDR", False)).lower()},
                            media: '(dynamic-range: high)'
                        }};
                    }}
                    return origMatchMedia.apply(this, arguments);
                }};
            }}
        }})();
        """

        # 注入伪造逻辑
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_script})

    def fake_locale_and_timezone(self, timezone: str, locale: str) -> None:
        # 通过CDP设置时区
        self.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": timezone})

        # 覆盖HTTP请求头中的Accept-Language (需启动参数)
        # 启动时需添加: options.add_argument(f"--lang={locale}")

        # 覆盖JavaScript中的本地化属性
        js_script = f"""
        (function() {{
            // 覆盖时区检测
            const originalToLocaleString = Date.prototype.toLocaleString;
            Date.prototype.toLocaleString = function(locales, options) {{
                return originalToLocaleString.call(this, '{locale}', options);
            }};

            // 覆盖Intl API
            const originalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(locales, options) {{
                return originalDateTimeFormat('{locale}', options);
            }};
        }})();
        """
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_script})

    # def find_element(self, by=By.ID, value=None, iframe=False):
    #     # 在这里改变查找元素的行为
    #     if self.iframe_env:
    #         super().switch_to.default_content()
    #         self.iframe_env = False
    #     if iframe:
    #         # 获取所有的 iframe
    #         try:
    #             iframes = super().find_elements(By.CSS_SELECTOR, "iframe")
    #         except Exception as e:
    #             print(e)
    #         find_element = False
    #         # 遍历所有的 iframe 并查找里面的元素
    #         for iframe in iframes:
    #             # 切换到 iframe
    #             super().switch_to.default_content()
    #             super().switch_to.frame(iframe)
    #             self.iframe_env = True
    #             try:
    #                 # 在 iframe 中查找元素
    #                 # 在这个例子中，我们查找 XPath 为 '//div[1]' 的元素
    #                 element = super().find_element(by=by, value=value)
    #                 find_element = True
    #             except NoSuchElementException as e:
    #                 print(f"No such element found in the iframe: {str(e)}")
    #             except Exception as e:
    #                 print(f"Exception: {str(e)}")
    #             # 完成操作后切回主文档
    #             # super().switch_to.default_content()
    #             if find_element:
    #                 return element
    #         if not find_element:
    #             raise NoSuchElementException
    #     else:
    #         return super().find_element(by=by, value=value)

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
                    element = super().find_element(by=by, value=value)
                    return element
                except NoSuchElementException:
                    # Recurse into nested iframes
                    nested_frames = super().find_elements(By.CSS_SELECTOR, "iframe")
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
            element = super().find_element(by=by, value=value)
        return element

    # def find_elements(self, by=By.ID, value=None, iframe=False):
    #     # 在这里改变查找元素的行为
    #     if self.iframe_env:
    #         super().switch_to.default_content()
    #         self.iframe_env = False
    #     if iframe:
    #         # 获取所有的 iframe
    #         iframes = super().find_elements(By.CSS_SELECTOR, "iframe")
    #         find_element = False
    #         # 遍历所有的 iframe 并找到里面的元素
    #         for iframe in iframes:
    #             # 切换到 iframe
    #             try:
    #                 super().switch_to.default_content()
    #                 super().switch_to.frame(iframe)
    #                 self.iframe_env = True
    #                 # 在 iframe 中查找元素
    #                 # 在这个例子中，我们查找 XPath 为 '//div[1]' 的元素
    #                 elements = super().find_elements(by=by, value=value)
    #                 if len(elements) > 0:
    #                     find_element = True
    #                 # 完成操作后切回主文档
    #                 # super().switch_to.default_content()
    #                 if find_element:
    #                     return elements
    #             except NoSuchElementException as e:
    #                 print(f"No such element found in the iframe: {str(e)}")
    #             except Exception as e:
    #                 print(f"Exception: {str(e)}")
    #         if not find_element:
    #             raise NoSuchElementException
    #     else:
    #         return super().find_elements(by=by, value=value)

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
                elements = super().find_elements(by=by, value=value)
                if elements:
                    return elements
                # Recursively search for elements in nested iframes
                nested_frames = super().find_elements(By.CSS_SELECTOR, "iframe")
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
            elements = super().find_elements(by=by, value=value)
        return elements


# MacOS不支持直接打包带Cloudflare的功能，如果要自己编译运行，可以把这个if去掉，然后配置好浏览器和driver路径
if sys.platform != "darwin":
    ES = True
    if ES:  # 用自己写的ES版本
        import undetected_chromedriver_ES as uc
    else:
        import undetected_chromedriver as uc

    class MyUCChrome(uc.Chrome):

        def __init__(self, *args, **kwargs):
            self.iframe_env = False  # 现在的环境是root还是iframe
            super().__init__(*args, **kwargs)  # 调用父类的 __init__

        def find_element(self, by=By.ID, value=None, iframe=False):
            # 在这里改变查找元素的行为
            if self.iframe_env:
                super().switch_to.default_content()
                self.iframe_env = False
            if iframe:
                # 获取所有的 iframe
                try:
                    iframes = super().find_elements(By.CSS_SELECTOR, "iframe")
                except Exception as e:
                    print(e)
                find_element = False
                # 遍历所有的 iframe 并找到里面的元素
                for iframe in iframes:
                    # 切换到 iframe
                    super().switch_to.default_content()
                    super().switch_to.frame(iframe)
                    self.iframe_env = True
                    try:
                        # 在 iframe 中查找元素
                        # 在这个例子中，我们查找 XPath 为 '//div[1]' 的元素
                        element = super().find_element(by=by, value=value)
                        find_element = True
                    except NoSuchElementException as e:
                        print(f"No such element found in the iframe: {str(e)}")
                    except Exception as e:
                        print(f"Exception: {str(e)}")
                    # 完成操作后切回主文档
                    # super().switch_to.default_content()
                    if find_element:
                        return element
                if not find_element:
                    raise NoSuchElementException
            else:
                return super().find_element(by=by, value=value)

        def find_elements(self, by=By.ID, value=None, iframe=False):
            # 在这里改变查找元素的行为
            if self.iframe_env:
                super().switch_to.default_content()
                self.iframe_env = False
            if iframe:
                # 获取所有的 iframe
                iframes = super().find_elements(By.CSS_SELECTOR, "iframe")
                find_element = False
                # 遍历所有的 iframe 并查找里面的元素
                for iframe in iframes:
                    # 切换到 iframe
                    try:
                        super().switch_to.default_content()
                        super().switch_to.frame(iframe)
                        self.iframe_env = True
                        # 在 iframe 中查找元素
                        # 在这个例子中，我们查找 XPath 为 '//div[1]' 的元素
                        elements = super().find_elements(by=by, value=value)
                        if len(elements) > 0:
                            find_element = True
                        # 完成操作后切回主文档
                        # super().switch_to.default_content()
                        if find_element:
                            return elements
                    except NoSuchElementException as e:
                        print(f"No such element found in the iframe: {str(e)}")
                    except Exception as e:
                        print(f"Exception: {str(e)}")
                if not find_element:
                    raise NoSuchElementException
            else:
                return super().find_elements(by=by, value=value)
