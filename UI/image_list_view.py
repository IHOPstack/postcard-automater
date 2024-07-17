import os
import tempfile

from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QComboBox, QLabel, QListWidget, QMessageBox, QListWidgetItem, QCheckBox, QSplitter, QAction
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QImage, QPainter, QDragEnterEvent, QDropEvent
from PyQt5.QtGui import QColor, QLinearGradient, QPalette, QBrush
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPageLayout, QPageSize
from PyQt5.QtCore import QMarginsF

from image_operations import is_supported_image

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, QCheckBox, QPushButton

class ImageListWidget(QListWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self._setup_header()
        self.main_window = main_window


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
        header_item.setSizeHint(header_widget.sizeHint())
        self.setItemWidget(header_item, header_widget)

        # Style the header
        header_color = QColor(180, 180, 180)
        header_item.setBackground(QBrush(header_color))
        header_item.setFlags(header_item.flags() & ~Qt.ItemIsSelectable)

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

    def add_item(self, image_path):
        item = QListWidgetItem(self)
        image_widget = ImageListItem(image_path)
        item.setSizeHint(image_widget.sizeHint())
        self.setItemWidget(item, image_widget)
        return image_widget

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
