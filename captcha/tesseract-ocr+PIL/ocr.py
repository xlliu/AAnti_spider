#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import uuid
import os
import time
import pytesseract
import StringIO

from PIL import Image, ImageEnhance


'''
Eg:
    c = Captcha()
    c.decode_captcha(file_path)

Descript:
    1. 强化图片(增加对比度 亮度)
    2. 去单噪点
    3. 切割图片(向x轴投影)
    4. 去矢量形噪点 (分别向x轴，y轴投影, 找到连续且小于3的点)
    5. 删除空白图片
    6. 识别图片

'''

# 0 不开启图片保存 1 开启图片保存
OPEN_SAVE = 0
# 0 不开启统计计数 1 开启计数
OPEN_COUNTS = 0
# 0 网络图片来源 1 本地图片来源
LOCAL_IMAGE = 0

# 识别char参数
CONFIG_CHAR = "-psm 10 -c tessedit_char_whitelist=0123456789ABCEFGHJKLMNPQRSTUVWXYZabcdefghjklmnpqrstuvwxyz"


class Captcha(object):

    def __init__(self):
        if OPEN_COUNTS:
            self.counts = 0
            self.success_counts = 0
            self.errer_counts = 0
        self._white = (255, 255, 255)
        self._black = (0, 0, 0)
        pass

    def binarization1(self, _img):
        u"""识别."""
        char = self.img_to_str2(_img)
        if char:
            self._debug_captch_save(_img, 'split', char)
        return char

    def graying(self, img):
        # 将RGB 彩图强化 二值化
        enhancer = ImageEnhance.Contrast(img)  # 增加对比对
        img = enhancer.enhance(2)
        # enhancer = ImageEnhance.Sharpness(img) #锐化
        # img = enhancer.enhance(2)
        enhancer = ImageEnhance.Brightness(img)  # 二值化
        img = enhancer.enhance(2)
        img = self.set_white_x_y(img)
        img = self.clear_point(img)
        split_img = self.spilt_columns_captcha(img)
        img_list = [img.crop(i) for i in split_img]

        return img_list

    def img_to_str2(self, img):
        char = pytesseract.image_to_string(
            img, lang='eng', config=CONFIG_CHAR)
        return char

    def _deal_x_shadow(self, img_list):
        img_list = map(self.map_cols_to_x_captcha, img_list)
        return img_list

    def _deal_y_shadow(self, img_list):
        img_list = map(self.map_rows_to_y_captcha, img_list)
        return img_list

    def _deal_white_picture(self, img_list):
        for i, il in enumerate(img_list):
            _list_black = [1 for w in xrange(il.size[0]) 
                            for h in xrange(il.size[1]) 
                                if il.getpixel((w, h)) == self._black]
            if not _list_black:
                del img_list[i]
        return img_list

    def _daal_forecast_char(self, img_list):
        _char_all = map(self.binarization1, img_list)
        return _char_all

    def _deal_empty_char(self, _char_all):
        _char_list = filter(lambda x: x, _char_all)
        return _char_all

    def clear_point(self, im):
        '''清除单噪点
        '''
        _black = self._black
        _white = self._white
        for j in range(1, (im.size[1] - 1)):
            for i in range(1, (im.size[0] - 1)):
                _x_0_y_0 = (im.getpixel((i, j)) == _black)
                _x_down_y_0 = (im.getpixel((i, (j + 1))) == _white)
                _x_up_y_0 = (im.getpixel((i, (j - 1))) == _white)

                _x_0_y_left = (im.getpixel(((i - 1), j)) == _white)
                _x_down_y_left = (im.getpixel(((i - 1), (j + 1))) == _white)
                _x_up_y_left = (im.getpixel(((i - 1), (j - 1))) == _white)

                _x_0_y_right = (im.getpixel(((i + 1), j)) == _white)
                _x_down_y_right = (im.getpixel(((i + 1), (j + 1))) == _white)
                _x_up_y_right = (im.getpixel(((i + 1), (j - 1))) == _white)
                _alone_point = (_x_0_y_0 and _x_up_y_left and _x_up_y_0 and _x_up_y_right and _x_0_y_left and _x_0_y_right and _x_down_y_left and _x_down_y_0 and _x_down_y_right)

                if _alone_point:
                    im.putpixel([i, j], _white)
        return im

    def set_white_x_y(self, im):
        '''边缘填充
        '''
        _white = self._white
        _st_width = _st_high = 0
        _default_high = im.size[1] - 1
        _default_width = im.size[0] - 1
        for h in range(im.size[1]):
            for w in range(im.size[0]):
                _width_st_or_ed = (w == _st_width) or (w == _default_width)
                _high_st_or_ed = (h == _st_high) or (h == _default_high)
                if _width_st_or_ed or _high_st_or_ed:
                    im.putpixel([w, h], _white)

        return im

    def spilt_columns_captcha(self, im):
        '''横向沿x轴切割
        '''
        up = left = right = _black_flag = _tmp_flag = 0
        down = int(im.size[1]) - 1
        
        _split_list = []
        for w in xrange(left, im.size[0]):
            for h in xrange(1, im.size[1]):
                if im.getpixel((w, h)) == self._black:
                    _tmp_flag = 1
            if not _black_flag and _tmp_flag:
                _black_flag = 1
                left = w
            if _black_flag and not _tmp_flag:
                _black_flag = 0
                right = w
                _split_list.append(
                    (left - 1 if left else 0, up, right + 1 if right < im.size[0] else im.size[0], down))
            _tmp_flag = False
        return _split_list

    def map_rows_to_y_captcha(self, im):
        '''映射到y轴
        '''
        up = _black_flag = _tmp_flag = 0
        down = im.size[1]
        cut_lines_pixel_num = 3

        _y_pixel = []
        for h in xrange(up, down):
            for w in xrange(1, im.size[0]):
                if im.getpixel((w, h)) == self._black:
                    _tmp_flag = 1

            if _tmp_flag:
                _y_pixel.append(h)
            _tmp_flag = 0
        im = self.cut_y_lines_lt_num(im, _y_pixel, cut_lines_pixel_num)
        return im

    def cut_y_lines_lt_num(self, im, _y_pixel, num):
        '''切割y轴投影小于num像素
        找到像素片位置
        '''
        _is_one_y_pixel = 0
        list_y_lines = []
        for i, v in enumerate(_y_pixel):
            _ = v - i
            if _ != _is_one_y_pixel:
                _is_one_y_pixel = _
                list_y_lines.append(i)
            if i == len(_y_pixel) - 1:
                list_y_lines.append(i)

        for i in xrange(len(list_y_lines) - 1):
            if not (list_y_lines[i + 1] - list_y_lines[i]):
                for w in xrange(im.size[0]):
                    im.putpixel([w, _y_pixel[list_y_lines[i]]], self._white)
            elif 0 < (list_y_lines[i + 1] - list_y_lines[i]) < num:
                for h in xrange(list_y_lines[i], list_y_lines[i + 1]):
                    for w in xrange(im.size[0]):
                        # print [w, _y_pixel[h]]
                        im.putpixel([w, _y_pixel[h]], self._white)
        return im

    def map_cols_to_x_captcha(self, im):
        '''映射到x轴
        '''
        left = _black_flag = _tmp_flag = 0
        right = im.size[0]
        cut_lines_pixel_num = 3

        _x_pixel = []
        for w in xrange(left, right):
            for h in xrange(1, im.size[1]):
                if im.getpixel((w, h)) == self._black:
                    _tmp_flag = 1
            if _tmp_flag:
                _x_pixel.append(w)
            _tmp_flag = 0
        im = self.cut_x_lines_lt_num(im, _x_pixel, cut_lines_pixel_num)
        return im

    def cut_x_lines_lt_num(self, im, _x_pixel, num):
        '''切割x轴投影小于num像素
        找到像素片位置
        '''
        _is_one_x_pixel = 0
        list_x_lines = []
        for i, v in enumerate(_x_pixel):
            _ = v - i
            if _ != _is_one_x_pixel:
                _is_one_x_pixel = _
                list_x_lines.append(i)
            if i == len(_x_pixel) - 1:
                list_x_lines.append(i)
        for i in xrange(len(list_x_lines) - 1):
            if not (list_x_lines[i + 1] - list_x_lines[i]):
                for h in xrange(im.size[1]):
                    im.putpixel([_x_pixel[list_x_lines[i]], h], self._white)
            elif 0 < (list_x_lines[i + 1] - list_x_lines[i]) < num:
                for w in xrange(list_x_lines[i], list_x_lines[i + 1]):
                    for h in xrange(im.size[1]):
                        im.putpixel([_x_pixel[w], h], self._white)
        return im

    def decode_captcha(self, name):
        u"""通过 tesseract 识别.
        """
        if LOCAL_IMAGE:
            self.img = Image.open(name)
        else:
            _io_name = StringIO.StringIO(name)
            self.img = Image.open(_io_name)
        img_list = self.graying(self.img)
        img_list = self._deal_x_shadow(img_list)
        img_list = self._deal_y_shadow(img_list)
        img_list = self._deal_white_picture(img_list)
        _char_all = self._daal_forecast_char(img_list)
        _char_list = self._deal_empty_char(_char_all)
        self._debug_counts(name, _char_list)
        return ''.join(_char_list)

    def _debug_captch_save(self, _img, path, char):
        u'''
        保存切割识别的图像素材，调试使用
        OPEN_SAVE = 0 不启用 1 启用

        _img = Image对象
        path = 保存路径
        char = 需要保存的预测字符（拼接文件名使用）
        Eg:
            self.captch_download(_img, 'split', char)
        '''
        if OPEN_SAVE:
            _ = str(uuid.uuid4())[:4]
            _img.save('./test_captcha_{}/{}_{}.png'.format(path, char, _))

    def _debug_counts(self, name, _char_list):
        '''
        统计识别正确率， 调试使用
        OPEN_COUNTS = 0 不启用 1 启用

        name: xxxx.png
        _char_list: xxxx

        Eg:
            self._debug_counts(file_name, _char_list)
        '''
        
        if OPEN_COUNTS:
            self.counts += 1
            print '正确为: {}, 识别为: {}'.format(name[-8:-4], ''.join(_char_list).lower())
            if ''.join(_char_list).lower() == name[-8:-4]:
                self.success_counts += 1
                if OPEN_SAVE:
                    self._debug_captch_save(
                        self.img, 'success', ''.join(_char_list))

            else:
                self.errer_counts += 1
                if OPEN_SAVE:
                    self._debug_captch_save(
                        self.img, 'errer', ''.join(_char_list))
            print u'总识别数量: {},      ✅  : {}, ❌ : {},     成功率: {}%'.format(self.counts, self.success_counts, self.errer_counts, self.success_counts * 100.0 / float(self.counts))
            if OPEN_SAVE:
                self._debug_captch_save(self.img, 'all', ''.join(_char_list))

def get_captcha_files(path):
    files = os.listdir(path)
    files_png = filter(lambda x: x.endswith('.png'), files)
    path_files = map(lambda x: '{}/{}.png'.format(path, x[:4]), files_png)
    return path_files


def img_to_str(img):
    char = pytesseract.image_to_string(
        img, lang='eng', config="-psm 7 -c tessedit_char_whitelist=0123456789")
    return char

def test():
    c = Captcha()
    files = get_captcha_files('./test_captcha2')
    map(c.decode_captcha, files)


if __name__ == '__main__':
    test()
