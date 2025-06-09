# -*- coding: utf-8 -*-

import os
import subprocess
from PySide6.QtWidgets import QFileDialog, QInputDialog, QListWidgetItem, QDialog, QLabel, QLineEdit, QPushButton, \
    QVBoxLayout, QMessageBox, QHBoxLayout
from PySide6.QtGui import QPixmap, QColor, QIcon
from PySide6.QtCore import QThread, Signal
from datetime import datetime
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QCheckBox
import shutil
import json
import AL_config2  # 导入配置文件
import hashlib
from infor import BloodCellAnalysisUI





def validate_input(username, password, email=None):
    """验证输入内容"""
    if not username or not password:
        return False, "用户名和密码不能为空"
    if email and "@" not in email:
        return False, "邮箱格式不正确"
    return True, ""


def hash_password(password):
    """对密码进行加密"""
    return hashlib.sha256(password.encode()).hexdigest()


class AdminLoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("管理员登录 - 外周血细胞检测系统")
        self.setGeometry(300, 300, 300, 200)
        self.setWindowIcon(QIcon('blood_icon.png'))  # 替换为血红细胞相关图标
        self.setStyleSheet(self.get_stylesheet())

        layout = QVBoxLayout()

        self.admin_username_label = QLabel("管理员账户:")
        self.admin_username_label.setFont(QFont("Arial", 12))
        self.admin_username_input = QLineEdit()
        self.admin_username_input.setPlaceholderText("请输入管理员账户")
        layout.addWidget(self.admin_username_label)
        layout.addWidget(self.admin_username_input)

        self.admin_password_label = QLabel("管理员密码:")
        self.admin_password_label.setFont(QFont("Arial", 12))
        self.admin_password_input = QLineEdit()
        self.admin_password_input.setEchoMode(QLineEdit.Password)
        self.admin_password_input.setPlaceholderText("请输入管理员密码")
        layout.addWidget(self.admin_password_label)
        layout.addWidget(self.admin_password_input)

        self.login_button = QPushButton("登录")
        self.login_button.setFont(QFont("Arial", 12))
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def get_stylesheet(self):
        return """
            QDialog {
                background-color: #fff;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
                color: #333;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #c0392b; /* 红色边框 */
                background-color: #fff;
            }
            QPushButton {
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                color: #fff;
                background-color: #c0392b; /* 红色背景 */
            }
            QPushButton:hover {
                background-color: #a93226;
            }
            QPushButton:pressed {
                background-color: #943126;
            }
        """

    def login(self):
        username = self.admin_username_input.text()
        password = self.admin_password_input.text()

        admin_username = "admin"
        admin_password = "admin123"

        if username == admin_username and password == admin_password:
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "管理员账户或密码错误")


class AdminWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("管理员平台 - 外周血细胞检测系统")
        self.setGeometry(300, 300, 400, 300)
        self.setWindowIcon(QIcon('blood_icon.png'))
        self.setStyleSheet(self.get_stylesheet())

        layout = QVBoxLayout()

        self.username_label = QLabel("用户名:")
        self.username_label.setFont(QFont("Arial", 12))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        self.password_label = QLabel("密码:")
        self.password_label.setFont(QFont("Arial", 12))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("请输入密码")
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        self.register_button = QPushButton("注册用户")
        self.register_button.setFont(QFont("Arial", 12))
        self.register_button.clicked.connect(self.register_user)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    def get_stylesheet(self):
        return """
            QDialog {
                background-color: #fff;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
                color: #333;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #c0392b;
                background-color: #fff;
            }
            QPushButton {
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                color: #fff;
                background-color: #c0392b;
            }
            QPushButton:hover {
                background-color: #a93226;
            }
            QPushButton:pressed {
                background-color: #943126;
            }
        """

    def register_user(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "错误", "用户名和密码不能为空")
            return

        users = {}
        if os.path.exists("users.json"):
            try:
                with open("users.json", "r") as f:
                    content = f.read()
                    if content.strip():
                        users = json.loads(content)
                    else:
                        users = {}
            except json.JSONDecodeError:
                users = {}

        if username in users:
            QMessageBox.warning(self, "错误", "用户名已存在")
            return

        users[username] = {
            "password": hash_password(password),
            "role": "user"
        }

        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)

        QMessageBox.information(self, "成功", "用户注册成功")


class ChangePasswordWindow(QDialog):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("修改密码 - 外周血细胞检测系统")
        self.setGeometry(300, 300, 300, 200)
        self.setWindowIcon(QIcon('blood_icon.png'))
        self.setStyleSheet(self.get_stylesheet())
        self.username = username

        layout = QVBoxLayout()

        self.old_password_label = QLabel("旧密码:")
        self.old_password_label.setFont(QFont("Arial", 12))
        self.old_password_input = QLineEdit()
        self.old_password_input.setEchoMode(QLineEdit.Password)
        self.old_password_input.setPlaceholderText("请输入旧密码")
        layout.addWidget(self.old_password_label)
        layout.addWidget(self.old_password_input)

        self.new_password_label = QLabel("新密码:")
        self.new_password_label.setFont(QFont("Arial", 12))
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("请输入新密码")
        layout.addWidget(self.new_password_label)
        layout.addWidget(self.new_password_input)

        self.confirm_password_label = QLabel("确认新密码:")
        self.confirm_password_label.setFont(QFont("Arial", 12))
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("请再次输入新密码")
        layout.addWidget(self.confirm_password_label)
        layout.addWidget(self.confirm_password_input)

        self.change_password_button = QPushButton("修改密码")
        self.change_password_button.setFont(QFont("Arial", 12))
        self.change_password_button.clicked.connect(self.change_password)
        layout.addWidget(self.change_password_button)

        self.setLayout(layout)

    def get_stylesheet(self):
        return """
            QDialog {
                background-color: #fff;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
                color: #333;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #c0392b;
                background-color: #fff;
            }
            QPushButton {
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                color: #fff;
                background-color: #c0392b;
            }
            QPushButton:hover {
                background-color: #a93226;
            }
            QPushButton:pressed {
                background-color: #943126;
            }
        """

    def change_password(self):
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not old_password or not new_password or not confirm_password:
            QMessageBox.warning(self, "错误", "请输入完整信息")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "错误", "两次输入的新密码不一致")
            return

        if os.path.exists("users.json"):
            with open("users.json", "r") as f:
                users = json.load(f)
                if self.username in users and users[self.username]["password"] == hash_password(old_password):
                    users[self.username]["password"] = hash_password(new_password)
                    with open("users.json", "w") as f:
                        json.dump(users, f)
                    QMessageBox.information(self, "成功", "密码修改成功")
                    self.close()
                else:
                    QMessageBox.warning(self, "错误", "旧密码错误")
        else:
            QMessageBox.warning(self, "错误", "用户信息文件不存在")


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("外周血细胞检测系统 - 登录")
        self.setGeometry(300, 300, 400, 300)
        self.setWindowIcon(QIcon("C://Users//l1313//Desktop//nihao//src//nihao.png"))  # 替换为血红细胞相关图标
        self.setStyleSheet(self.get_stylesheet())

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # 标题
        self.title_label = QLabel("外周血细胞检测系统")
        self.title_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #c0392b;")  # 红色标题
        layout.addWidget(self.title_label)

        # 欢迎信息
        self.welcome_label = QLabel("欢迎使用外周血细胞检测系统，请登录")
        self.welcome_label.setFont(QFont("Arial", 14))
        self.welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.welcome_label)

        # 用户名输入框
        self.username_label = QLabel("用户名:")
        self.username_label.setFont(QFont("Arial", 12))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setMinimumWidth(250)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        # 密码输入框
        self.password_label = QLabel("密码:")
        self.password_label.setFont(QFont("Arial", 12))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumWidth(250)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # 记住我复选框
        self.remember_me = QCheckBox("记住我")
        self.remember_me.setFont(QFont("Arial", 10))
        layout.addWidget(self.remember_me)

        # 登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setFont(QFont("Arial", 12,QFont.Bold))
        self.login_button.setFixedSize(150, 40)
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button, alignment=Qt.AlignCenter)

        # 修改密码按钮
        self.change_password_button = QPushButton("修改密码")
        self.change_password_button.setFont(QFont("Arial", 12,QFont.Bold))
        self.change_password_button.setFixedSize(150, 40)
        self.change_password_button.clicked.connect(self.show_change_password_window)
        layout.addWidget(self.change_password_button, alignment=Qt.AlignCenter)

        # 管理员登录按钮（右下角）
        self.admin_button = QPushButton()
        self.admin_button.setText("管理员")
        self.admin_button.setFont(QFont("Arial", 0.1))
        self.admin_button.setFixedSize(55, 35)
        self.admin_button.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                border: 2px solid #a93226;
                border-radius: 18px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #a93226;
                border: 2px solid #943126;
            }
            QPushButton:pressed {
                background-color: #943126;
                border: 2px solid #7b241c;
            }
        """)
        self.admin_button.clicked.connect(self.show_admin_login_window)

        # 将管理员按钮添加到布局的右下角
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 将按钮推到右边
        button_layout.addWidget(self.admin_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.load_login_info()

    def get_stylesheet(self):
        return """
            QDialog {
                background-color: #fff;
                background-image: url('blood_background.png'); /* 替换为血红细胞相关背景图片 */
                background-repeat: no-repeat;
                background-position: center;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
                color: #333;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #c0392b;
                background-color: #fff;
            }
            QPushButton {
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                color: #fff;
                background-color: #c0392b;
            }
            QPushButton:hover {
                background-color: #a93226;
            }
            QPushButton:pressed {
                background-color: #943126;
            }
            QCheckBox {
                font-size: 14px;
                color: #333;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:checked {
                background-color: #c0392b;
                border: 1px solid #a93226;
            }
        """

    def show_change_password_window(self):
        username = self.username_input.text()
        if username:
            change_password_window = ChangePasswordWindow(username)
            change_password_window.exec()
        else:
            QMessageBox.warning(self, "错误", "请先输入用户名")

    def show_admin_login_window(self):
        admin_login_window = AdminLoginWindow()
        if admin_login_window.exec() == QDialog.Accepted:
            admin_window = AdminWindow()
            admin_window.exec()

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        valid, message = validate_input(username, password)
        if not valid:
            QMessageBox.warning(self, "错误", message)
            return

        if os.path.exists("users.json"):
            with open("users.json", "r") as f:
                users = json.load(f)
                if username in users and users[username]["password"] == hash_password(password):
                    self.save_login_info()
                    self.current_user = username
                    self.accept()
                else:
                    QMessageBox.warning(self, "登录失败", "用户名或密码错误")
        else:
            QMessageBox.warning(self, "登录失败", "用户信息文件不存在")

    def load_login_info(self):
        if os.path.exists("login_info.json"):
            with open("login_info.json", "r") as f:
                login_info = json.load(f)
                self.username_input.setText(login_info.get("username", ""))
                self.remember_me.setChecked(login_info.get("remember_me", False))

    def save_login_info(self):
        if self.remember_me.isChecked():
            login_info = {
                "username": self.username_input.text(),
                "remember_me": True
            }
            with open("login_info.json", "w") as f:
                json.dump(login_info, f)
        else:
            if os.path.exists("login_info.json"):
                os.remove("login_info.json")

class ScriptRunner(QThread):
    output_signal = Signal(str, str)

    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path
        self.process = None

    def run(self):
        if os.path.exists(self.script_path) and os.path.isfile(self.script_path):
            try:
                startupinfo = None
                # 新增部分：处理 Windows 系统不显示窗口
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                # 以二进制模式读取输出
                self.process = subprocess.Popen(["python", self.script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupinfo)
                encodings_to_try = ['utf-8', 'gbk', 'cp1252']  # 可以根据需要添加更多编码
                for line in self.process.stdout:
                    if self.process.poll() is not None:  # 检查进程是否已经结束
                        break
                    decoded = None
                    for encoding in encodings_to_try:
                        try:
                            decoded = line.decode(encoding).strip()
                            break
                        except UnicodeDecodeError:
                            continue
                    if decoded:
                        # 根据输出内容判断消息类型
                        if "error" in decoded.lower():
                            self.output_signal.emit(decoded, "error")
                        elif "warning" in decoded.lower():
                            self.output_signal.emit(decoded, "warning")
                        elif "success" in decoded.lower():
                            self.output_signal.emit(decoded, "success")
                        else:
                            self.output_signal.emit(decoded, "info")
                self.process.wait()
                if self.process.returncode != 0:
                    self.output_signal.emit(f"Script exited with error code {self.process.returncode}", "error")
            except Exception as e:
                self.output_signal.emit(f"Error running script: {e}", "error")
        else:
            self.output_signal.emit(f"Script file not found: {self.script_path}", "error")

    def stop(self):
        """停止脚本运行"""
        if self.process and self.process.poll() is None:  # 检查进程是否存在且仍在运行
            self.process.terminate()  # 终止进程
            self.output_signal.emit("已停止运行", "info")


class InteractionFunctions:
    def __init__(self, window):
        self.window = window
        # 为按钮添加点击事件处理，并指定要运行的脚本文件地址
        self.window.btn_new.clicked.connect(self.create_folder)
        self.window.btn_open.clicked.connect(self.open_file)
        self.window.btn_save.clicked.connect(self.save)
        self.window.btn_prev.clicked.connect(self.prev_image)
        self.window.btn_next.clicked.connect(self.next_image)
        self.window.btn_auto.clicked.connect(lambda: self.run_script(r"C://system//system//1//X-AnyLabeling//anylabeling//app.py"))
        self.window.btn_translate.clicked.connect(lambda: self.run_script(r"./export.py"))
        self.window.btn_start.clicked.connect(self.start_script)  # 调用 start_script 方法
        self.window.btn_stop.clicked.connect(self.stop_script)  # 调用 stop_script 方法
        self.window.tag_list_button.clicked.connect(self.clear_history)
        self.window.btn_infor.clicked.connect(self.show_new_page)
        self.window.btn_select.clicked.connect(self.start_select)
        # 将 epochs 和 iou_thres 的设置转移到 LabelingUI 中的 spinbox1 和 spinbox2
        self.setup_param_settings()

    def setup_param_settings(self):
        # 获取 LabelingUI 中的 spinbox1 和 spinbox2
        self.epochs_spinbox = self.window.spinbox1
        self.iou_thres_spinbox = self.window.spinbox2
        self.conf_thres_spinbox=self.window.spinbox3
        self.select_spinbox=self.window.spinbox4
        # 设置初始值为默认值
        self.epochs_spinbox.setValue(AL_config2.epochs)
        self.select_spinbox.setValue(AL_config2.max_queried)
        self.iou_thres_spinbox.setDecimals(2)  # 设置小数位数为2
        self.iou_thres_spinbox.setSingleStep(0.01)  # 设置步长为0.01
        self.iou_thres_spinbox.setValue(AL_config2.iou_thres)
        self.conf_thres_spinbox.setDecimals(2)  # 设置小数位数为2
        self.conf_thres_spinbox.setSingleStep(0.01)  # 设置步长为0.01
        self.conf_thres_spinbox.setValue(AL_config2.conf_thres)
        # 连接信号槽
        self.epochs_spinbox.valueChanged.connect(self.update_epochs)
        self.iou_thres_spinbox.valueChanged.connect(self.update_iou_thres)
        self.conf_thres_spinbox.valueChanged.connect(self.update_conf_thres)
        self.select_spinbox.valueChanged.connect(self.update_a)
    def update_epochs(self, value):
        AL_config2.epochs = value
        self.update_config_file('epochs', value)
    
    def update_a(self, value):
        AL_config2.max_queried = value
        self.update_config_file('max_queried', value)
        

    def update_iou_thres(self, value):
        AL_config2.iou_thres = value
        self.update_config_file('iou_thres', value)

    def update_conf_thres(self, value):
        AL_config2.conf_thres = value
        self.update_config_file('conf_thres', value)

    def update_config_file(self, param_name, value):
        with open('AL_config2.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open('AL_config2.py', 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith(f'{param_name} ='):
                    if isinstance(value, int):
                        f.write(f'{param_name} = {value}\n')
                    else:
                        f.write(f'{param_name} = {value:.2f}\n')
                else:
                    f.write(line)

    def run_script(self, script_path):
        """运行指定的脚本文件，并将结果输出到右侧信息面板"""
        self.runner = ScriptRunner(script_path)
        self.runner.output_signal.connect(self.update_tag_list)
        self.runner.start()

    def start_script(self):
        """运行指定的脚本文件，并将结果输出到右侧信息面板"""
        print("正在训练中...")
        script_path = r"train_model.py"
        self.runner = ScriptRunner(script_path)
        self.runner.output_signal.connect(self.update_tag_list)
        self.runner.start()
    

    def start_select(self):
        """运行指定的脚本文件，并将结果输出到右侧信息面板"""
        print("正在取样中...")
        script_path = r"extract_images.py"
        self.runner = ScriptRunner(script_path)
        self.runner.output_signal.connect(self.update_tag_list)
        self.runner.start()

    def stop_script(self):
        """停止脚本运行"""
        if self.runner:
            self.runner.stop()

    def update_tag_list(self, message, msg_type="info"):
        """更新标签列表，使用颜色和图标来美化输出"""
        color_mapping = {
            "info": "#2B6CB0",  # 深蓝色
            "error": "#C53030",  # 深红色
            "warning": "#DD6B20",  # 橙色
            "success": "#38A169",  # 绿色
            "output": "#718096"  # 中灰色
        }

        item = QListWidgetItem(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        item.setForeground(QColor(color_mapping.get(msg_type, "#718096")))  # 默认灰色
        self.window.tag_list.addItem(item)
        self.window.tag_list.scrollToBottom()

    def create_folder(self):
        """创建新文件夹"""
        # 弹出文件夹选择对话框，让用户选择基础路径
        base_path = QFileDialog.getExistingDirectory(self.window, "选择基础路径")
        if base_path:
            # 让用户输入文件夹名称
            folder_name, ok = QInputDialog.getText(self.window, "输入文件夹名称", "请输入要创建的文件夹名称:")
            if ok and folder_name:
                folder_path = os.path.join(base_path, folder_name)
                try:
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                        self.update_tag_list(f"Folder created: {folder_path}", "success")
                    else:
                        self.update_tag_list(f"Folder already exists: {folder_path}", "warning")
                except Exception as e:
                    self.update_tag_list(f"Error creating folder: {e}", "error")

    def open_file(self):
        """打开用户选择的文件夹并显示其中的所有图片"""
        file_dialog = QFileDialog()
        folder_path = file_dialog.getExistingDirectory(self.window, "选择图片文件夹")
        if folder_path:
            # 获取文件夹中的所有图片文件
            self.image_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        self.image_files.append(os.path.join(root, file))
            if self.image_files:
                self.current_index = 0
                self.show_image()
            else:
                self.update_tag_list("所选文件夹中没有图片文件", "warning")
        else:
            self.update_tag_list("未选择任何文件夹", "warning")

    def show_image(self):
        """显示当前索引的图片"""
        if 0 <= self.current_index < len(self.image_files):
            image_path = self.image_files[self.current_index]
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.window.image_label.size(), Qt.KeepAspectRatio)
                self.window.image_label.setPixmap(scaled_pixmap)
            else:
                self.update_tag_list(f"无法加载图片: {image_path}", "error")

    def prev_image(self):
        """显示上一张图片"""
        if self.image_files:
            self.current_index = (self.current_index - 1) % len(self.image_files)
            self.show_image()

    def next_image(self):
        """显示下一张图片"""
        if self.image_files:
            self.current_index = (self.current_index + 1) % len(self.image_files)
            self.show_image()

    def clear_history(self):
        """清除右侧运行结果框内的记录"""
        self.window.tag_list.clear()
    def save(self):
        """将一个指定文件夹中的所有文件复制到另一个指定的文件夹中"""
        # 固定源文件夹和目标文件夹的路径
        source_folder_path = "C://Users//l1313//Desktop//nihao//src//runs//train//gun//weights"
        target_folder_path ="C://Users//l1313//Desktop//nihao//src//X-AnyLabeling//model"
        try:
            # 遍历源文件夹中的所有文件和子文件夹
            for root, dirs, files in os.walk(source_folder_path):
                for file in files:
                    source_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(source_file_path, source_folder_path)
                    target_file_path = os.path.join(target_folder_path, relative_path)
                    target_dir = os.path.dirname(target_file_path)
                    # 如果目标文件夹不存在，则创建
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    # 复制文件
                    shutil.copy2(source_file_path, target_file_path)
            self.update_tag_list(f"模型保存成功: 从 {source_folder_path} 到 {target_folder_path}", "success")
        except Exception as e:
            self.update_tag_list(f"模型保存失败: {e}", "error")
    def show_new_page(self):
        """显示导入的新页面"""
        self.new_page_window = BloodCellAnalysisUI()
        self.new_page_window.show()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # 显示登录窗口
    login_window = LoginWindow()
    if login_window.exec() == QDialog.Accepted:
        # 登录成功，显示主窗口
        from main import LabelingUI  # 导入主程序窗口
        main_window = LabelingUI()  # 创建主程序窗口实例
        main_window.show()  # 显示主程序窗口
    else:
        # 登录失败，退出程序
        QMessageBox.warning(None, "失败", "登录失败")
    sys.exit(app.exec())