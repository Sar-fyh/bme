import sys
import csv
import pandas as pd
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QGroupBox, QMenuBar, QMenu, QPushButton, QDateEdit, QComboBox, QFileDialog, QCheckBox
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QBrush, QColor
import os
import zipfile
from datetime import datetime


class BloodCellAnalysisUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.is_editing = False
        self.editing_item = None
        self.data_file = "blood_cell_data.csv"
        self.load_data()
        self.original_background_colors = {}
        self.setGeometry(600, 40, 800, 100)
        self.setMinimumSize(800, 600)
        self.setMaximumSize(1600, 1000)

    def init_ui(self):
        self.setWindowTitle("外周血细胞检测系统--患者信息")
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #333333;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
            }
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #cccccc;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTableWidget QHeaderView::section {
                background-color: #f0f0f0;
                color: #333333;
                border: none;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QDateEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()

        menu_bar_layout = QHBoxLayout()
        button_names = ["保存", "删除", "编辑" ,"导出", "退出"]
        self.buttons = {}
        for name in button_names:
            button = QPushButton(name)
            if name == "保存":
                button.clicked.connect(self.on_save_button_click)
            elif name == "编辑":
                button.clicked.connect(self.on_edit_button_click)
            elif name == "删除":
                button.clicked.connect(self.on_delete_button_click)
            elif name == "导出":
                button.clicked.connect(self.on_export_button_click)
            
            elif name == "退出":
                button.clicked.connect(self.on_exit_button_click)
            self.buttons[name] = button
            menu_bar_layout.addWidget(button)

        top_layout.addLayout(menu_bar_layout)
        top_layout.addStretch()

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入查询关键字")
        search_layout.addWidget(self.search_input)

        search_button = QPushButton("查询")
        search_button.clicked.connect(self.on_search_button_click)
        search_layout.addWidget(search_button)

        self.cancel_search_button = QPushButton("取消查询")
        self.cancel_search_button.clicked.connect(self.on_cancel_search_button_click)
        self.cancel_search_button.hide()
        search_layout.addWidget(self.cancel_search_button)

        top_layout.addLayout(search_layout)

        main_layout.addLayout(top_layout)

        self.select_all_checkbox = QCheckBox("全选")
        self.select_all_checkbox.setChecked(True)
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_checkbox_changed)
        main_layout.addWidget(self.select_all_checkbox)

        content_layout = QHBoxLayout()

        left_group_box = QGroupBox("")
        left_layout = QVBoxLayout()

        info_labels = ["患者姓名", "患者性别", "患者年龄", "住院号", "床号", "送检科室", "血片号", "送检医院", "标本类型", "染色类型", "送检日期", "报告日期", "送检医生", "报告医生", "审核医生"]
        self.input_widgets = []
        for index, label_text in enumerate(info_labels):
            label = QLabel(label_text)
            left_layout.addWidget(label)
            if label_text == "患者性别":
                gender_combo = QComboBox()
                gender_combo.addItems(["男", "女"])
                gender_combo.setFixedHeight(30)
                self.input_widgets.append(gender_combo)
                left_layout.addWidget(gender_combo)
            elif label_text in ["送检日期", "报告日期"]:
                date_edit = QDateEdit()
                date_edit.setCalendarPopup(True)
                date_edit.setDate(QDate.currentDate())
                date_edit.setMinimumWidth(150)
                date_edit.setFixedHeight(30)
                self.input_widgets.append(date_edit)
                left_layout.addWidget(date_edit)
            else:
                line_edit = QLineEdit()
                line_edit.setMinimumWidth(150)
                line_edit.setFixedHeight(30)
                self.input_widgets.append(line_edit)
                left_layout.addWidget(line_edit)

        left_group_box.setLayout(left_layout)
        content_layout.addWidget(left_group_box)

        right_group_box = QGroupBox("患者信息列表")
        right_layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(len(info_labels) + 1)
        header_labels = ["选择"] + info_labels
        self.table_widget.setHorizontalHeaderLabels(header_labels)

        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.itemChanged.connect(self.on_item_changed)

        # 设置第一列（选择列）的宽度为 50 像素
        self.table_widget.setColumnWidth(0, 30)

        right_layout.addWidget(self.table_widget)
        right_group_box.setLayout(right_layout)
        content_layout.addWidget(right_group_box)

        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 3)

        main_layout.addLayout(content_layout)

        self.show()
        self.add_checkboxes()

    def add_checkboxes(self):
        for row in range(self.table_widget.rowCount()):
            checkbox_item = QTableWidgetItem()
            checkbox_item.setCheckState(Qt.Unchecked)
            # 设置复选框所在单元格的背景色为很浅的颜色（例如浅灰色）
            checkbox_item.setBackground(QBrush(QColor(240, 240, 240)))  
            self.table_widget.setItem(row, 0, checkbox_item)

    def on_select_all_checkbox_changed(self, state):
        target_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        for row in range(self.table_widget.rowCount()):
            checkbox_item = self.table_widget.item(row, 0)
            if checkbox_item:
                # 确保状态不同时更新状态
                if checkbox_item.checkState() != target_state:
                    checkbox_item.setCheckState(target_state)
                # 强制刷新表格项以更新显示
                self.table_widget.update()

    def on_save_button_click(self):
        row_data = []
        for widget in self.input_widgets:
            if isinstance(widget, QLineEdit):
                row_data.append(widget.text())
            elif isinstance(widget, QComboBox):
                row_data.append(widget.currentText())
            elif isinstance(widget, QDateEdit):
                row_data.append(widget.date().toString("yyyy-MM-dd"))
        for widget in self.input_widgets:
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QDateEdit):
                widget.setDate(QDate.currentDate())
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
        row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(row_count)

        checkbox_item = QTableWidgetItem()
        checkbox_item.setCheckState(Qt.Unchecked)
        # 设置新插入的复选框所在单元格的背景色为很浅的颜色（例如浅灰色）
        checkbox_item.setBackground(QBrush(QColor(240, 240, 240)))  
        self.table_widget.setItem(row_count, 0, checkbox_item)

        for col, item in enumerate(row_data, start=1):
            table_item = QTableWidgetItem(item)
            self.table_widget.setItem(row_count, col, table_item)

        self.save_data()

    def on_edit_button_click(self):
        selected_rows = self.get_selected_rows()
        if selected_rows:
            self.editing_item = self.table_widget.item(selected_rows[0], 1)
            self.table_widget.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
            self.is_editing = True

    def on_item_changed(self, item):
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.is_editing = False
        self.editing_item = None
        self.save_data()
    
    def on_delete_button_click(self):
        if self.select_all_checkbox.isChecked():
            # 如果全选被勾选，删除所有行
            for row in range(self.table_widget.rowCount() - 1, -1, -1):
                self.table_widget.removeRow(row)
        else:
            # 否则只删除选中的行
            selected_rows = self.get_selected_rows()
            for row in sorted(selected_rows, reverse=True):
                self.table_widget.removeRow(row)
        self.save_data()

    def on_exit_button_click(self):
        self.save_data()
        self.close()

    def on_search_button_click(self):
        keyword = self.search_input.text()
        if keyword:
            self.original_background_colors = {}
            for row in range(self.table_widget.rowCount()):
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item:
                        self.original_background_colors[(row, col)] = item.background()
                        if keyword in item.text():
                            item.setBackground(QBrush(QColor(255, 255, 0)))
            self.cancel_search_button.show()

    def on_cancel_search_button_click(self):
        for (row, col), color in self.original_background_colors.items():
            item = self.table_widget.item(row, col)
            if item:
                item.setBackground(color)
        self.cancel_search_button.hide()
        self.search_input.clear()

    def mousePressEvent(self, event):
        if self.is_editing and not self.table_widget.rect().contains(event.pos()):
            self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
            self.is_editing = False
            self.editing_item = None
            self.save_data()
        super().mousePressEvent(event)

    def save_data(self):
        with open(self.data_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            header = [self.table_widget.horizontalHeaderItem(i).text() for i in range(1, self.table_widget.columnCount())]
            writer.writerow(header)
            for row in range(self.table_widget.rowCount()):
                row_data = []
                for col in range(1, self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append('')
                writer.writerow(row_data)

    def load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                for row_num, row in enumerate(reader):
                    self.table_widget.insertRow(row_num)
                    checkbox_item = QTableWidgetItem()
                    checkbox_item.setCheckState(Qt.Unchecked)
                    # 设置加载数据时复选框所在单元格的背景色为很浅的颜色（例如浅灰色）
                    checkbox_item.setBackground(QBrush(QColor(240, 240, 240)))  
                    self.table_widget.setItem(row_num, 0, checkbox_item)
                    for col_num, item in enumerate(row):
                        table_item = QTableWidgetItem(item)
                        self.table_widget.setItem(row_num, col_num + 1, table_item)
        except FileNotFoundError:
            pass

    def on_export_button_click(self):
        if self.select_all_checkbox.isChecked():
            # 如果全选被勾选，导出所有行
            data = []
            header = [self.table_widget.horizontalHeaderItem(i).text() for i in range(1, self.table_widget.columnCount())]
            data.append(header)
            for row in range(self.table_widget.rowCount()):
                row_data = []
                for col in range(1, self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append('')
                data.append(row_data)
        else:
            # 否则只导出选中的行
            selected_rows = self.get_selected_rows()
            if selected_rows:
                data = []
                header = [self.table_widget.horizontalHeaderItem(i).text() for i in range(1, self.table_widget.columnCount())]
                data.append(header)
                for row in selected_rows:
                    row_data = []
                    for col in range(1, self.table_widget.columnCount()):
                        item = self.table_widget.item(row, col)
                        if item:
                            row_data.append(item.text())
                        else:
                            row_data.append('')
                    data.append(row_data)
            else:
                return

        df = pd.DataFrame(data[1:], columns=data[0])

        file_path, _ = QFileDialog.getSaveFileName(self, "保存为 Excel 文件", "", "Excel 文件 (*.xlsx)")
        if file_path:
            df.to_excel(file_path, index=False, engine='openpyxl')

    def get_selected_rows(self):
        selected_rows = []
        for row in range(self.table_widget.rowCount()):
            checkbox_item = self.table_widget.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                selected_rows.append(row)
        return selected_rows


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BloodCellAnalysisUI()
    sys.exit(app.exec())