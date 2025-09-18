from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class ModeManager:
    """
    模式与显示统一管理器
    
    这个类负责统一管理模式操作区和图像显示区，确保每个模式都有对应的显示组件，
    简化模式切换逻辑，使开发更加统一和高效。
    """
    def __init__(self, app=None):
        """
        初始化模式显示管理器
        
        参数:
            app: 应用程序主窗口实例
        """
        self.app = app
        self.mode_opt_manager = None  # ModeManager实例
        self.image_display_manager = None  # ImageDisplayManager实例
        
        # 保存模式与显示组件的对应关系
        self.mode_display_map = {
            'crop': 'crop',        # 裁切模式对应裁切显示组件
            'resize': 'resize',    # 缩放模式对应缩放显示组件
            'mark': 'mark',        # 打标模式对应打标显示组件
            'correct': 'correct',  # 修正模式对应修正显示组件
            'default': 'default'   # 默认模式对应默认显示组件
        }
    
    def set_mode_opt_manager(self, mode_opt_manager):
        """
        设置模式操作管理器
        
        参数:
            mode_opt_manager: 已初始化的ModeOptManager实例
        """
        self.mode_opt_manager = mode_opt_manager
        
    def set_image_display_manager(self, image_display_manager):
        """
        设置图像显示管理器
        
        参数:
            image_display_manager: 已初始化的ImageDisplayManager实例
        """
        self.image_display_manager = image_display_manager
    
    def register_mode_display_pair(self, mode_name, display_name):
        """
        注册模式与显示组件的对应关系
        
        参数:
            mode_name: 模式名称
            display_name: 显示组件名称
        """
        self.mode_display_map[mode_name] = display_name
    
    def set_mode(self, mode_name):
        """
        统一切换模式，同时更新操作区域和显示区域
        
        参数:
            mode_name: 要切换到的模式名称 (None表示无模式状态)
        
        返回:
            (success, message): 成功标志和消息
        """
        # 处理None状态
        if mode_name is None:
            # 1. 通过模式管理器退出当前模式
            if self.mode_opt_manager:
                self.mode_opt_manager.exit_current_mode()
            
            # 2. 通过图像显示管理器重置显示
            if self.image_display_manager:
                self.image_display_manager.reset()
            
            # 3. 更新应用程序状态信息
            if self.app and hasattr(self.app, 'update_process_info'):
                self.app.update_process_info('已重置为无模式状态')
            
            return True, '已重置为无模式状态'
        
        # 正常模式切换逻辑
        # 1. 先通过模式管理器切换模式操作区域
        if self.mode_opt_manager:
            mode_success, mode_message = self.mode_opt_manager.set_mode(mode_name)
            if not mode_success:
                return False, mode_message
        
        # 2. 然后通过图像显示管理器切换显示组件
        if self.image_display_manager:
            display_name = self.mode_display_map.get(mode_name, 'default')
            self.image_display_manager.set_mode(display_name)
        
        # 3. 更新应用程序状态信息
        if self.app and hasattr(self.app, 'update_process_info'):
            if mode_name == 'default':
                self.app.update_process_info('当前为默认模式')
        
        return True, f'成功切换到{mode_name}模式'
    
    def exit_current_mode(self):
        """
        退出当前模式，返回到默认状态
        
        返回:
            (success, message): 成功标志和消息
        """
        # 1. 退出当前模式操作
        if self.mode_opt_manager:
            exit_success, exit_message = self.mode_opt_manager.exit_current_mode()
        
        # 2. 切换回默认显示组件
        if self.image_display_manager:
            self.image_display_manager.set_mode('default')
        
        return True, '已退出所有模式，返回到默认状态'
    
    def setup_ui(self, parent_layout, display_widget):
        """
        统一设置UI组件
        
        参数:
            parent_layout: 主布局（通常用于放置operation_widget）
            display_widget: 图像显示容器
        """
        # 1. 设置模式管理器的UI
        if self.mode_opt_manager:
            self.mode_opt_manager.setup_ui(parent_layout)
        
        # 2. 设置图像显示管理器的显示容器
        if self.image_display_manager:
            self.image_display_manager.set_display_widget(display_widget)
            # 默认显示默认组件
            self.image_display_manager.set_mode('default')
    
    def get_current_mode(self):
        """
        获取当前激活的模式名称
        
        返回:
            当前模式名称或None
        """
        if self.mode_opt_manager:
            return self.mode_opt_manager.get_current_mode()
        return None
    
    def get_current_display_component(self):
        """
        获取当前显示组件
        
        返回:
            当前显示组件实例或None
        """
        if self.image_display_manager:
            return self.image_display_manager.get_current_component()
        return None
    
    def perform_current_mode_action(self, *args, **kwargs):
        """
        执行当前模式的操作
        
        参数:
            *args, **kwargs: 传递给模式操作的参数
        
        返回:
            (success, message): 成功标志和消息
        """
        if self.mode_opt_manager:
            return self.mode_opt_manager.perform_current_mode_action(*args, **kwargs)
        return False, '请先选择一个操作模式'
    
    def set_image(self, image_manager):
        """
        设置要显示的图像
        
        参数:
            image_manager: 图像管理器实例
        """
        if self.image_display_manager:
            self.image_display_manager.set_image(image_manager)
    
    def reset(self):
        """
        重置所有组件
        """
        # 1. 退出当前模式
        self.exit_current_mode()
        
        # 2. 重置图像显示
        if self.image_display_manager:
            self.image_display_manager.reset()
    
    def resizeEvent(self, event):
        """
        处理窗口大小变化事件
        
        参数:
            event: 窗口大小变化事件对象
        """
        if self.image_display_manager:
            self.image_display_manager.resizeEvent(event)