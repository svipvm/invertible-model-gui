import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QAbstractItemView, QStyledItemDelegate,
    QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QBrush, QColor
from data_utils import ImageDataManager

class StatusCircleDelegate(QStyledItemDelegate):
    """用于在表格单元格中绘制不同颜色圆圈的代理类"""
    
    # 为不同状态定义不同颜色
    STATUS_COLORS = {
        ImageDataManager.STATE_NONE: QColor(200, 200, 200),  # 灰色 - 无状态
        ImageDataManager.STATE_CROP: QColor(255, 165, 0),    # 橙色 - 裁切
        ImageDataManager.STATE_RESIZE: QColor(0, 0, 255),    # 蓝色 - 缩放
        ImageDataManager.STATE_INFER: QColor(0, 128, 0),     # 绿色 - 推理
        ImageDataManager.STATE_FIX: QColor(255, 0, 0)        # 红色 - 修正
    }
    
    def paint(self, painter, option, index):
        # 获取状态值
        state = index.data(Qt.UserRole)
        if state is None:
            state = ImageDataManager.STATE_NONE
        else:
            # 获取state的最后一个1的位置对应的状态
            last_bit = state & -state  # 获取最低位的1
            state = last_bit if last_bit in self.STATUS_COLORS else ImageDataManager.STATE_NONE
        
        # 设置抗锯齿
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取单元格的中心位置
        center = option.rect.center()
        radius = min(option.rect.width(), option.rect.height()) // 3
        
        # 选择颜色
        color = self.STATUS_COLORS.get(state, self.STATUS_COLORS[ImageDataManager.STATE_NONE])
        
        # 绘制圆圈
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius, radius)
        
    def sizeHint(self, option, index):
        # 设置单元格大小提示
        size = super().sizeHint(option, index)
        # 确保有足够的空间显示圆圈
        size.setHeight(30)
        return size

class ImageListWidget(QWidget):
    def __init__(self, app=None):
        super().__init__()
        self.image_list = []  # 存储ImageDataManager对象的列表
        self.app = app
        self.last_selected_index = -1  # 存储最后一次点击的数据项索引
        self.init_ui()
    
    def init_ui(self):
        # 设置布局
        layout = QVBoxLayout(self)
        
        # 创建图像列表表格
        self.image_list_table = QTableWidget()
        self.image_list_table.setColumnCount(3)
        self.image_list_table.setHorizontalHeaderLabels(['编号', '图片名', '状态'])
        
        # 控制每一列的宽度占比
        header = self.image_list_table.horizontalHeader()
        # 编号列：固定宽度
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.image_list_table.setColumnWidth(0, 80)
        # 图片名列：拉伸以填充剩余空间
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        # 状态列：固定宽度
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.image_list_table.setColumnWidth(2, 60)
        
        # 为状态列设置自定义代理，用于显示彩色圆圈
        self.image_list_table.setItemDelegateForColumn(2, StatusCircleDelegate())
        
        # 设置列表只能以行为单位进行选择
        self.image_list_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.image_list_table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # 设置单元格不可编辑
        self.image_list_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 隐藏垂直表头（默认索引列）
        self.image_list_table.verticalHeader().setVisible(False)
        
        # 连接信号
        self.image_list_table.cellClicked.connect(self.on_image_selected)
        
        # 添加到布局
        layout.addWidget(self.image_list_table)
    
    def import_image(self):
        """导入单张或多张图像"""
        file_names, _ = QFileDialog.getOpenFileNames(
            self, "选择图像文件", "", "图像文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_names:
            new_images = []
            duplicate_count = 0
            for file_path in file_names:
                # 规范化路径并转换为小写以进行比较（Windows系统路径大小写不敏感）
                normalized_file_path = os.path.normpath(file_path).lower()
                # 检查图像是否已在列表中
                is_duplicate = False
                for img in self.image_list:
                    if os.path.normpath(img.image_path).lower() == normalized_file_path:
                        is_duplicate = True
                        break
                        
                if not is_duplicate:
                    try:
                        # 创建ImageDataManager对象
                        img_manager = ImageDataManager(file_path)
                        new_images.append(img_manager)
                    except ValueError as e:
                        self._update_info(f'加载图像失败: {str(e)}')
                        continue
                else:
                    duplicate_count += 1
            
            if new_images:
                # 记录导入前图像列表是否为空
                was_empty = len(self.image_list) == 0
                # 选中最后一个新增项
                last_row = len(self.image_list)
                # 添加新图像到列表
                self.image_list.extend(new_images)
                # 更新表格
                self.update_table()
                # 如果之前是空模式，切换到默认模式
                # if was_empty and self.app and hasattr(self.app, 'set_mode'):
                #     self.app.set_mode('browse')
                # 触发显示图像信号
                self.on_image_selected(last_row, 0)
                # 更新处理信息
                message = f'成功导入 {len(new_images)} 张图像'
                if duplicate_count > 0:
                    message += f'，过滤掉 {duplicate_count} 张重复图像'
                message += f'，共 {len(self.image_list)} 张'
                self._update_info(message)
            elif duplicate_count > 0:
                self._update_info(f'未导入任何新图像，{duplicate_count} 张图像已存在于列表中')
            else:
                self._update_info('未导入任何图像')

    def import_folder(self):
        """导入文件夹中的所有图像"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择图像文件夹", "")
        
        if folder_path:
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            new_images = []
            duplicate_count = 0
            
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        file_path = os.path.join(root, file)
                        # 规范化路径并转换为小写以进行比较（Windows系统路径大小写不敏感）
                        normalized_file_path = os.path.normpath(file_path).lower()
                        # 检查图像是否已在列表中
                        is_duplicate = False
                        for img in self.image_list:
                            if os.path.normpath(img.image_path).lower() == normalized_file_path:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            try:
                                # 创建ImageDataManager对象
                                img_manager = ImageDataManager(file_path)
                                new_images.append(img_manager)
                            except ValueError as e:
                                self._update_info(f'加载图像失败: {str(e)}')
                                continue
                        else:
                            duplicate_count += 1
            
            if new_images:
                # 记录导入前图像列表是否为空
                was_empty = len(self.image_list) == 0
                # 选中最后一个新增项
                last_row = len(self.image_list)
                # 添加新图像到列表
                self.image_list.extend(new_images)
                # 更新表格
                self.update_table()
                # 如果之前是空模式，切换到默认模式
                # if was_empty and self.app and hasattr(self.app, 'set_mode'):
                #     self.app.set_mode('browse')
                # 触发显示图像信号
                self.on_image_selected(last_row, 0)
                # 更新处理信息
                message = f'从文件夹成功导入 {len(new_images)} 张图像'
                if duplicate_count > 0:
                    message += f'，过滤掉 {duplicate_count} 张重复图像'
                message += f'，共 {len(self.image_list)} 张'
                self._update_info(message)
            elif duplicate_count > 0:
                self._update_info(f'未导入任何新图像，文件夹中的 {duplicate_count} 张图像已存在于列表中')
            else:
                self._update_info('未找到新的图像文件')
    
    def delete_image(self):
        """删除选中的图像"""
        selected_rows = set()
        for item in self.image_list_table.selectedItems():
            selected_rows.add(item.row())
        
        if selected_rows:
            # 显示确认对话框
            count = len(selected_rows)
            reply = QMessageBox.question(
                self, '确认删除', f'确定要删除选中的 {count} 张图像吗？',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 从大到小排序，避免索引问题
                sorted_rows = sorted(selected_rows, reverse=True)
                last_row = sorted_rows[0]
                for row in sorted_rows:
                    # 直接删除列表中的ImageDataManager对象，确保不再保留在内存中
                    del self.image_list[row]
                
                # 清空选择
                self.image_list_table.clearSelection()
                # 更新表格
                self.update_table()
                # 触发显示图像信号
                if len(self.image_list) > 0:
                    # 如果还有图像，尝试选择一个合适的行
                    if last_row >= len(self.image_list):
                        last_row = len(self.image_list) - 1
                    self.on_image_selected(last_row, 0)
                else:
                    # 如果图像列表为空，触发空模式
                    if self.app and hasattr(self.app, 'set_mode'):
                        self.app.set_mode('empty')
                # 更新处理信息
                self._update_info(f'已删除 {len(selected_rows)} 张图像')
        else:
            QMessageBox.information(self, '提示', '请先添加图像')
    
    def delete_workspace(self):
        """清空工作区的所有图像"""
        # 如果工作区不为空，显示确认对话框
        if self.image_list:
            reply = QMessageBox.question(
                self, '确认清空工作区', '确定要清空工作区中的所有图像吗？此操作无法撤销。',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        else:
            QMessageBox.information(self, '提示', '请先添加图像')
            return
        
        # 清空图像列表，确保所有数据不在内存中保留
        self.image_list.clear()
        # 清空选择
        self.image_list_table.clearSelection()
        # 重置最后选中的索引
        self.last_selected_index = -1
        # 更新表格
        self.update_table()
        # 触发空模式
        if self.app and hasattr(self.app, 'set_mode'):
            self.app.set_mode('empty')
        # 更新处理信息
        self._update_info('工作区已清空，所有图像数据已删除')
    
    def update_table(self):
        """更新图像列表表格"""
        self.image_list_table.setRowCount(len(self.image_list))
        
        for row, img_manager in enumerate(self.image_list):
            # 设置编号 - P开头加五位数编号，居中显示
            id_item = QTableWidgetItem(f'P{row + 1:05d}')
            id_item.setTextAlignment(Qt.AlignCenter)
            self.image_list_table.setItem(row, 0, id_item)
            # 设置图片名 - 从image_path中提取文件名
            img_name = os.path.basename(img_manager.image_path)
            name_item = QTableWidgetItem(img_name)
            # 设置tooltip显示完整文件路径
            name_item.setToolTip(img_manager.image_path)
            self.image_list_table.setItem(row, 1, name_item)
            # 设置状态 - 存储状态值，使用代理类显示彩色圆圈
            state_item = QTableWidgetItem()
            # 将状态值存储在UserRole中，供代理类使用
            state_item.setData(Qt.UserRole, img_manager.state)
            # 设置居中对齐
            state_item.setTextAlignment(Qt.AlignCenter)
            self.image_list_table.setItem(row, 2, state_item)
        
        if len(self.image_list) == 0:
            # 重置图像显示区域
            if self.app and hasattr(self.app, 'reset_image_display'):
                self.app.reset_image_display()
                
    def on_image_selected(self, row, column):
        """处理图像选中事件"""
        if 0 <= row < len(self.image_list):
            self.image_list_table.setCurrentCell(row, 0)
            self.image_list_table.scrollToItem(self.image_list_table.item(row, 0))
            # 更新最后选中的索引
            self.last_selected_index = row
            img_name = os.path.basename(self.image_list[row].image_path)
            # 更新处理信息
            self._update_info(f'{row + 1} / {len(self.image_list)} 已选择图像: {img_name}')
            # 调用显示图像的回调函数
            if self.app and hasattr(self.app, 'display_selected_image'):
                self.app.display_selected_image(row)
            # 返回选中的图像管理器
            return self.image_list[row]
        else:
            # 重置图像显示区域
            if self.app and hasattr(self.app, 'reset_image_display'):
                self.app.reset_image_display()
        return None
    
    def get_selected_images(self):
        """获取所有选中的图像"""
        selected_rows = set()
        for item in self.image_list_table.selectedItems():
            selected_rows.add(item.row())
        
        return [self.image_list[row] for row in selected_rows]
        
    def get_last_selected_index(self):
        """获取最后一次点击的数据项索引"""
        return self.last_selected_index
        
    def get_last_selected_image(self):
        """获取最后一次点击的图像管理器对象"""
        if 0 <= self.last_selected_index < len(self.image_list):
            return self.image_list[self.last_selected_index]
        return None
    
    def _update_info(self, message):
        """更新处理信息"""
        if self.app and hasattr(self.app, 'update_process_info'):
            self.app.update_process_info(message)