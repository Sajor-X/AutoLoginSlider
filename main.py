import random
import time
from urllib import request

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# your account and password
EMAIL = 'xxxxx'
PASSWORD = 'xxxxx'
BORDER = 0
SLIDER_TOP = 110


class CrackOceanEngine(object):
    def __init__(self):
        self.url = 'https://business.oceanengine.com/site/login'
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.email = EMAIL
        self.password = PASSWORD

        self.alpha = 1.65

    def open(self):
        """
        打开网页输入用户名密码
        :return: None
        """
        self.browser.get(self.url)
        email = self.wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        password = self.wait.until(EC.presence_of_element_located((By.NAME, 'password')))

        email.send_keys(self.email)
        password.send_keys(self.password)

    def __del__(self):
        self.browser.close()

    def login(self):
        print("login success.")
        user_name = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'index_header-user-name__5Ol1I'))).getText()
        print(user_name)

    def get_login_button(self):
        """
        获取登陆按钮
        :return:
        """
        return self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'account-center-action-button')))

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        return self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'secsdk-captcha-drag-sliding')))

    def get_slider_img(self):
        """
        获取滑块图片
        :return:
        """
        return self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'captcha_verify_img_slide')))

    def get_verify_img(self):
        """
        获取缺口图片
        :return:
        """
        return self.wait.until(EC.presence_of_element_located((By.ID, 'captcha-verify-image')))

    def get_gap(self, slider_img, verify_img):
        """
        获取缺口偏移量
        :param slider_img: 滑块图片
        :param verify_img: 验证码缺口图片
        :return:
        """

        # 获取缺口大致高度 y轴
        top = slider_img.value_of_css_property("top")
        top_px = int(float(top[:-2]) * self.alpha)

        img_url = verify_img.get_attribute("src")
        print("验证码图片url：%s" % img_url)
        # 存储验证码图片位置
        request.urlretrieve(img_url, 'imgs.jpg')

        verify_img = plt.imread("./imgs.jpg")
        # 读取图片 缩小范围
        img = verify_img[top_px: top_px + SLIDER_TOP]

        plt.imsave('immg1.jpg', img)
        # 这个是设置的滤波，也就是卷积核
        fil = np.array([[1, 0, -2],
                        [1, 0, -2],
                        [1, 0, -2]])

        # 使用opencv的卷积函数
        res = cv2.filter2D(img, -1, fil)
        plt.imsave('immg2.jpg', res)
        x, y, z = res.shape

        res_list = []
        for i in range(x):
            for j in range(y):
                if (res[i, j] == (255, 255, 255)).all():
                    res_list.append(j)

        gap = pd.Series(np.array(res_list)).mode()[0]

        plt.imsave('img_final.jpg', verify_img[:, gap:])
        return gap

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹

        拿到移动轨迹，模仿人的滑动行为，先匀加速后匀减速
        匀变速运动基本公式：
        ①v=v₀ + at
        ②s=v₀t + (1/2)at²
        ③v²-v₀²=2as

        :param distance: 偏移量 需要移动的距离
        :return: 移动轨迹 存放每0.2秒移动的距离
        """
        # 移动轨迹 位移/轨迹列表，列表内的一个元素代表0.2s的位移
        track = []
        # 当前位移
        current = 0
        # 减速阈值  到达mid值开始减速
        mid = distance * 7 / 10
        # 单位时间为0.2s来统计轨迹，轨迹即0.2内的位移
        t = 0.9
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速运动
                # 加速度越小，单位时间的位移越小,模拟的轨迹就越多越详细
                a = random.randint(1, 3)
            else:
                # 减速运动
                a = -random.randint(2, 4)

            # 初速度v₀
            v0 = v
            # 当前速度v = v₀ + at
            v = v0 + a * t
            # 移动距离s = v₀t + 1/2 * a * t^2
            s = v0 * t + 0.5 * a * t * t
            # 当前位移
            current += s
            # 加入轨迹
            track.append(round(s))

            # 速度已经达到v,该速度作为下次的初速度
            v = v0 + a * t
        track.append(distance - sum(track))
        return track

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    def crack(self):
        # 输入用户名密码
        self.open()
        # 点击登陆按钮
        login_button = self.get_login_button()
        login_button.click()
        # 获取滑块
        slider = self.get_slider()
        # 获取验证码滑块图片
        slider_img = self.get_slider_img()
        # 获取验证码图片
        verify_img = self.get_verify_img()
        # 获取缺口位置
        gap = self.get_gap(slider_img, verify_img)

        # 减去缺口位移
        gap = int(gap / self.alpha) - BORDER

        # 获取移动轨迹
        track = self.get_track(gap)
        print('滑动轨迹', track)
        print('缺口: %s, 滑动轨迹: %s' % (gap, sum(track)))
        # 拖动滑块
        self.move_to_gap(slider, track)

        try:
            print(self.browser.find_element_by_class_name("msg").text)
            print(self.browser.find_element_by_class_name("jwiskW").text)
            success = self.wait.until(
                EC.text_to_be_present_in_element((By.CLASS_NAME, 'jwiskW'), '验证失败，请根据提示重新操作'))
            print(success)

            # 失败后重试
            if not success:
                self.crack()
            else:
                self.login()
        except Exception as e:
            print(e)
            self.crack()


if __name__ == '__main__':
    crack = CrackOceanEngine()
    crack.crack()
