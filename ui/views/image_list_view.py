import os
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QLabel, QListWidget, QListWidgetItem, QCheckBox, QPushButton, QMenu
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QColor, QBrush

from business_logic.image_operations import is_supported_image
from config import get_setting

class ImageListWidget(QListWidget):
    def __init__(self, file_manager, pdf_preview):
        super().__init__()
        self.file_manager = file_manager
        self.pdf_preview = pdf_preview
        persisted_files = file_manager.images
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self._setup_header()
        self.add_items(persisted_files)
        self.setContextMenuPolicy(Qt.CustomContextMenu)


    def _setup_header(self):
        header_item = QListWidgetItem(self)
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(5, 2, 5, 2)
        self.select_all_front = QCheckBox("Front")
        self.select_all_back = QCheckBox("Back")
        header_layout.addWidget(self.select_all_front)
        header_layout.addWidget(self.select_all_back)
        header_layout.addWidget(QLabel("File Name"))
        header_layout.addStretch()
        clear_all_button = QPushButton("Clear All")
        clear_all_button.clicked.connect(self.clear_all)
        header_layout.addWidget(clear_all_button)
        header_item.setSizeHint(header_widget.sizeHint())
        self.setItemWidget(header_item, header_widget)

        # Style the header
        header_color = QColor(180, 180, 180)
        header_item.setBackground(QBrush(header_color))
        header_item.setFlags(header_item.flags() & ~Qt.ItemIsSelectable)

        self.select_all_front.stateChanged.connect(lambda state: self.select_all(state, is_front=True))
        self.select_all_back.stateChanged.connect(lambda state: self.select_all(state, is_front=False))

    def clear_all(self):
        self.clear()
        self._setup_header()
        self.file_manager.clear_files()
        self.pdf_preview.update_preview()

    def show_context_menu(self, position: QPoint):
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(position))
        if action == delete_action:
            self.delete_selected_items()

    def delete_selected_items(self):
        for item in self.selectedItems():
            image_widget = self.itemWidget(item)
            self.file_manager.remove_file(image_widget.image_path)
            self.takeItem(self.row(item))
            self.pdf_preview.update_preview()
    
    def add_item(self, file, auto_select_front=False, auto_select_back=False):
        item = QListWidgetItem(self)
        image_widget = ImageListItem(file, self.file_manager, self.pdf_preview)
        
        # Set checkbox state based on FileManager's selection
        image_widget.front_checkbox.setChecked(file in self.file_manager.front_images)
        image_widget.back_checkbox.setChecked(file in self.file_manager.back_images)
        
        item.setSizeHint(image_widget.sizeHint())
        self.setItemWidget(item, image_widget)
        self.pdf_preview.update_preview()
        return image_widget
    
    def add_items(self, files):
        for file in files:
            self.add_item(file)

    def update_image_list(self, image_path, state, is_front):
        self.file_manager.update_image_list(image_path, state == Qt.Checked, is_front)
        self.pdf_preview.update_preview()

    def dragEnterEvent(self, event: QDragEnterEvent):
        print("Drag enter event received in ImageListWidget")

        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        print("Drag move event triggered")
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            files = [u.toLocalFile() for u in event.mimeData().urls() if is_supported_image(u.toLocalFile())]
            if files:
                self.handle_file_list_drop(event)
        else:
            super().dropEvent(event)
    
    def select_all(self, state, is_front):
        is_checked = state == Qt.Checked
        self.file_manager.select_all(is_front, is_checked)
        self.update_all_checkboxes(is_front, is_checked)
        self.pdf_preview.update_preview()
        
    def update_all_checkboxes(self, is_front, is_checked):
        for index in range(1, self.count()):  # Start from 1 to skip header
            item = self.item(index)
            image_widget = self.itemWidget(item)
            if image_widget:
                if is_front:
                    image_widget.front_checkbox.setChecked(is_checked)
                else:
                    image_widget.back_checkbox.setChecked(is_checked)

    def handle_file_list_drop(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            files = [u.toLocalFile() for u in event.mimeData().urls() if is_supported_image(u.toLocalFile())]
            if files:
                added_files = self.file_manager.add_files(files)
                self.add_items(added_files)
                self.pdf_preview.update_preview()

    def dropEvent(self, event):
        self.handle_file_list_drop(event)

class ImageListItem(QWidget):
    def __init__(self, image_path, file_manager, pdf_preview):
        super().__init__()
        self.image_path = image_path
        self.file_manager = file_manager
        self.pdf_preview = pdf_preview
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        self.front_checkbox = QCheckBox("Front")
        self.back_checkbox = QCheckBox("Back")
        self.name_label = QLabel(os.path.basename(self.image_path))
        self.name_label.setMinimumWidth(200)
        layout.addWidget(self.front_checkbox)
        layout.addWidget(self.back_checkbox)
        layout.addWidget(self.name_label)
        layout.addStretch()

        self.front_checkbox.stateChanged.connect(self.on_checkbox_changed)
        self.back_checkbox.stateChanged.connect(self.on_checkbox_changed)

    def update_image_list(self, state, is_front):
        self.file_manager.update_image_list(self.image_path, state == Qt.Checked, is_front)

    def on_checkbox_changed(self):
        is_front = self.sender() == self.front_checkbox
        is_checked = self.sender().isChecked()
        self.file_manager.update_image_list(self.image_path, is_checked, is_front)
        self.pdf_preview.update_preview()
