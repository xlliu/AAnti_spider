#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import sys
import numpy as np
import uuid
import os

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import StringIO
from subprocess import call
from ordered_set import OrderedSet
import ipdb


PRINT_IMG_LEVEL = 20

def print_img(img, level=0, count=[0]):
    if level < PRINT_IMG_LEVEL:
        return

    file_name = 'temp/tmp_{}.png'.format(count[0])
    count[0] += 1
    w, h = img.size

    img = img.copy()
    img = img.resize((w*4, h*4))

    # img.show()
    img.save(file_name, quality=100)
    call(['imgcat', file_name])


def img_to_str(img):
    char = pytesseract.image_to_string(img, lang='eng', config="-psm 7 -c tessedit_char_whitelist=0123456789")
    return char


def img_to_str2(img):
    char = pytesseract.image_to_string(img, lang='eng', config="-psm 7 -c tessedit_char_whitelist=0123456789ABCEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
    return char

def split_captch_download(_img, char):
    _ = str(uuid.uuid4())[:4]
    _img.save('./test_captcha_split/{}_{}.png'.format(char, _))

def all_captch_download(_img, sprin):
    _ = str(uuid.uuid4())[:4]
    _img.save('./test_captcha_all/{}_{}.png'.format(sprin, _))


def get_captcha_files(path):
    files = os.listdir(path)
    for f in files:
        if len(f) == 8:
            os.remove('{}/{}'.format(path,f))
    path_files = map(lambda x: './test_captcha/{}'.format(x), files)
    return path_files


class Captcha(object):

    def __init__(self):
        self._white = (255, 255, 255)
        self._black = (0, 0, 0)
        pass
 
    def binarization1(self, img):
        u"""二值化."""
        _img = img.convert("1")
        char = img_to_str2(_img)
        if char:
            split_captch_download(_img, char)
        return char

    def graying(self, img):
    	# 将RGB彩图转为灰度图
        enhancer = ImageEnhance.Contrast(img) #增加对比对
        img = enhancer.enhance(2)
        enhancer = ImageEnhance.Sharpness(img) #锐化
        img = enhancer.enhance(2)
        enhancer = ImageEnhance.Brightness(img) #增加亮度
        img = enhancer.enhance(2)

        img = self.set_white_x_y(img)
        img = self.clear_point(img)

        split_img = self.spilt_columns_captcha(img)
        img_list = [ img.crop(i) for i in split_img ]
        return img_list

    def pixel_in_L(self, black_pixel, pixel, valid_pixel):
        u"""像素点在L中."""
        x, y = pixel
        pixels = []

        for m in (-1, 0, 1):
            for n in (-1, 0, 1):
                pixels.append((x + n, y + m))

        com = (
            (0, 1), (0, 3), (1, 2), (1, 3), (1, 5), (2, 5),
            (3, 6), (3, 7), (5, 8), (5, 7), (6, 7), (7, 8)
        )
        for c in com:
            if pixels[c[0]] in black_pixel and pixels[c[1]] in black_pixel:
                valid_pixel.add(pixels[c[0]])
                valid_pixel.add(pixels[c[1]])
                return True
        return False

    def filter_pixel_not_in_L(self, img):
        u"""去掉不在L图形中的像素."""
        width, height = img.size
        black_pixel = OrderedSet()

        for y in range(height):
            for x in range(width):
                color = img.getpixel((x, y))
                assert color in (0, 255)
                if color == 0:
                    black_pixel.add((x, y))

        valid_pixel = set()
        for pixel in black_pixel:
            if not self.pixel_in_L(black_pixel, pixel, valid_pixel):
                img.putpixel(pixel, 255)
        return img

    def is_hole(self, pixel, block):
        u"""如果一个像素点四周有三个点属于block认为这是一个坑，可以填上."""
        x, y = pixel
        pixels = []
        for m in (-1, 0, 1):
            for n in (-1, 0, 1):
                pixels.append((x + n, y + m))

        connect_points = []
        for order in (1, 3, 5, 7):
            if pixels[order] in block:
                connect_points.append(order)

        # 有两个以上连接点的都是洞
        if len(connect_points) > 2:
            return True
        return False

    def is_burr(self, pixel, block):
        u"""是否毛刺"""
        x, y = pixel
        pixels = []
        for m in (-1, 0, 1):
            for n in (-1, 0, 1):
                pixels.append((x + n, y + m))

        connect_points = []
        for order in (1, 3, 5, 7):
            if pixels[order] in block:
                connect_points.append(order)

        # 上下左右有两个连接点的不是 毛刺
        if len(connect_points) > 1:
            return False
        return True

    def smooth(self, img):
        u"""去掉突出的单个像素."""

        no_change = True

        for i in range(5):
            for block in self.blocks:
                del_pixels = []
                for pixel in block:
                    flag = self.is_burr(pixel, block)
                    if flag:
                        del_pixels.append(pixel)
                        no_change = False
                        img.putpixel(pixel, 255)
                for pixel in del_pixels:
                    block.remove(pixel)

            if no_change:
                break

        print_img(img)
        return img

    def decode_captcha(self, name):
        u"""通过 tesseract 识别.
        """
        self.img = Image.open(name)
        img_list = self.graying(self.img)
        _char_list = filter(lambda x: x, map(self.binarization1, img_list))
        all_captch_download(self.img, ''.join(_char_list))
        if len(_char_list) != 4:
            return "xxxxxxxxxx: {}, len({})".format(''.join(_char_list), len(_char_list))
        else:
            return "oooooooooo: {}, len({})".format(''.join(_char_list), len(_char_list))
        # img = self.filter_pixel_not_in_L(img)
        # print_img(img)
        # s = img_to_str2(img).replace(' ', '')

    def clear_point(self, im):
        _tmpA = self._black
        _tmpB = self._white
        for j in range(1,(im.size[1]-1)):
            for i in range(1,(im.size[0]-1)):
                if im.getpixel((i,j))==_tmpA and im.getpixel(((i-1),(j-1)))==_tmpB  and im.getpixel((i,(j-1)))==_tmpB  and im.getpixel(((i+1),(j-1)))==_tmpB  and im.getpixel(((i-1),j))==_tmpB  and im.getpixel(((i+1),j))==_tmpB  and im.getpixel(((i-1),(j+1)))==_tmpB  and im.getpixel((i,(j+1)))==_tmpB  and im.getpixel(((i+1),(j+1)))==_tmpB:
                    im.putpixel([i,j], _tmpB)
        return im

    def set_white_x_y(self, im):
        for j in range(im.size[1]):
            for i in range(im.size[0]):
                if i==0 or i==(im.size[0]-1): #将图片的第一行和最后一行设为白色。
                    im.putpixel([i,j], self._white)

                if j==0 or j==(im.size[1]-1): #将图片的第一列和最后一列设为白色。
                    im.putpixel([i,j], self._white)
        return im

    def spilt_columns_captcha(self, im):
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

    # def caculate_X(im):
    #     Image_Value=[]
    #     for i in range(im.size[0]):
    #         Y_pixel=0
    #         for j in range(im.size[1]):
    #             if im.getpixel((i,j))==0:
    #                 temp_value=1
    #             else:
    #                 temp_value=0
    #             Y_pixel = Y_pixel temp_value
    #         Image_Value.append(Y_pixel)
    #     return Image_Value

def test():
    c = Captcha()
    files = get_captcha_files('./test_captcha')
    for i in map(c.decode_captcha, files):
        print i
    # print c.decode_captcha()

if __name__ == '__main__':
    # img = Image.open('captcha.jpg')
    # print decode_captcha(img)
    test()
    # # img_large = zoom_in_img(img)
    # # img_large.save('captcha_large.jpg', quality=100)






