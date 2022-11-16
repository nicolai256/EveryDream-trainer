
import PIL
import numpy as np
from torchvision import transforms, utils
import random
import math
import os

class ImageTrainItem(): 
    """
    image: PIL.Image
    identifier: caption,
    target_aspect: (width, height), 
    pathname: path to image file
    flip_p: probability of flipping image (0.0 to 1.0)
    """    
    def __init__(self, image: PIL.Image, caption: str, target_wh: list, pathname: str, flip_p=0.0):
        self.caption = caption
        self.target_wh = target_wh
        self.pathname = pathname
        self.flip = transforms.RandomHorizontalFlip(p=flip_p)
        self.cropped_img = None

        if image is None:
            self.image = []
        else:
            self.image = image

    def hydrate(self, crop=False, save=False, crop_jitter=0):
        """
        crop: hard center crop to 512x512
        save: save the cropped image to disk, for manual inspection of resize/crop
        crop_jitter: randomly shift cropp by N pixels when using multiple aspect ratios to improve training quality
        """
        if not hasattr(self, 'image') or len(self.image) == 0:
            self.image = PIL.Image.open(self.pathname).convert('RGB')

            width, height = self.image.size
            if crop:
                cropped_img = self.__autocrop(self.image)
                self.image = cropped_img.resize((512,512), resample=PIL.Image.BICUBIC)
            else:
                if self.target_wh[0] == self.target_wh[1]:
                    pass
                else: 
                    width, height = self.image.size
                    image_aspect = width / height
                    jitter_amount = random.randint(0, crop_jitter)
                    target_aspect = self.target_wh[0] / self.target_wh[1]
                    print(f"{target_aspect}, {self.target_wh}")
                    if image_aspect > target_aspect:
                        new_width = int(height * target_aspect)
                        jitter_amount = max(min(jitter_amount, int(abs(width-new_width)/2)), 0)
                        left = jitter_amount
                        right = left + new_width
                        print(f"crop left: {left}, right: {right}, jitteramt:{jitter_amount}, [{width}, {height}] img: {self.pathname}")
                        self.image = self.image.crop((left, 0, right, height))
                    else:
                        new_height = int(width / target_aspect)
                        jitter_amount = max(min(jitter_amount, int(abs(height-new_height)/2)), 0)
                        top = jitter_amount
                        bottom = top + new_height
                        print(f"crop top: {top}, bottom: {bottom}, jitteramt:{jitter_amount}, [{width}, {height}] img: {self.pathname}")
                        self.image = self.image.crop((0, top, width, bottom))
                self.image = self.image.resize(self.target_wh, resample=PIL.Image.BICUBIC)

            self.image = self.flip(self.image)

        if type(self.image) is not np.ndarray:
            if save: 
                base_name = os.path.basename(self.pathname)
                if not os.path.exists("test/output"):
                    os.makedirs("test/output")
                self.image.save(f"test/output/{base_name}")
            
            self.image = np.array(self.image).astype(np.uint8)

            self.image = (self.image / 127.5 - 1.0).astype(np.float32)
        
        print(self.image.shape)

        return self

    @staticmethod
    def __autocrop(image: PIL.Image, q=.404):
        """
        crops image to a random square inside small axis using a truncated gaussian distribution across the long axis
        """
        x, y = image.size

        if x != y:
            if (x>y):
                rand_x = x-y
                sigma = max(rand_x*q,1)
            else:
                rand_y = y-x
                sigma = max(rand_y*q,1)

            if (x>y):
                x_crop_gauss = abs(random.gauss(0, sigma))
                x_crop = min(x_crop_gauss,(x-y)/2)
                x_crop = math.trunc(x_crop)
                y_crop = 0
            else:
                y_crop_gauss = abs(random.gauss(0, sigma))
                x_crop = 0
                y_crop = min(y_crop_gauss,(y-x)/2)
                y_crop = math.trunc(y_crop)
                
            min_xy = min(x, y)
            image = image.crop((x_crop, y_crop, x_crop + min_xy, y_crop + min_xy))

        return image