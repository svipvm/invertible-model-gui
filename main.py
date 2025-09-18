import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QProgressBar,
    QFrame, QHeaderView, QSizePolicy
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QEvent
from image_list_widget import ImageListWidget
from component_opt_widgets import ModeOptManager
from component_image_display import ModeDisplayManager
from mode_manager import ModeManager

class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化模式管理器和图像显示管理器
        mode_opt_manager = ModeOptManager(self)
        mode_display_manager = ModeDisplayManager(self)
        
        # 初始化统一模式显示管理器
        self.mode_manager = ModeManager(self)
        self.mode_manager.set_mode_opt_manager(mode_opt_manager)
        self.mode_manager.set_image_display_manager(mode_display_manager)
        
        # 初始化UI
        self.init_ui()
        # 连接信号和槽
        self.connect_signals()
        
        # 检查图像列表是否为空，如果为空则设置为空模式
        if not self.image_list_widget.image_list:
            self.mode_manager.set_mode('empty')
        else:
            self.mode_manager.set_mode('default')
    
    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle('图像处理器')
        self.setGeometry(100, 100, 1000, 600)
        self.setMinimumSize(1200, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主水平布局
        main_layout = QHBoxLayout(central_widget)
        
        # ========== 左侧按钮区域 ==========
        left_panel = QWidget()
        left_panel.setMinimumSize(150, 0)
        left_panel.setMaximumSize(150, 16777215)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(5)  # 明确设置按钮之间的间距为5像素
        left_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距适中
        left_layout.setAlignment(Qt.AlignTop)  # 确保组件从上到下对齐
        
        # 文件操作按钮
        self.import_image_button = QPushButton('导入图像')
        self.import_folder_button = QPushButton('导入文件夹')
        self.delete_image_button = QPushButton('删除图像')
        self.delete_work_button = QPushButton('清除工作区')
        
        # 添加文件操作按钮到布局
        left_layout.addWidget(self.import_image_button)
        left_layout.addWidget(self.import_folder_button)
        left_layout.addWidget(self.delete_image_button)
        left_layout.addWidget(self.delete_work_button)
        
        # 添加横杠分隔符
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(separator)
        
        # 模式选择按钮
        self.browse_mode_button = QPushButton('浏览模式')
        self.crop_mode_button = QPushButton('裁切模式')
        self.resize_mode_button = QPushButton('缩放模式')
        self.mark_mode_button = QPushButton('打标模式')
        self.correct_mode_button = QPushButton('修正模式')
        
        # 添加模式选择按钮到布局
        left_layout.addWidget(self.browse_mode_button)
        left_layout.addWidget(self.crop_mode_button)
        left_layout.addWidget(self.resize_mode_button)
        left_layout.addWidget(self.mark_mode_button)
        left_layout.addWidget(self.correct_mode_button)
        
        # ========== 中间工作区域 ==========
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # 图像显示区
        self.image_display_widget = QWidget()
        self.image_display_widget.setMinimumSize(400, 300)
        self.image_display_widget.setStyleSheet('background-color: #f0f0f0;')
        self.image_display_layout = QVBoxLayout(self.image_display_widget)
        
        # 添加显示容器到布局
        center_layout.addWidget(self.image_display_widget)
        
        # 第一个横杠分隔符：图像显示区和模式操作区之间
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        center_layout.addWidget(separator1)
        
        # 使用统一模式显示管理器设置UI
        self.mode_manager.setup_ui(center_layout, self.image_display_widget)
        
        # 处理状态区
        process_status_widget = QWidget()
        process_status_widget.setMaximumSize(16777215, 60)
        process_status_layout = QVBoxLayout(process_status_widget)
        
        self.process_info_label = QLabel('处理信息: 就绪')
        
        # 创建水平布局用于放置进度条标签和进度条
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel('处理进度:')
        self.process_progress_bar = QProgressBar()
        self.process_progress_bar.setValue(0)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.process_progress_bar)
        
        process_status_layout.addWidget(self.process_info_label)
        process_status_layout.addLayout(progress_layout)
        
        center_layout.addWidget(process_status_widget)
        
        # ========== 右侧图像列表面板 ==========
        right_panel = QWidget()
        right_panel.setMinimumSize(400, 0)  # 增加到当前宽度的两倍
        right_panel.setMaximumSize(400, 16777215)
        right_layout = QVBoxLayout(right_panel)
        
        # 创建图像列表组件
        self.image_list_widget = ImageListWidget(self)
        
        right_layout.addWidget(self.image_list_widget)
        
        # 创建左侧竖线分隔符
        left_vline = QFrame()
        left_vline.setFrameShape(QFrame.VLine)
        left_vline.setFrameShadow(QFrame.Sunken)
        left_vline.setMaximumWidth(2)
        
        # 创建右侧竖线分隔符
        right_vline = QFrame()
        right_vline.setFrameShape(QFrame.VLine)
        right_vline.setFrameShadow(QFrame.Sunken)
        right_vline.setMaximumWidth(2)
        
        # 将三个面板和分隔符添加到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(left_vline)
        main_layout.addWidget(center_panel)
        main_layout.addWidget(right_vline)
        main_layout.addWidget(right_panel)
           
    def connect_signals(self):
        # 文件操作相关信号
        self.import_image_button.clicked.connect(self.image_list_widget.import_image)
        self.import_folder_button.clicked.connect(self.image_list_widget.import_folder)
        self.delete_image_button.clicked.connect(self.image_list_widget.delete_image)
        self.delete_work_button.clicked.connect(self.image_list_widget.delete_workspace)
        
        # 模式选择相关信号
        self.browse_mode_button.clicked.connect(lambda: self.set_mode('default'))
        self.crop_mode_button.clicked.connect(lambda: self.set_mode('crop'))
        self.resize_mode_button.clicked.connect(lambda: self.set_mode('resize'))
        self.mark_mode_button.clicked.connect(lambda: self.set_mode('mark'))
        self.correct_mode_button.clicked.connect(lambda: self.set_mode('correct'))
        
        # 连接图像列表变化信号
        self.image_list_widget.image_list_table.itemChanged.connect(self._update_buttons_state)
        self.image_list_widget.image_list_table.model().rowsInserted.connect(self._update_buttons_state)
        self.image_list_widget.image_list_table.model().rowsRemoved.connect(self._update_buttons_state)
        
        # 初始按钮状态
        self._update_buttons_state()

    def _update_buttons_state(self):
        """根据图像列表状态更新按钮可用状态"""
        has_images = len(self.image_list_widget.image_list) > 0

        # 文件操作按钮
        self.delete_image_button.setEnabled(has_images)
        self.delete_work_button.setEnabled(has_images)

        # 模式按钮
        for mode in ['default', 'crop', 'resize', 'mark', 'correct']:
            self._set_mode_button_state(mode, has_images)
        
        current_mode = self.mode_manager.get_current_mode()
        if current_mode is not None and not has_images:
            self.set_mode(None)
        if current_mode is None and has_images:
            self.set_mode('default', confirm=False)
        
    def set_mode(self, mode, confirm=True):
        """设置当前模式，委托给统一模式显示管理器处理，并显示确认对话框"""
        # 空模式不需要确认对话框
        if mode == 'empty':
            success, message = self.mode_manager.set_mode(mode)
            if success:
                self.update_process_info('请先导入图像文件')
            return
            
        if mode is None:
            self.mode_manager.set_mode(mode)
            return

        if not confirm:
            success, message = self.mode_manager.set_mode(mode)
            if success:
                self._set_mode_button_state(mode, False)
                self.update_process_info(f'请开始操作！')
            return
        
        from PyQt5.QtWidgets import QMessageBox
        # 显示确认对话框
        mode_names = {
            'default': '浏览模式', 
            'crop': '裁切模式', 
            'resize': '缩放模式', 
            'mark': '打标模式',
            'correct': '修正模式'
        }
        mode_display_name = mode_names.get(mode, mode)
        reply = QMessageBox.question(
            self,
            '确认切换模式',
            f'确定要切换到{mode_display_name}吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # 默认选择"否"以防止误操作
        )
        
        # 如果用户确认，才切换模式
        if reply == QMessageBox.Yes:
            # 禁用当前模式按钮
            current_mode = self.mode_manager.get_current_mode()
            if current_mode:
                self._set_mode_button_state(current_mode, True)
            
            success, message = self.mode_manager.set_mode(mode)
            if success:
                # 禁用新模式的按钮
                self._set_mode_button_state(mode, False)
                self.update_process_info(f'已切换到{mode_display_name}')
    
    def _set_mode_button_state(self, mode, enabled):
        """设置模式按钮的可用状态"""
        button_map = {
            'default': self.browse_mode_button,
            'crop': self.crop_mode_button,
            'resize': self.resize_mode_button,
            'mark': self.mark_mode_button,
            'correct': self.correct_mode_button
        }
        # 空模式不需要按钮
        if mode == 'empty':
            # 禁用所有模式按钮
            for btn in button_map.values():
                btn.setEnabled(False)
            return
            
        # 对于普通模式，启用所有按钮，然后根据需要禁用当前模式按钮
        for btn in button_map.values():
            btn.setEnabled(True)
        
        button = button_map.get(mode)
        if button and not enabled:
            button.setEnabled(enabled)
    
    def update_process_info(self, info):
        """更新处理信息"""
        self.process_info_label.setText(f'处理信息: {info}')
        QApplication.processEvents()
    
    def get_mode_name(self):
        """获取当前模式的名称"""
        current_mode = self.mode_opt_manager.get_current_mode()
        if current_mode:
            return self.mode_opt_manager.get_mode_display_name(current_mode)
        return ''
    
    def display_selected_image(self, row):
        """显示指定行的图像"""
        # 获取图像管理器对象
        if 0 <= row < len(self.image_list_widget.image_list):
            img_manager = self.image_list_widget.image_list[row]
            img_path = img_manager.image_path
            
            # 设置图像到模式显示管理器
            self.mode_manager.set_image(img_manager)
            
            # 更新处理信息
            self.update_process_info(f'已显示图像: {os.path.basename(img_path)}')
        else:
            self.reset_image_display()
            self.update_process_info('请选择一张图像')
    
    def reset_image_display(self):
        """重置图像显示区域到初始状态"""
        self.mode_manager.reset()
        
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理图像标签的大小变化"""
        current_component = self.mode_manager.get_current_display_component()
        if obj == current_component and event.type() == QEvent.Resize:
            # 调用当前组件的resizeEvent方法
            obj.resizeEvent(event)
        return super().eventFilter(obj, event)
    
if __name__ == '__main__':
    app = QApplication(sys.argv) 
    window = ImageProcessorApp()
    window.showMaximized()  # 启动窗口时最大化显示

    sys.exit(app.exec_())