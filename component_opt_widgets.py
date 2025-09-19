from abc import ABC, abstractmethod
from abc import ABC, abstractmethod
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFrame, QFileDialog, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import Qt

class BaseOptMode(ABC):
    """模式基类，定义模式的通用接口"""
    def __init__(self, name, display_name, ui_height, app=None):
        self.name = name  # 模式唯一标识符
        self.display_name = display_name  # 模式显示名称
        self.ui_height = ui_height  # 模式UI高度
        self.app = app  # 应用程序引用
        self.ui_container = None  # 模式UI组件的容器
        self.ui_components = []  # 模式特有的UI组件列表
        self.parent_layout = None  # 父布局引用

    def create_ui(self, parent_layout):
        """创建模式特有的UI组件"""
        # 保存父布局引用
        self.parent_layout = parent_layout
        
        # 创建UI容器
        self.ui_container = QWidget()
        self.ui_container.setMaximumSize(16777215, self.ui_height)
        
        # 子类应该重写get_ui_layout方法来提供具体的UI布局
        layout = self.get_ui_layout()
        if layout:
            self.ui_container.setLayout(layout)
            parent_layout.addWidget(self.ui_container)
            # 创建后默认隐藏
            self.ui_container.hide()
        
        return self.ui_container
    
    def get_ui_layout(self):
        """获取模式特有的UI布局"""
        # 子类必须重写此方法以提供自定义布局
        layout = QHBoxLayout()
        default_label = QLabel(f'未实现的{self.display_name}模式UI')
        layout.addWidget(default_label)
        return layout
    
    def show_ui(self):
        """显示模式UI"""
        if self.ui_container:
            self.ui_container.show()
    
    def hide_ui(self):
        """隐藏模式UI"""
        if self.ui_container:
            self.ui_container.hide()
    
    @abstractmethod
    def on_enter(self):
        """进入模式时执行的操作"""
        pass
    
    @abstractmethod
    def on_exit(self):
        """退出模式时执行的操作"""
        pass
    
    def add_ui_component(self, component):
        """添加模式特有的UI组件"""
        self.ui_components.append(component)

class CropOptMode(BaseOptMode):
    """裁切模式"""
    def __init__(self, app=None):
        super().__init__('crop', '裁切', 60,app)
        self.ratio_combo = None
    
    def get_ui_layout(self):
        """获取裁切模式特有的UI布局"""
        layout = QHBoxLayout()
        
        # 裁切比例标签和下拉框
        ratio_label = QLabel('裁切比例:')
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(['1:1', '3:4', '4:3', '9:16', '16:9'])
        self.add_ui_component(self.ratio_combo)
        
        # 连接比例变化信号
        self.ratio_combo.currentTextChanged.connect(self.on_ratio_changed)

        # 添加到主布局
        layout.addWidget(ratio_label)
        layout.addWidget(self.ratio_combo)
        
        return layout
    
    def on_ratio_changed(self, ratio_str):
        """处理比例变化事件"""
        if self.app:
            # 通过app的mode_manager获取当前显示组件
            if hasattr(self.app, 'mode_manager'):
                display_component = self.app.mode_manager.get_current_display_component()
                if display_component and hasattr(display_component, 'set_aspect_ratio'):
                    display_component.set_aspect_ratio(ratio_str)
    
    def on_enter(self):
        if self.app:
            self.app.update_process_info(f'已切换到 {self.display_name}模式。'
                '矩形框实时跟随鼠标，左键确定区域，右键取消，滚轮缩放')
            # 初始化比例
            if hasattr(self.app, 'mode_manager'):
                current_ratio = self.ratio_combo.currentText()
                display_component = self.app.mode_manager.get_current_display_component()
                if display_component and hasattr(display_component, 'set_aspect_ratio'):
                    display_component.set_aspect_ratio(current_ratio)
        self.show_ui()
    
    def on_exit(self):
        self.hide_ui()
    
class ResizeOptMode(BaseOptMode):
    """缩放模式"""
    def __init__(self, app=None):
        super().__init__('resize', '缩放', 120, app)
        self.width_edit = None
        self.height_edit = None
        self.apply_button = None
        self.cancel_button = None
    
    def get_ui_layout(self):
        """获取缩放模式特有的UI布局"""
        layout = QHBoxLayout()
        
        # 宽度输入
        width_label = QLabel('宽:')
        self.width_edit = QLineEdit()
        self.width_edit.setPlaceholderText('输入宽度')
        self.add_ui_component(self.width_edit)
        
        # 高度输入
        height_label = QLabel('高:')
        self.height_edit = QLineEdit()
        self.height_edit.setPlaceholderText('输入高度')
        self.add_ui_component(self.height_edit)
        
        # 按钮
        button_layout = QVBoxLayout()
        self.apply_button = QPushButton('应用缩放')
        self.cancel_button = QPushButton('取消缩放')
        
        # 连接信号
        if self.app:
            self.apply_button.clicked.connect(self.perform_action)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        
        # 添加到主布局
        layout.addWidget(width_label)
        layout.addWidget(self.width_edit)
        layout.addWidget(height_label)
        layout.addWidget(self.height_edit)
        layout.addStretch(1)
        layout.addLayout(button_layout)
        
        return layout
    
    def on_enter(self):
        if self.app:
            self.app.update_process_info(f'已切换到 {self.display_name}模式')
        self.show_ui()
    
    def on_exit(self):
        self.hide_ui()
    
    def perform_action(self, param=None, option=None):
        """执行缩放操作"""
        if self.app:
            selected_images = self.app.image_list_widget.get_selected_images()
            if selected_images:
                width = self.width_edit.text() if self.width_edit else ''
                height = self.height_edit.text() if self.height_edit else ''
                for img in selected_images:
                    img.state |= img.STATE_RESIZE  # 使用ImageDataManager的STATE_RESIZE
                return True, f'{self.display_name}处理完成，尺寸: {width}x{height}'
            else:
                return False, '请先选择要处理的图像'
        return False, '操作失败'

class MarkOptMode(BaseOptMode):
    """打标模式"""
    def __init__(self, app=None):
        super().__init__('mark', '打标', 120, app)
        self.model_path_label = None
        self.select_model_button = None
        self.retry_button = None
        self.continue_button = None
        self.stop_button = None
        self.model_path = ''
    
    def get_ui_layout(self):
        """获取打标模式特有的UI布局"""
        layout = QHBoxLayout()
        
        # 模型选择
        select_model_layout = QVBoxLayout()
        self.model_path_label = QLabel('未选择模型')
        self.select_model_button = QPushButton('选择模型')
        
        # 连接信号
        self.select_model_button.clicked.connect(self.select_model)
        
        select_model_layout.addWidget(self.model_path_label)
        select_model_layout.addWidget(self.select_model_button)
        
        # 推理控制按钮
        control_layout = QVBoxLayout()
        self.retry_button = QPushButton('重新推理')
        self.continue_button = QPushButton('继续推理')
        self.stop_button = QPushButton('停止推理')
        
        # 连接信号
        if self.app:
            self.retry_button.clicked.connect(lambda: self.perform_action('retry'))
            self.continue_button.clicked.connect(lambda: self.perform_action('continue'))
            self.stop_button.clicked.connect(lambda: self.perform_action('stop'))
        
        control_layout.addWidget(self.retry_button)
        control_layout.addWidget(self.continue_button)
        control_layout.addWidget(self.stop_button)
        
        # 添加到主布局
        layout.addLayout(select_model_layout)
        layout.addStretch(1)
        layout.addLayout(control_layout)
        
        return layout
    
    def select_model(self):
        """选择模型文件夹"""
        directory = QFileDialog.getExistingDirectory(self.app, "选择模型文件夹")
        if directory:
            self.model_path = directory
            self.model_path_label.setText(f'已选择模型: {directory.split("/")[-1]}')
    
    def on_enter(self):
        if self.app:
            self.app.update_process_info(f'已切换到 {self.display_name}模式')
        self.show_ui()
    
    def on_exit(self):
        self.hide_ui()
    
    def perform_action(self, action_type):
        """执行打标操作"""
        if self.app:
            selected_images = self.app.image_list_widget.get_selected_images()
            if not self.model_path:
                return False, '请先选择模型'
            
            if selected_images:
                for img in selected_images:
                    img.state |= img.STATE_INFER  # 使用ImageDataManager的STATE_INFER
                action_text = {
                    'retry': '重新推理',
                    'continue': '继续推理',
                    'stop': '停止推理'
                }.get(action_type, '未知操作')
                return True, f'{self.display_name}{action_text}完成'
            else:
                return False, '请先选择要处理的图像'
        return False, '操作失败'

class DefaultOptMode(BaseOptMode):
    """默认浏览模式"""
    def __init__(self, app=None):
        super().__init__('browse', '浏览', 60, app)
        self.info_label = None
    
    def get_ui_layout(self):
        """获取浏览模式特有的UI布局"""
        layout = QHBoxLayout()
        
        # 创建信息标签
        self.info_label = QLabel('浏览模式 - 您可以查看和选择图像')
        self.info_label.setStyleSheet('color: #333;')
        
        layout.addWidget(self.info_label)
        layout.addStretch(1)  # 添加弹性空间
        
        return layout
    
    def on_enter(self):
        if self.app:
            self.app.update_process_info('已切换到浏览模式\n提示：您可以查看和选择图像进行操作')
        self.show_ui()
    
    def on_exit(self):
        self.hide_ui()

class EmptyOptMode(BaseOptMode):
    """空模式"""
    def __init__(self, app=None):
        super().__init__('empty', '空状态', 20, app)
        self.info_label = None
    
    def get_ui_layout(self):
        """获取空模式特有的UI布局"""
        layout = QHBoxLayout()
        
        # 创建信息标签
        # self.info_label = QLabel('暂无图像，请先导入图像文件')
        # self.info_label.setStyleSheet('color: gray; font-style: italic;')
        
        # layout.addWidget(self.info_label)
        layout.addStretch(1)  # 添加弹性空间
        
        return layout
    
    def on_enter(self):
        if self.app:
            self.app.update_process_info('请先导入图像文件')
        self.show_ui()
    
    def on_exit(self):
        self.hide_ui()

class CorrectOptMode(BaseOptMode):
    """修正模式"""
    def __init__(self, app=None):
        super().__init__('correct', '修复', 400, app)
        self.source_edit = None
        self.target_edit = None
        self.translate_button = None
        self.apply_button = None
        self.cancel_button = None
    
    def get_ui_layout(self):
        """获取修复模式特有的UI布局"""
        layout = QVBoxLayout()
        
        # 文本编辑区域
        edit_layout = QHBoxLayout()
        
        # 源文本编辑框
        source_label = QLabel('原文:')
        self.source_edit = QTextEdit()
        self.source_edit.setPlaceholderText('输入要修复的文本')
        self.source_edit.setMaximumHeight(80)
        self.add_ui_component(self.source_edit)
        
        # 目标文本编辑框
        target_label = QLabel('修复后:')
        self.target_edit = QTextEdit()
        self.target_edit.setPlaceholderText('修复后的文本将显示在这里')
        self.target_edit.setMaximumHeight(80)
        self.add_ui_component(self.target_edit)
        
        # 添加到编辑布局
        source_vlayout = QVBoxLayout()
        source_vlayout.addWidget(source_label)
        source_vlayout.addWidget(self.source_edit)
        
        target_vlayout = QVBoxLayout()
        target_vlayout.addWidget(target_label)
        target_vlayout.addWidget(self.target_edit)
        
        edit_layout.addLayout(source_vlayout)
        edit_layout.addLayout(target_vlayout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.translate_button = QPushButton('翻译')
        self.apply_button = QPushButton('应用修改')
        self.cancel_button = QPushButton('取消修改')
        
        # 连接信号
        if self.app:
            self.translate_button.clicked.connect(self.perform_translation)
            self.apply_button.clicked.connect(self.perform_apply)
        
        button_layout.addWidget(self.translate_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        
        # 添加到主布局
        layout.addLayout(edit_layout)
        layout.addLayout(button_layout)
        
        return layout
    
    def perform_translation(self):
        """执行翻译操作"""
        source_text = self.source_edit.toPlainText()
        if source_text:
            # 这里只是模拟翻译
            self.target_edit.setPlainText(f'[翻译] {source_text}')
            return True, '翻译完成'
        return False, '请输入要翻译的文本'
    
    def perform_apply(self):
        """执行应用修改操作"""
        if self.app:
            selected_images = self.app.image_list_widget.get_selected_images()
            if selected_images:
                target_text = self.target_edit.toPlainText()
                for img in selected_images:
                    img.state |= img.STATE_FIX  # 使用ImageDataManager的STATE_FIX
                return True, f'{self.display_name}处理完成'
            else:
                return False, '请先选择要处理的图像'
        return False, '操作失败'
    
    def on_enter(self):
        if self.app:
            self.app.update_process_info(f'已切换到 {self.display_name}模式')
        self.show_ui()
    
    def on_exit(self):
        self.hide_ui()
    
    def perform_action(self, param=None, option=None):
        """兼容原有接口的执行操作方法"""
        return self.perform_apply()

class ModeOptManager:
    """模式操作管理器，负责管理所有模式和模式操作区的UI组件"""
    def __init__(self, app=None):
        self.app = app
        self.modes = {}
        self.current_mode = None
        
        # UI容器
        self.operation_widget = None
        self.operation_layout = None
        self.empty_state_widget = None
        
        # 初始化所有内置模式
        self.add_mode(EmptyOptMode(app))  # 添加空模式
        self.add_mode(DefaultOptMode(app))  # 添加默认浏览模式
        self.add_mode(CropOptMode(app))
        self.add_mode(ResizeOptMode(app))
        self.add_mode(MarkOptMode(app))
        self.add_mode(CorrectOptMode(app))
    
    def add_mode(self, mode):
        """添加一个新模式"""
        if isinstance(mode, BaseOptMode):
            mode.app = self.app  # 确保模式有应用程序引用
            self.modes[mode.name] = mode
    
    def remove_mode(self, mode_name):
        """删除一个模式"""
        if mode_name in self.modes:
            # 如果删除的是当前模式，先退出当前模式
            if self.current_mode == mode_name:
                self.exit_current_mode()
            del self.modes[mode_name]
    
    def set_mode(self, mode_name):
        """设置当前模式"""
        if mode_name in self.modes:
            # 先退出当前模式
            if self.current_mode:
                self.exit_current_mode()
            
            # 进入新模式
            self.current_mode = mode_name
            mode = self.modes[mode_name]
            
            # 隐藏空状态提示
            if self.empty_state_widget:
                self.empty_state_widget.hide()
            
            # 根据当前模式的ui_height调整操作区高度
            if hasattr(mode, 'ui_height') and mode.ui_height > 0:
                self.operation_widget.setMaximumHeight(mode.ui_height)
                self.operation_widget.setMinimumHeight(mode.ui_height)
            else:
                # 如果没有指定高度，则设置为合理的默认值
                self.operation_widget.setMaximumHeight(120)
                self.operation_widget.setMinimumHeight(60)
            
            # 调用模式特有的进入逻辑
            mode.on_enter()
            
            # 强制重新计算布局
            self.operation_widget.updateGeometry()
            
            return True, f'已切换到{mode.display_name}模式'
        return False, f'模式{mode_name}不存在'
    
    def exit_current_mode(self):
        """退出当前模式"""
        if self.current_mode and self.current_mode in self.modes:
            self.modes[self.current_mode].on_exit()
            self.current_mode = None
            
            # 显示空状态提示
            if self.empty_state_widget:
                self.empty_state_widget.show()
            
            # 恢复到默认高度，与空状态提示高度一致
            self.operation_widget.setMaximumHeight(60)
            self.operation_widget.setMinimumHeight(60)
            
            # 强制重新计算布局
            self.operation_widget.updateGeometry()
            
            if self.app:
                self.app.update_process_info('已退出所有模式')
            
            return True, '已退出当前模式'
        return False, '当前没有激活的模式'
    
    def setup_ui(self, parent_layout):
        """设置模式操作区的UI容器"""
        # 创建模式操作区部件
        self.operation_widget = QWidget()
        # 移除固定高度限制，允许根据当前模式的ui_height自适应
        self.operation_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.operation_layout = QVBoxLayout(self.operation_widget)
        
        # 创建空状态提示
        self.empty_state_widget = QLabel('请选择一个操作模式')
        self.empty_state_widget.setAlignment(Qt.AlignCenter)
        self.empty_state_widget.setStyleSheet('color: gray; font-style: italic;')
        # 设置空状态提示的固定高度，提供良好的初始体验
        self.empty_state_widget.setMinimumHeight(60)
        self.empty_state_widget.setMaximumHeight(60)
        self.operation_layout.addWidget(self.empty_state_widget)
        
        # 初始化所有模式的UI组件
        for mode in self.modes.values():
            mode.create_ui(self.operation_layout)
        
        # 添加分隔符
        separator = self.create_separator()
        self.operation_layout.addWidget(separator)
        
        # 添加到父布局
        parent_layout.addWidget(self.operation_widget)
        
        return self.operation_widget
    
    def get_current_mode_inputs(self):
        """获取当前模式的输入参数和选项（兼容旧接口）"""
        return '', ''
    
    def create_separator(self, orientation='horizontal'):
        """创建分隔符"""
        separator = QFrame()
        if orientation == 'horizontal':
            separator.setFrameShape(QFrame.HLine)
        else:
            separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator
    
    def get_current_mode(self):
        """获取当前模式"""
        return self.current_mode
    
    def get_mode_display_name(self, mode_name):
        """获取模式的显示名称"""
        if mode_name in self.modes:
            return self.modes[mode_name].display_name
        return ''
    
    def perform_current_mode_action(self, *args, **kwargs):
        """执行当前模式的操作"""
        if self.current_mode and self.current_mode in self.modes:
            return self.modes[self.current_mode].perform_action(*args, **kwargs)
        return False, '请先选择一个操作模式'