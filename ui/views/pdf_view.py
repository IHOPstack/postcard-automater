from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from ..controllers.view_logic import get_pdf_pixmap, update_preview
from business_logic.image_operations import is_supported_image

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton

class PdfPreviewWidget(QWidget):
    def __init__(self, file_manager, paper_size_combo):
        super().__init__()
        self.file_manager = file_manager
        self.paper_size_combo = paper_size_combo
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.front_viewer = PdfViewer(is_front=True, parent=self)
        self.back_viewer = PdfViewer(is_front=False, parent=self)
        self.layout.addWidget(self.front_viewer)
        self.layout.addWidget(self.back_viewer)

    def load_pdfs(self, front_pdf_paths=None, back_pdf_paths=None):
        self.front_viewer.load_pdfs(list(reversed(front_pdf_paths)) if front_pdf_paths else None)
        self.back_viewer.load_pdfs(list(reversed(back_pdf_paths)) if back_pdf_paths else None)

    def update_preview(self):
        front_images, back_images = self.file_manager.get_selected_images()
        paper_size = self.paper_size_combo.currentText()
        front_pdfs, back_pdfs = update_preview(front_images, back_images, paper_size, self.file_manager.temp_dir)
        print(f"Front PDFs: {front_pdfs}")
        print(f"Back PDFs: {back_pdfs}")
        self.front_viewer.load_pdfs(front_pdfs)
        self.back_viewer.load_pdfs(back_pdfs)

    def handle_preview_drop(self, files, is_front):
        added_files = self.file_manager.add_files(files, auto_select_front=is_front, auto_select_back=not is_front)
        return added_files

class PdfViewer(QWidget):
    def __init__(self, is_front, parent=None):
        super().__init__(parent)
        self.is_front = is_front
        self.pdf_paths = []
        self.current_page = 0
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

        self.prev_button.clicked.connect(self.show_previous)
        self.next_button.clicked.connect(self.show_next)

        self.setAcceptDrops(True)

    def load_pdfs(self, pdf_paths):
        self.pdf_paths = pdf_paths or []
        self.current_page = 0
        self.update_display()

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
        self.update_display()

    def update_display(self):
        print(f"Updating display. Current page: {self.current_page}, Total pages: {len(self.pdf_paths)}")
        if self.pdf_paths and 0 <= self.current_page < len(self.pdf_paths):
            pixmap = get_pdf_pixmap(self.pdf_paths[self.current_page], self.image_label.width(), self.image_label.height())
            if pixmap:
                print(f"Pixmap created. Size: {pixmap.width()}x{pixmap.height()}")
                self.image_label.setPixmap(pixmap)
            else:
                print("Failed to create pixmap")
                self.image_label.setText("Failed to load image")
        else:
            print("No image selected")
            self.image_label.setText("No image selected")
        
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < len(self.pdf_paths) - 1)

    def show_previous(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()

    def show_next(self):
        if self.current_page < len(self.pdf_paths) - 1:
            self.current_page += 1
            self.update_display()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()
