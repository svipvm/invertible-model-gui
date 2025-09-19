import cv2
import numpy as np

class ImageDataManager:
    # 状态定义（使用二进制位标记，高位到低位表示顺序），最后状态需要多一位
    STATE_NONE   = 0b00000
    STATE_CROP   = 0b10000
    STATE_RESIZE = 0b01000
    STATE_INFER  = 0b00100
    STATE_FIX    = 0b00010

    STATE_ORDER = [STATE_CROP, STATE_RESIZE, STATE_INFER, STATE_FIX]

    def __init__(self, image_path: str):
        self.image_path = image_path
        self.original_img = cv2.imread(image_path)
        if self.original_img is None:
            raise ValueError(f"无法加载图像：{image_path}")
        self.org_height, self.org_width = self.original_img.shape[:2]
        self.reset()

    def reset(self):
        """初始化，清空所有变量和状态"""
        self.state = self.STATE_NONE
        self.roi = None
        self.resize = None
        self.prompt = None
        self.fix_prompt = None

    def _update_state(self, new_state):
        """叠加状态：新状态会清除之后的状态，再进行 OR"""
        # 找到 new_state 在顺序中的位置
        if new_state in self.STATE_ORDER:
            idx = self.STATE_ORDER.index(new_state)
            # 允许保留之前的状态，清空之后的状态
            keep_mask = sum(self.STATE_ORDER[:idx+1])
            self.state &= keep_mask
        # 叠加新状态
        self.state |= new_state

    @property
    def is_croped(self):
        return self.state & self.STATE_CROP

    @property
    def is_resized(self):
        return self.state & self.STATE_RESIZE
    
    @property
    def is_infered(self):
        return self.state & self.STATE_INFER
    
    @property
    def is_fixed(self):
        return self.state & self.STATE_FIX
    
    def set_crop(self, roi):
        self.roi = roi
        self.resize = None
        self.prompt = None
        self.fix_prompt = None
        self._update_state(self.STATE_CROP)

    def get_cropped_image(self):
        if self.roi is None:
            return self.original_img
        x, y, w, h = self.roi
        return self.original_img[y:y+h, x:x+w]

    def set_resize(self, resize):
        self.resize = resize
        self.prompt = None
        self.fix_prompt = None
        self._update_state(self.STATE_RESIZE)

    def get_resized_image(self, interpolation=cv2.INTER_LINEAR):
        img = self.get_cropped_image()
        if self.resize is None:
            return img
        return cv2.resize(
            img, self.resize, interpolation=interpolation)

    def set_infer(self, prompt: str):
        self.prompt = prompt
        self.fix_prompt = None
        self._update_state(self.STATE_INFER)

    def set_fix(self, fix_prompt: str):
        self.fix_prompt = fix_prompt
        self._update_state(self.STATE_FIX)

    def get_state(self):
        return format(self.state, '05b')