import os
import json
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QLabel, QListWidget, QListWidgetItem, QCheckBox, QPushButton, QMenu
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QColor, QBrush

from business_logic.image_operations import is_supported_image
from config import get_setting
from .file_controller import FileManager


class ImageListWidget(QListWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self._setup_header()
        self.main_window = main_window
        self.file_manager = main_window.file_manager
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

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

    def clear_all(self):
        self.clear()
        self._setup_header()
        self.file_manager.clear_files()

    def show_context_menu(self, position: QPoint):
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(position))
        if action == delete_action:
            self.delete_selected_items()

    def delete_selected_items(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))
        self.save_persisted_files()

    def load_persisted_files(self):
        if get_setting("user_modifiable.persist_files"):
            try:
                with open("persisted_files.json", "r") as f:
                    files = json.load(f)
                for file in files:
                    self.add_item(file)
            except FileNotFoundError:
                pass

    def add_item(self, image_path):
        item = QListWidgetItem(self)
        image_widget = ImageListItem(image_path, self.main_window)
        item.setSizeHint(image_widget.sizeHint())
        self.setItemWidget(item, image_widget)
        
        # Connect checkbox signals to main window's update_preview method
        image_widget.front_checkbox.stateChanged.connect(self.main_window.update_preview)
        image_widget.back_checkbox.stateChanged.connect(self.main_window.update_preview)
        
        return image_widget

    def load_persisted_files(self):
        if get_setting("user_modifiable.persist_files"):
            try:
                with open("persisted_files.json", "r") as f:
                    files = json.load(f)
                for file in files:
                    if os.path.exists(file):
                        self.add_item(file, is_persisted=True)
                    else:
                        print(f"Warning: File not found: {file}")
                # After loading all persisted files, update the preview
                self.main_window.update_preview()
            except FileNotFoundError:
                print("No persisted files found.")

    def dragEnterEvent(self, event: QDragEnterEvent):
        print("Drag enter event received in ImageListWidget")

        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        print("Drag move event triggered")  # Debug print
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
                self.main_window.handle_file_list_drop(files)
        else:
            super().dropEvent(event)

class ImageListItem(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
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
