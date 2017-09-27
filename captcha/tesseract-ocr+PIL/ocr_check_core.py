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


PRINT_IMG_LEVEL = 20
DOWNLOAD_LEVEL = 0
OPEN_COUNTS = 1

def get_captcha_files(path):
    files = os.listdir(path)
    files_png = filter(lambda x: x.endswith('.png'), files)
    path_files = map(lambda x: '{}/{}.png'.format(path, x[:4]), files_png)
    return path_files

def img_to_str(img):
    char = pytesseract.image_to_string(img, lang='eng', config="-psm 7 -c tessedit_char_whitelist=0123456789")
    return char


class Captcha(object):

    def __init__(self):
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
            self.captch_download(_img, 'split', char)
        return char

    def graying(self, img):
        # 将RGB 彩图强化 二值化
        enhancer = ImageEnhance.Contrast(img) #增加对比对
        img = enhancer.enhance(2)
        # enhancer = ImageEnhance.Sharpness(img) #锐化
        # img = enhancer.enhance(2)
        enhancer = ImageEnhance.Brightness(img) #二值化
        img = enhancer.enhance(2)
        img = self.set_white_x_y(img)
        img = self.clear_point(img)
        split_img = self.spilt_columns_captcha(img)
        img_list = [ img.crop(i) for i in split_img ]

        return img_list


    def img_to_str2(self, img):
        _config = "-psm 10 -c tessedit_char_whitelist=0123456789ABCEFGHJKLMNPQRSTUVWXYZabcdefghjklmnpqrstuvwxyz"
        char = pytesseract.image_to_string(img, lang='eng', config=_config)
        return char

    def captch_download(self, _img, path, char):
        if DOWNLOAD_LEVEL:
            _ = str(uuid.uuid4())[:4]
            _img.save('./test_captcha_{}/{}_{}.png'.format(path, char, _))

    def _debug_counts(self, name, _char_list):
        if OPEN_COUNTS:
            self.counts += 1
            print '正确为: {}, 识别为: {}'.format(name[-8:-4], ''.join(_char_list).lower())
            if ''.join(_char_list).lower() == name[-8:-4]:
                self.success_counts +=1
                if DOWNLOAD_LEVEL:
                    self.captch_download(self.img, 'success', ''.join(_char_list))
                
            else:
                self.errer_counts +=1
                if DOWNLOAD_LEVEL:
                    self.captch_download(self.img, 'errer', ''.join(_char_list))
            print u'总识别数量: {},      ✅  : {}, ❌ : {},     成功率: {}%'.format(self.counts, self.success_counts, self.errer_counts, self.success_counts*100.0/float(self.counts))
            if DOWNLOAD_LEVEL:
                self.captch_download(self.img, 'all', ''.join(_char_list))

    def decode_captcha(self, name):
        u"""通过 tesseract 识别.
        """
        self.img = Image.open(StringIO.StringIO(s))
        # self.img = Image.open(name)
        img_list = self.graying(self.img)
        img_list = map(self.map_cols_to_X_captcha, img_list)
        img_list = map(self.map_rows_to_Y_captcha, img_list)
        # 移除空白图片
        for i, il in enumerate(img_list):
            if not [1 for w in xrange(il.size[0]) for h in xrange(il.size[1]) if il.getpixel((w,h)) == self._black]:
                del img_list[i]
    
        _char_list = filter(lambda x: x, map(self.binarization1, img_list))
        self._debug_counts(name, _char_list)
        return ''.join(_char_list)

    def clear_point(self, im):
        '''清除单噪点
        '''
        _tmpA = self._black
        _tmpB = self._white
        for j in range(1,(im.size[1]-1)):
            for i in range(1,(im.size[0]-1)):
                if (im.getpixel((i,j))==_tmpA and im.getpixel(((i-1),(j-1)))==_tmpB  and im.getpixel((i,(j-1)))==_tmpB 
                    and im.getpixel(((i+1),(j-1)))==_tmpB  and im.getpixel(((i-1),j))==_tmpB  and im.getpixel(((i+1),j))==_tmpB  
                    and im.getpixel(((i-1),(j+1)))==_tmpB  and im.getpixel((i,(j+1)))==_tmpB  and im.getpixel(((i+1),(j+1)))==_tmpB):
                    im.putpixel([i,j], _tmpB)
        return im

    def set_white_x_y(self, im):
        '''边缘填充
        '''
        for j in range(im.size[1]):
            for i in range(im.size[0]):
                if i==0 or i==(im.size[0]-1):
                    im.putpixel([i,j], self._white)

                if j==0 or j==(im.size[1]-1):
                    im.putpixel([i,j], self._white)
        return im

    def spilt_columns_captcha(self, im):
        '''横向切割
        '''
        up = 0
        down = int(im.size[1])-1
        left = 0
        right = 0

        _black_flag = 0
        _tmp = 0
        _split_list = []
        for w in xrange(left, im.size[0]):
            for h in xrange(1, im.size[1]):
                if im.getpixel((w, h)) == self._black:
                    _tmp = 1
            if not _black_flag and _tmp:
                _black_flag = 1
                left = w
            if _black_flag and not _tmp:
                _black_flag = 0
                right = w
                _split_list.append((left-1 if left else 0, up,right+1 if right < im.size[0] else im.size[0], down))
            _tmp = False
        return _split_list

    def map_rows_to_Y_captcha(self, im):
        '''映射到y轴
        '''
        up = 0
        down = int(im.size[1])-1

        _black_flag = 0
        _tmp = 0
        _y_pixel = []
        for h in xrange(0, im.size[1]):
            for w in xrange(1, im.size[0]):
                if im.getpixel((w, h)) == self._black:
                    _tmp = 1

            if _tmp:
                _y_pixel.append(h)
            _tmp = 0

        _tmp2 = 0
        list_i = []
        for i, v in enumerate(_y_pixel):
            _ = v-i
            if _ != _tmp2:
                _tmp2 = _
                list_i.append(i)
            if i == len(_y_pixel)-1:
                list_i.append(i)

        for i in xrange(len(list_i)-1):
            if not (list_i[i+1] - list_i[i]):
                for w in xrange(im.size[0]):
                    im.putpixel([w, _y_pixel[list_i[i]]], self._white)
            elif 0 < (list_i[i+1] - list_i[i]) < 3:
                for h in xrange(list_i[i], list_i[i+1]):
                    for w in xrange(im.size[0]):
                        # print [w, _y_pixel[h]]
                        im.putpixel([w, _y_pixel[h]], self._white)
        return im

    def map_cols_to_X_captcha(self, im):
        '''映射到x轴
        '''
        left = 0
        right = int(im.size[0])-1

        _black_flag = 0
        _tmp = 0
        _x_pixel = []
        for w in xrange(0, im.size[0]):
            for h in xrange(1, im.size[1]):
                if im.getpixel((w, h)) == self._black:
                    _tmp = 1
            if _tmp:
                _x_pixel.append(w)
            _tmp = 0

        _tmp2 = 0
        list_i = []
        for i, v in enumerate(_x_pixel):
            _ = v-i
            if _ != _tmp2:
                _tmp2 = _
                list_i.append(i)
            if i == len(_x_pixel)-1:
                list_i.append(i)
        for i in xrange(len(list_i)-1):
            if not (list_i[i+1] - list_i[i]):
                for h in xrange(im.size[1]):
                    im.putpixel([_x_pixel[list_i[i]], h], self._white)
            elif 0 < (list_i[i+1] - list_i[i]) < 3:
                for w in xrange(list_i[i], list_i[i+1]):
                    for h in xrange(im.size[1]):
                        im.putpixel([_x_pixel[w], h], self._white)
        return im


def test():
    c = Captcha()
    files = get_captcha_files('./test_captcha2')
    map(c.decode_captcha, files)

if __name__ == '__main__':
    # img = Image.open('captcha.jpg')
    # print decode_captcha(img)
    test()
    # # img_large = zoom_in_img(img)
    # # img_large.save('captcha_large.jpg', quality=100)






