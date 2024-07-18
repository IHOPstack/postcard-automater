import os
import tempfile

from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QComboBox, QLabel, QListWidget, QMessageBox, QListWidgetItem, QCheckBox, QSplitter, QAction
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QImage, QPainter, QDragEnterEvent, QDropEvent
from PyQt5.QtGui import QColor, QLinearGradient, QPalette, QBrush
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPageLayout, QPageSize
from PyQt5.QtCore import QMarginsF

import fitz

from ..controllers.view_logic import get_pdf_pixmap
from business_logic.image_operations import is_supported_image
from config import get_setting, update_setting

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, QCheckBox, QPushButton
from config import get_setting, update_setting

class PdfPreviewWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.front_viewer = PdfViewer(is_front=True, main_window=self.main_window, parent=self)
        self.back_viewer = PdfViewer(is_front=False, main_window=self.main_window, parent=self)
        self.layout.addWidget(self.front_viewer)
        self.layout.addWidget(self.back_viewer)

    def load_pdfs(self, front_pdf_paths=None, back_pdf_paths=None):
        self.front_viewer.load_pdfs(front_pdf_paths)
        self.back_viewer.load_pdfs(back_pdf_paths)

class PdfViewer(QWidget):
    def __init__(self, is_front, main_window, parent=None):
        super().__init__(parent)
        self.is_front = is_front
        self.main_window = main_window
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.image_label = QLabel(f"No image selected")
        self.image_label.setAlignment(Qt.AlignCenter)
        
        self.layout.addWidget(self.prev_button)
        self.layout.addWidget(self.image_label, 1)
        self.layout.addWidget(self.next_button)

        self.pdf_paths = []
        self.current_page = 0

        self.prev_button.clicked.connect(self.show_previous)
        self.next_button.clicked.connect(self.show_next)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            files = [u.toLocalFile() for u in event.mimeData().urls() if is_supported_image(u.toLocalFile())]
            if files:
                self.main_window.handle_preview_drop(files, self.is_front)

    def load_pdfs(self, pdf_paths):
        self.pdf_paths = pdf_paths or []
        self.current_page = 0
        self.update_preview()

    def update_preview(self):
        if self.pdf_paths and 0 <= self.current_page < len(self.pdf_paths):
            pixmap = get_pdf_pixmap(self.pdf_paths[self.current_page], self.image_label.width(), self.image_label.height())
            # Print the size of the generated pixmap
            print(f"Generated pixmap size: {pixmap.width()}x{pixmap.height()}")
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("No image selected")
        
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < len(self.pdf_paths) - 1)


    def show_previous(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_preview()

    def show_next(self):
        if self.current_page < len(self.pdf_paths) - 1:
            self.current_page += 1
            self.update_preview()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()
