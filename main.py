import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QPushButton, QLabel, QListWidget, QListWidgetItem, QSplitter,
                               QFrame, QFileSystemModel, QTreeView, QToolButton, QSizePolicy, QComboBox, QSlider, QDoubleSpinBox,QSpinBox) 
from PySide6.QtGui import QIcon, QFont, QPixmap, QGradient, QLinearGradient, QBrush, QColor
from PySide6.QtCore import Qt, QSize

from NewMain import InteractionFunctions


class LabelingUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("外周血细胞检测系统")
        self.setGeometry(100, 100, 1600, 900)
        icon_path = "C://system//system//1//nihao.png"
        app_icon = QIcon(icon_path)
        self.setWindowIcon(app_icon)

        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 主布局（水平布局）
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)  # 增加边距
        main_layout.setSpacing(15)  # 增加间距

        # 使用分割器实现可调节布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧控制面板
        left_panel = QWidget()
        left_panel.setMinimumWidth(200)  # 增加最小宽度
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)  # 增加间距

        # 按钮部分容器，添加边框样式
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setFrameShadow(QFrame.Raised)
        button_frame.setLineWidth(0)  # 去除边框线
        button_frame.setLayout(QVBoxLayout())
        button_frame.layout().setContentsMargins(0, 0, 0, 0)

        # 创建带图标的工具按钮
        self.btn_new = self.create_tool_button("   New File", "icons/new.png")
        self.btn_open = self.create_tool_button("   Open File", "icons/open.png")
        self.btn_save = self.create_tool_button("   Save Model", "icons/save.png")
        self.btn_prev = self.create_tool_button("   Prev Image", "icons/prev.png")
        self.btn_next = self.create_tool_button("   Next Image", "icons/next.png")
        self.btn_auto = self.create_tool_button("   X-Labeling", "icons/auto.png")
        self.btn_translate = self.create_tool_button("   ADF", "icons/translate.png")
        self.btn_start = self.create_tool_button("   Start Train", "icons/run.png")
        self.btn_stop = self.create_tool_button("   Stop ", "icons/stop.png")
        self.btn_infor = self.create_tool_button("   Register", "icons/Register.png")
        self.btn_select = self.create_tool_button("   Extract sample", "icons/select.png")

        button_frame.layout().addWidget(self.btn_new)
        button_frame.layout().addWidget(self.btn_open)
        button_frame.layout().addWidget(self.btn_prev)
        button_frame.layout().addWidget(self.btn_next)
        button_frame.layout().addWidget(self.btn_auto)
        button_frame.layout().addWidget(self.btn_select)
        button_frame.layout().addWidget(self.btn_start)
        button_frame.layout().addWidget(self.btn_stop)
        button_frame.layout().addWidget(self.btn_translate)
        button_frame.layout().addWidget(self.btn_save)
        button_frame.layout().addWidget(self.btn_infor)

        left_layout.addWidget(button_frame)

        # 添加分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #d9d9d9;")  # 分割线颜色
        left_layout.addWidget(separator)

        # 参数设置部分容器，添加边框样式
        param_frame = QFrame()
        param_frame.setFrameShape(QFrame.StyledPanel)
        param_frame.setFrameShadow(QFrame.Raised)
        param_frame.setLineWidth(0)  # 去除边框线
        param_frame.setLayout(QVBoxLayout())
        param_frame.layout().setContentsMargins(10, 10, 10, 10)
        param_frame.layout().setSpacing(5)  # 增加间距

        # 参数设置文字提示
        param_label = QLabel("参数设置")
        param_label.setAlignment(Qt.AlignCenter)  # 将文字居中显示
        param_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")  # 字体样式
        param_frame.layout().addWidget(param_label)

        # 新增两个 QSpinBox 及描述标签
        spinbox1_label = QLabel("Epochs")
        spinbox1_label.setStyleSheet("font-size: 12px; color: #555;")  # 字体样式
        param_frame.layout().addWidget(spinbox1_label)
        self.spinbox1 = QSpinBox()
        self.spinbox1.setRange(0, 100)  # 设置取值范围
        self.spinbox1.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
                color: #333;
            }
        """)
        param_frame.layout().addWidget(self.spinbox1)





        spinbox4_label = QLabel("Select")
        spinbox4_label.setStyleSheet("font-size: 12px; color: #555;")  # 字体样式
        param_frame.layout().addWidget(spinbox4_label)
        self.spinbox4 = QSpinBox()
        self.spinbox4.setRange(0, 600)  # 设置取值范围
        self.spinbox4.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
                color: #333;
            }
        """)
        param_frame.layout().addWidget(self.spinbox4)


        spinbox2_label = QLabel("标准(Iou)")
        spinbox2_label.setStyleSheet("font-size: 12px; color: #555;")  # 字体样式
        param_frame.layout().addWidget(spinbox2_label)
        self.spinbox2 = QDoubleSpinBox()
        self.spinbox2.setRange(0, 200)  # 设置取值范围
        self.spinbox2.setStyleSheet("""
            QDoubleBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
                color: #333;
            }
        """)
        param_frame.layout().addWidget(self.spinbox2)

        spinbox3_label = QLabel("配置(Conf)")
        spinbox3_label.setStyleSheet("font-size: 12px; color: #555;")  # 字体样式
        param_frame.layout().addWidget(spinbox3_label)
        self.spinbox3 = QDoubleSpinBox()
        self.spinbox3.setRange(0, 200)  # 设置取值范围
        self.spinbox3.setStyleSheet("""
            QDoubleBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
                color: #333;
            }
        """)
        param_frame.layout().addWidget(self.spinbox3)

        # 添加一个伸缩项，将下方内容往下推
        param_frame.layout().addStretch()

        left_layout.addWidget(param_frame)

        # 中间图像显示区域
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        self.image_label = QLabel("Image Display Area...")
        self.image_label.setAlignment(Qt.AlignCenter)

        # 设置图片显示区域的初始大小
        self.image_label.setMinimumSize(800, 600)  # 设置最小大小
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许扩展

        # 添加渐变背景
        gradient = QLinearGradient(0, 0, 0, self.image_label.height())
        gradient.setColorAt(0, QColor(240, 240, 240))
        gradient.setColorAt(1, QColor(220, 220, 220))
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(240, 240, 240, 255), stop:1 rgba(220, 220, 220, 255));
                border: 1px solid #ccc;
                border-radius: 8px;
                color: #333;
                font-size: 16px;
                padding: 20px;
            }}
        """)
        center_layout.addWidget(self.image_label)

        # 右侧信息面板
        right_panel = QWidget()
        right_panel.setMinimumWidth(300)  # 增加最小宽度
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(12)  # 增加间距

        # 标签列表
        lbl_tags = QLabel("Result")
        lbl_tags.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")  # 字体样式
        self.tag_list = QListWidget()
        self.tag_list.setStyleSheet("""
            QListWidget {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 8px;
                color: #333;
                font-size: 14px;
            }
            QListWidget::item:selected {
                background-color: #007BFF;
                color: white;
            }
        """)

        # 在标签列表右下角添加一个清除按钮
        self.tag_list_button = QPushButton("Purge")  
        self.tag_list_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        right_layout.addWidget(lbl_tags)
        right_layout.addWidget(self.tag_list)

        # 创建一个水平布局来放置按钮，并将其推到右下角
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 增加一个弹簧，将按钮推到右边
        button_layout.addWidget(self.tag_list_button)  # 添加按钮到布局中
        right_layout.addLayout(button_layout)  # 将按钮布局添加到主布局中

        # 文件列表
        lbl_files = QLabel("File List")
        lbl_files.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")  # 字体样式
        self.file_tree = QTreeView()
        self.file_tree.setRootIsDecorated(False)
        self.file_tree.setHeaderHidden(True)
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath('')
        self.file_tree.setModel(self.file_model)
        self.file_tree.setStyleSheet("""
            QTreeView {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 8px;
                color: #333;
                font-size: 14px;
            }
            QTreeView::item:selected {
                background-color: #007BFF;
                color: white;
            }
        """)

        right_layout.addWidget(lbl_files)
        right_layout.addWidget(self.file_tree)

        # 组装分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 1000, 350])  # 设置初始大小

        main_layout.addWidget(splitter)

        # 设置全局样式
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: Segoe UI;
                font-size: 12px;
                color: #333;
            }
            QToolButton {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                text-align: left;
                min-width: 120px;
                color: #333;
                icon-size: 24px;
                padding-left: 32px;
            }
            QToolButton:hover {
                background-color: #e6e6e6;
            }
            QToolButton:pressed {
                background-color: #d9d9d9;
            }
            QLabel {
                color: #333;
            }
            QTreeView, QListView {
                color: #333;
            }
        """)

        # 初始化 InteractionFunctions
        self.interaction_functions = InteractionFunctions(self)

    def create_tool_button(self, text, icon_path):
        """创建带自定义图标的工具按钮"""
        btn = QToolButton()
        btn.setText(text)

        # 加载图标（使用绝对路径或相对路径）
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                btn.setIcon(QIcon(pixmap))
                btn.setIconSize(QSize(24, 24))  # 调整图标尺寸

        btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        btn.setStyleSheet("""
               QToolButton {
                   text-align: left;
                   padding: 8px 12px;
                   margin: 2px 0;
                   background-color: #fff;
                   border: 1px solid #ccc;
                   border-radius: 4px;
                   color: #333;
               }
               QToolButton:hover {
                   background-color: #e6e6e6;
               }
               QToolButton:pressed {
                   background-color: #d9d9d9;
               }
           """)
        return btn


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelingUI()
    window.show()
    sys.exit(app.exec())