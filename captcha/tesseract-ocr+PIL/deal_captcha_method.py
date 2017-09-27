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