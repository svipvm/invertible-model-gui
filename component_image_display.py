from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtGui import QPixmap, QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QRect, QPoint

class BaseImageDisplay(QLabel):
    """图像显示组件基类，定义通用接口和方法"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.image_manager = None  # 当前显示的图像管理器
        self.original_pixmap = None  # 原始图像
        self.scaled_pixmap = None  # 缩放后的图像
        
        # 设置组件属性
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet('background-color: #ffffff; border: 1px solid #cccccc;')
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
    def set_image(self, image_manager):
        """设置要显示的图像"""
        self.image_manager = image_manager
        if image_manager:
            img_path = image_manager.image_path
            self.original_pixmap = QPixmap(img_path)
            self._scale_image()
        else:
            self.original_pixmap = None
            self.scaled_pixmap = None
            self.setText('请选择一张图像')
        self.update()
        
    def _scale_image(self):
        """缩放图像以适应组件大小"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            self.scaled_pixmap = self.original_pixmap.scaled(
                self.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
    
    def reset(self):
        """重置组件状态"""
        self.image_manager = None
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.setText('请选择一张图像')
        self.update()
    
    def resizeEvent(self, event):
        """窗口大小变化事件"""
        super().resizeEvent(event)
        if self.original_pixmap:
            self._scale_image()
            self.update()
    
    def on_enter_mode(self):
        """进入模式时的回调"""
        pass
    
    def on_exit_mode(self):
        """退出模式时的回调"""
        pass

class DefaultImageDisplay(BaseImageDisplay):
    """默认简单图像显示组件"""
    def paintEvent(self, event):
        """重绘事件，简单绘制图像"""
        super().paintEvent(event)
        
        if self.scaled_pixmap and not self.scaled_pixmap.isNull():
            painter = QPainter(self)
            # 正常绘制整个图像，居中显示
            x = (self.width() - self.scaled_pixmap.width()) // 2
            y = (self.height() - self.scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, self.scaled_pixmap)

class CropImageDisplay(BaseImageDisplay):
    """裁切模式图像显示组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aspect_ratio = None  # 默认比例为空
        self.rect_size = 512  # 默认长边大小
        self.rectangle = QRect()  # 裁切区域矩形
        self.is_selecting = True  # 是否正在选择区域
        self.start_pos = QPoint()  # 鼠标起始位置
        self.last_rect_size = {}  # 存储每个图像最后操作的尺寸 {image_path: rect_size}
        self.last_rect_pos = {}  # 存储每个图像最后操作的位置 {image_path: rect_pos}
        
    def set_image(self, image_manager):
        """设置要显示的图像"""
        self.image_manager = image_manager
        if image_manager:
            img_path = image_manager.image_path
            self.original_pixmap = QPixmap(img_path)
            self._scale_image()
            
            # 检查是否有之前的裁切区域信息
            if img_path in self.last_rect_size and self.aspect_ratio is not None:
                self.rect_size = self.last_rect_size[img_path]
                self.rectangle = self.last_rect_pos[img_path]
                self.is_selecting = False
                self.update()
            else:
                # 只有当设置了比例时才设置默认裁切区域
                if self.aspect_ratio is not None:
                    self._set_default_rectangle()
                else:
                    self.rectangle = QRect()  # 清除裁切框
                self.is_selecting = True
        else:
            self.original_pixmap = None
            self.scaled_pixmap = None
            self.rectangle = QRect()
            self.setText('请选择一张图像')
        self.update()
    
    def _set_default_rectangle(self):
        """设置默认的裁切区域，长边为512，保持比例"""
        if self.scaled_pixmap and not self.scaled_pixmap.isNull():
            img_width = self.scaled_pixmap.width()
            img_height = self.scaled_pixmap.height()
            
            # 计算图像在标签中的居中位置
            x_offset = (self.width() - img_width) // 2
            y_offset = (self.height() - img_height) // 2
            
            # 根据比例计算矩形尺寸
            if self.aspect_ratio > 1:  # 横屏比例
                width = min(self.rect_size, img_width)
                height = int(width / self.aspect_ratio)
            else:  # 竖屏比例
                height = min(self.rect_size, img_height)
                width = int(height * self.aspect_ratio)
            
            # 确保矩形不超出图像范围
            width = min(width, img_width)
            height = min(height, img_height)
            
            # 居中放置矩形
            x = x_offset + (img_width - width) // 2
            y = y_offset + (img_height - height) // 2
            
            self.rectangle = QRect(x, y, width, height)
    
    def set_aspect_ratio(self, ratio_str):
        """设置裁切比例"""
        try:
            # 处理空比例情况
            if not ratio_str or ratio_str.strip() == '':
                self.aspect_ratio = None
                self.rectangle = QRect()  # 清除裁切框
                if self.image_manager:
                    # 清除图像管理器中的裁切信息
                    self.image_manager.roi = None
                    self.image_manager.state &= ~self.image_manager.STATE_CROP  # 清除裁切状态标记
                self.update()
                return
                
            width_ratio, height_ratio = map(int, ratio_str.split(':'))
            self.aspect_ratio = width_ratio / height_ratio
            if self.image_manager:
                self._set_default_rectangle()
                self.update()
        except ValueError:
            pass
    
    def set_rect_size(self, size):
        """设置矩形长边大小"""
        self.rect_size = size
        if self.image_manager:
            self._set_default_rectangle()
            self.update()
    
    def paintEvent(self, event):
        """重绘事件，绘制图像和裁切矩形"""
        super().paintEvent(event)
        
        if self.scaled_pixmap and not self.scaled_pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # 首先绘制完整的原始图像（底层显示原图）
            x_offset = (self.width() - self.scaled_pixmap.width()) // 2
            y_offset = (self.height() - self.scaled_pixmap.height()) // 2
            painter.drawPixmap(x_offset, y_offset, self.scaled_pixmap)
            
            # 只有当设置了比例时才显示裁切框和相关功能
            if self.aspect_ratio is not None:
                # 如果已经选择了裁切区域
                if not self.is_selecting and not self.rectangle.isNull():
                    # 绘制裁切范围外的低亮度效果
                    # 1. 创建一个蒙版，覆盖整个窗口
                    mask_color = QColor(0, 0, 0, 100)  # 半透明黑色，降低亮度
                    painter.fillRect(self.rect(), mask_color)
                    
                    # 2. 在裁切区域内绘制原始亮度的图像
                    source_rect = self._get_source_rect()
                    painter.drawPixmap(self.rectangle, self.original_pixmap, source_rect)
                
                # 绘制裁切矩形边框
                if not self.rectangle.isNull():
                    if self.is_selecting:
                        # 未确认状态 - 使用红色边框
                        pen = QPen(Qt.red, 2, Qt.SolidLine)
                    else:
                        # 已确认状态 - 使用绿色边框
                        pen = QPen(Qt.green, 2, Qt.SolidLine)
                    painter.setPen(pen)
                    painter.drawRect(self.rectangle)
                    
                    # 绘制矩形的8个控制点（用于视觉提示）
                    self._draw_control_points(painter)
                    
                    # 添加状态提示文字
                    painter.setPen(QPen(Qt.white, 1, Qt.SolidLine))
                    if self.is_selecting:
                        painter.drawText(10, 20, "拖动鼠标移动裁切框，滚轮缩放，左键确认")
                    else:
                        painter.drawText(10, 20, "右键取消裁切区域")
    
    def _draw_control_points(self, painter):
        """绘制矩形的控制点"""
        pen = QPen(Qt.white, 4, Qt.SolidLine)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        
        # 左上角
        painter.drawPoint(self.rectangle.topLeft())
        # 右上角
        painter.drawPoint(self.rectangle.topRight())
        # 左下角
        painter.drawPoint(self.rectangle.bottomLeft())
        # 右下角
        painter.drawPoint(self.rectangle.bottomRight())
        # 上中
        painter.drawPoint(self.rectangle.left() + self.rectangle.width() // 2, self.rectangle.top())
        # 下中
        painter.drawPoint(self.rectangle.left() + self.rectangle.width() // 2, self.rectangle.bottom())
        # 左中
        painter.drawPoint(self.rectangle.left(), self.rectangle.top() + self.rectangle.height() // 2)
        # 右中
        painter.drawPoint(self.rectangle.right(), self.rectangle.top() + self.rectangle.height() // 2)
    
    def _get_source_rect(self):
        """将显示区域的矩形转换为原始图像的矩形"""
        if not self.original_pixmap or not self.scaled_pixmap or self.rectangle.isNull():
            return QRect()
        
        # 计算缩放比例
        scale_x = self.original_pixmap.width() / self.scaled_pixmap.width()
        scale_y = self.original_pixmap.height() / self.scaled_pixmap.height()
        
        # 计算图像在标签中的偏移量
        x_offset = (self.width() - self.scaled_pixmap.width()) // 2
        y_offset = (self.height() - self.scaled_pixmap.height()) // 2
        
        # 计算原始图像中的矩形
        x = int((self.rectangle.x() - x_offset) * scale_x)
        y = int((self.rectangle.y() - y_offset) * scale_y)
        width = int(self.rectangle.width() * scale_x)
        height = int(self.rectangle.height() * scale_y)
        
        return QRect(x, y, width, height)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        # 只有当设置了比例时才响应鼠标事件
        if self.aspect_ratio is None:
            return
            
        if event.button() == Qt.LeftButton:
            if self.is_selecting:
                # 未确认状态下，左键点击确认选择
                self.is_selecting = False
                
                # 保存裁切区域到图像管理器
                if self.image_manager:
                    source_rect = self._get_source_rect()
                    self.image_manager.set_crop((source_rect.x(), source_rect.y(), source_rect.width(), source_rect.height()))
                    
                    # 保存最后操作的尺寸和位置
                    img_path = self.image_manager.image_path
                    self.last_rect_size[img_path] = self.rect_size
                    self.last_rect_pos[img_path] = self.rectangle
                
                self.update()
        elif event.button() == Qt.RightButton:
            # 右键取消选择，回到未确认状态
            self.is_selecting = True
            
            # 清除图像管理器中的裁切信息
            if self.image_manager:
                self.image_manager.roi = None
                self.image_manager.state &= ~self.image_manager.STATE_CROP  # 清除裁切状态标记
                
                # 清除本地存储的该图像的历史裁切记录
                img_path = self.image_manager.image_path
                if img_path in self.last_rect_size:
                    del self.last_rect_size[img_path]
                if img_path in self.last_rect_pos:
                    del self.last_rect_pos[img_path]
                
                # 设置默认的裁切区域
                self._set_default_rectangle()
            
            self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 只有当设置了比例时才响应鼠标事件
        if self.aspect_ratio is None:
            return
            
        if self.is_selecting and self.image_manager:
            # 更新矩形位置，使裁切框中心跟随鼠标移动
            self._update_rectangle_position(event.pos())
            self.update()
    
    def _update_rectangle_position(self, pos):
        """更新矩形位置，确保矩形始终在图像范围内"""
        if not self.scaled_pixmap or not self.scaled_pixmap.isNull():
            img_width = self.scaled_pixmap.width()
            img_height = self.scaled_pixmap.height()
            
            # 计算图像在标签中的偏移量
            x_offset = (self.width() - img_width) // 2
            y_offset = (self.height() - img_height) // 2
            
            # 计算新的矩形中心点
            center_x = max(x_offset, min(pos.x(), x_offset + img_width))
            center_y = max(y_offset, min(pos.y(), y_offset + img_height))
            
            # 更新矩形位置（保持大小不变）
            new_x = center_x - self.rectangle.width() // 2
            new_y = center_y - self.rectangle.height() // 2
            
            # 确保矩形不超出图像范围
            new_x = max(x_offset, min(new_x, x_offset + img_width - self.rectangle.width()))
            new_y = max(y_offset, min(new_y, y_offset + img_height - self.rectangle.height()))
            
            self.rectangle = QRect(new_x, new_y, self.rectangle.width(), self.rectangle.height())
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            # 左键释放，确认选择
            self.is_selecting = False
            
            # 保存裁切区域到图像管理器
            if self.image_manager:
                source_rect = self._get_source_rect()
                self.image_manager.set_crop((source_rect.x(), source_rect.y(), source_rect.width(), source_rect.height()))
                
                # 保存最后操作的尺寸和位置
                img_path = self.image_manager.image_path
                self.last_rect_size[img_path] = self.rect_size
                self.last_rect_pos[img_path] = self.rectangle
            
            self.update()
    
    def wheelEvent(self, event):
        """鼠标滚轮事件，用于缩放矩形"""
        # 只有当设置了比例时才响应鼠标滚轮事件
        if self.aspect_ratio is None:
            return
            
        if self.is_selecting and self.image_manager:
            # 获取滚轮角度
            angle_delta = event.angleDelta().y()
            
            # 计算新的矩形尺寸
            scale_factor = 1.1 if angle_delta > 0 else 0.9
            new_width = int(self.rectangle.width() * scale_factor)
            new_height = int(new_width / self.aspect_ratio)
            
            # 计算图像在标签中的偏移量
            x_offset = (self.width() - self.scaled_pixmap.width()) // 2
            y_offset = (self.height() - self.scaled_pixmap.height()) // 2
            img_width = self.scaled_pixmap.width()
            img_height = self.scaled_pixmap.height()
            
            # 确保新尺寸不超出图像范围
            max_width = min(img_width, int(img_height * self.aspect_ratio))
            min_width = 100  # 最小宽度
            
            new_width = max(min_width, min(new_width, max_width))
            new_height = int(new_width / self.aspect_ratio)
            
            # 计算新的位置（保持中心点不变）
            center_x = self.rectangle.x() + self.rectangle.width() // 2
            center_y = self.rectangle.y() + self.rectangle.height() // 2
            new_x = center_x - new_width // 2
            new_y = center_y - new_height // 2
            
            # 确保矩形不超出图像范围
            new_x = max(x_offset, min(new_x, x_offset + img_width - new_width))
            new_y = max(y_offset, min(new_y, y_offset + img_height - new_height))
            
            # 更新矩形和大小
            self.rectangle = QRect(new_x, new_y, new_width, new_height)
            self.rect_size = max(new_width, new_height)  # 更新长边大小
            
            self.update()
    
    def reset(self):
        """重置组件状态"""
        super().reset()
        self.rectangle = QRect()
        self.is_selecting = True

class ResizeImageDisplay(BaseImageDisplay):
    """缩放模式图像显示组件，显示裁切后的图像"""
    def paintEvent(self, event):
        """重绘事件，显示裁切后的图像"""
        super().paintEvent(event)
        
        if self.scaled_pixmap and not self.scaled_pixmap.isNull() and self.image_manager:
            painter = QPainter(self)
            
            # 如果有裁切区域，绘制裁切后的图像
            if self.image_manager.roi:
                # 获取原始图像中的裁切区域
                x, y, w, h = self.image_manager.roi
                source_rect = QRect(x, y, w, h)
                
                # 计算裁切后图像的缩放尺寸
                scale_x = self.width() / w
                scale_y = self.height() / h
                scale = min(scale_x, scale_y)
                scaled_width = int(w * scale)
                scaled_height = int(h * scale)
                
                # 居中显示裁切后的图像
                x_pos = (self.width() - scaled_width) // 2
                y_pos = (self.height() - scaled_height) // 2
                
                # 绘制裁切后的图像
                painter.drawPixmap(QRect(x_pos, y_pos, scaled_width, scaled_height), 
                                  self.original_pixmap, source_rect)
                
                # 绘制裁切区域的边框
                pen = QPen(Qt.blue, 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(x_pos, y_pos, scaled_width, scaled_height)
            else:
                # 没有裁切区域，正常绘制整个图像
                x = (self.width() - self.scaled_pixmap.width()) // 2
                y = (self.height() - self.scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, self.scaled_pixmap)

class MarkImageDisplay(BaseImageDisplay):
    """打标模式图像显示组件，显示裁切和缩放后的图像"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.marks = []  # 存储打标位置和内容
    
    def paintEvent(self, event):
        """重绘事件，显示处理后的图像和打标"""
        super().paintEvent(event)
        
        if self.scaled_pixmap and not self.scaled_pixmap.isNull() and self.image_manager:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 获取处理后的图像显示区域
            display_rect = self._get_processed_image_rect()
            
            if display_rect.isValid():
                # 根据处理状态绘制不同的图像
                if self.image_manager.is_resized:
                    # 如果有缩放，显示缩放后的图像
                    # 这里简化处理，实际应从image_manager获取处理后的图像数据
                    pass
                elif self.image_manager.is_croped:
                    # 如果有裁切，显示裁切后的图像
                    x, y, w, h = self.image_manager.roi
                    source_rect = QRect(x, y, w, h)
                    painter.drawPixmap(display_rect, self.original_pixmap, source_rect)
                else:
                    # 否则显示原始图像
                    painter.drawPixmap(
                        (self.width() - self.scaled_pixmap.width()) // 2,
                        (self.height() - self.scaled_pixmap.height()) // 2,
                        self.scaled_pixmap
                    )
                
                # 绘制打标
                self._draw_marks(painter, display_rect)
    
    def _get_processed_image_rect(self):
        """计算处理后图像的显示区域"""
        if not self.scaled_pixmap or not self.scaled_pixmap.isNull():
            img_width = self.scaled_pixmap.width()
            img_height = self.scaled_pixmap.height()
            
            # 如果有裁切，调整图像大小
            if self.image_manager and self.image_manager.roi:
                x, y, w, h = self.image_manager.roi
                # 计算原始图像到显示图像的缩放比例
                scale_x = self.scaled_pixmap.width() / self.original_pixmap.width()
                scale_y = self.scaled_pixmap.height() / self.original_pixmap.height()
                
                # 计算显示区域中的裁切矩形
                display_x = (self.width() - self.scaled_pixmap.width()) // 2 + int(x * scale_x)
                display_y = (self.height() - self.scaled_pixmap.height()) // 2 + int(y * scale_y)
                display_width = int(w * scale_x)
                display_height = int(h * scale_y)
                
                # 计算居中显示的缩放比例
                scale = min(self.width() / display_width, self.height() / display_height)
                new_width = int(display_width * scale)
                new_height = int(display_height * scale)
                
                return QRect(
                    (self.width() - new_width) // 2,
                    (self.height() - new_height) // 2,
                    new_width,
                    new_height
                )
            else:
                # 没有裁切，返回原图像居中显示的区域
                x = (self.width() - self.scaled_pixmap.width()) // 2
                y = (self.height() - self.scaled_pixmap.height()) // 2
                return QRect(x, y, self.scaled_pixmap.width(), self.scaled_pixmap.height())
        return QRect()
    
    def _draw_marks(self, painter, display_rect):
        """绘制打标"""
        for mark in self.marks:
            x, y, text = mark
            # 绘制标记点
            pen = QPen(Qt.red, 5, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawPoint(x, y)
            
            # 绘制标记文本
            painter.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
            painter.drawText(x + 10, y - 10, text)
    
    def add_mark(self, pos, text):
        """添加一个打标"""
        self.marks.append((pos.x(), pos.y(), text))
        self.update()
    
    def clear_marks(self):
        """清除所有打标"""
        self.marks.clear()
        self.update()
    
    def reset(self):
        """重置组件状态"""
        super().reset()
        self.clear_marks()
    
    def mousePressEvent(self, event):
        """鼠标按下事件，用于添加打标"""
        if event.button() == Qt.LeftButton and self.image_manager:
            # 在鼠标位置添加打标
            self.add_mark(event.pos(), "标记点")

class CorrectImageDisplay(BaseImageDisplay):
    """修正模式图像显示组件，显示裁切和缩放后图像"""
    def paintEvent(self, event):
        """重绘事件，显示处理后的图像"""
        super().paintEvent(event)
        
        if self.scaled_pixmap and not self.scaled_pixmap.isNull() and self.image_manager:
            painter = QPainter(self)
            
            # 获取处理后的图像显示区域
            display_rect = self._get_processed_image_rect()
            
            if display_rect.isValid():
                # 根据处理状态绘制不同的图像
                if self.image_manager.is_resized:
                    # 如果有缩放，显示缩放后的图像
                    # 这里简化处理，实际应从image_manager获取处理后的图像数据
                    pass
                elif self.image_manager.is_croped:
                    # 如果有裁切，显示裁切后的图像
                    x, y, w, h = self.image_manager.roi
                    source_rect = QRect(x, y, w, h)
                    painter.drawPixmap(display_rect, self.original_pixmap, source_rect)
                else:
                    # 否则显示原始图像
                    painter.drawPixmap(
                        (self.width() - self.scaled_pixmap.width()) // 2,
                        (self.height() - self.scaled_pixmap.height()) // 2,
                        self.scaled_pixmap
                    )
                
                # 绘制修正模式的提示信息
                painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))
                painter.drawText(10, 20, "修正模式：显示最终处理后的图像")
    
    def _get_processed_image_rect(self):
        """计算处理后图像的显示区域"""
        if not self.scaled_pixmap or not self.scaled_pixmap.isNull():
            img_width = self.scaled_pixmap.width()
            img_height = self.scaled_pixmap.height()
            
            # 如果有裁切，调整图像大小
            if self.image_manager and self.image_manager.roi:
                x, y, w, h = self.image_manager.roi
                # 计算原始图像到显示图像的缩放比例
                scale_x = self.scaled_pixmap.width() / self.original_pixmap.width()
                scale_y = self.scaled_pixmap.height() / self.original_pixmap.height()
                
                # 计算显示区域中的裁切矩形
                display_x = (self.width() - self.scaled_pixmap.width()) // 2 + int(x * scale_x)
                display_y = (self.height() - self.scaled_pixmap.height()) // 2 + int(y * scale_y)
                display_width = int(w * scale_x)
                display_height = int(h * scale_y)
                
                # 计算居中显示的缩放比例
                scale = min(self.width() / display_width, self.height() / display_height)
                new_width = int(display_width * scale)
                new_height = int(display_height * scale)
                
                return QRect(
                    (self.width() - new_width) // 2,
                    (self.height() - new_height) // 2,
                    new_width,
                    new_height
                )
            else:
                # 没有裁切，返回原图像居中显示的区域
                x = (self.width() - self.scaled_pixmap.width()) // 2
                y = (self.height() - self.scaled_pixmap.height()) // 2
                return QRect(x, y, self.scaled_pixmap.width(), self.scaled_pixmap.height())
        return QRect()

class ModeDisplayManager:
    """图像显示组件管理器，负责管理不同模式的图像显示组件"""
    def __init__(self, app=None):
        self.app = app
        self.current_mode = None
        self.display_widget = None
        self.components = {}
        self.image_manager = None
        
        # 初始化各种模式的图像显示组件
        self._init_components()
    
    def _init_components(self):
        """初始化各种模式的图像显示组件"""
        self.components['default'] = DefaultImageDisplay(self.app)
        self.components['default'].hide()
        self.components['default'].on_exit_mode()

        self.components['crop'] = CropImageDisplay(self.app)
        self.components['crop'].hide()
        self.components['crop'].on_exit_mode()

        self.components['resize'] = ResizeImageDisplay(self.app)
        self.components['resize'].hide()
        self.components['resize'].on_exit_mode()

        self.components['mark'] = MarkImageDisplay(self.app)
        self.components['mark'].hide()
        self.components['mark'].on_exit_mode()
        
        self.components['correct'] = CorrectImageDisplay(self.app)
        self.components['correct'].hide()
        self.components['correct'].on_exit_mode()
    
    def set_display_widget(self, display_widget):
        """设置图像显示容器"""
        self.display_widget = display_widget
    
    def set_mode(self, mode):
        """切换到指定模式的图像显示组件"""
        if mode in self.components:
            # 如果当前有活跃的组件，先隐藏它
            if self.current_mode and self.current_mode in self.components:
                self.components[self.current_mode].hide()
                self.components[self.current_mode].on_exit_mode()
            
            # 显示新模式的组件
            self.current_mode = mode
            current_component = self.components[mode]
            
            # 如果显示容器存在，添加组件到容器
            if self.display_widget:
                layout = self.display_widget.layout()
                if layout is not None:
                    # 清空布局中的所有组件
                    while layout.count() > 0:
                        item = layout.takeAt(0)
                        widget = item.widget()
                        if widget:
                            widget.hide()
                            layout.removeWidget(widget)
                    
                    # 添加新模式的组件到布局
                    layout.addWidget(current_component)
            
            # 设置图像
            if self.image_manager:
                current_component.set_image(self.image_manager)
            
            # 显示组件
            current_component.show()
            current_component.on_enter_mode()
    
    def set_image(self, image_manager):
        """设置要显示的图像"""
        self.image_manager = image_manager
        # 为当前模式的组件设置图像
        if self.current_mode and self.current_mode in self.components:
            self.components[self.current_mode].set_image(image_manager)
    
    def reset(self):
        """重置所有组件"""
        for component in self.components.values():
            component.reset()
    
    def get_current_component(self):
        """获取当前模式的组件"""
        if self.current_mode and self.current_mode in self.components:
            return self.components[self.current_mode]
        return None
    
    def resizeEvent(self, event):
        """窗口大小变化事件"""
        if self.current_mode and self.current_mode in self.components:
            self.components[self.current_mode].resizeEvent(event)