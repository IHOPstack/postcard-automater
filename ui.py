import os
import tempfile

from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QComboBox, QLabel, QListWidget, QMessageBox, QListWidgetItem, QCheckBox, QSplitter
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QDragEnterEvent, QDropEvent
from PyQt5.QtGui import QColor, QLinearGradient, QPalette, QBrush
import fitz

from app_logic import select_images, generate_pdfs, pair_pdfs_wrapper, update_preview, cleanup_temp_files, get_pdf_pixmap
from image_operations import is_supported_image
from config import PAPER_SIZES

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

class PostcardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.images = []
        self.front_images = []
        self.back_images = []
        self.temp_dir = tempfile.mkdtemp()  # Create a temporary directory
        self.initUI()
        self.setMinimumSize(1000, 600)
        self.setAcceptDrops(True)

    def initUI(self):
        self.setWindowTitle('Postcard Printer')
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Set a fixed width for the left widget
        left_widget.setFixedWidth(200)  # Adjust this value as needed
        left_widget.setMaximumWidth(250)  # Set a maximum width

        self.select_images_button = QPushButton('Select Images')
        self.paper_size_combo = QComboBox()
        self.paper_size_combo.addItems(list(PAPER_SIZES.keys()))
        self.generate_button = QPushButton('Generate PDFs')
        self.pair_button = QPushButton('Pair PDFs')

        left_layout.addWidget(self.select_images_button)
        left_layout.addWidget(QLabel('Paper Size:'))
        left_layout.addWidget(self.paper_size_combo)
        left_layout.addWidget(self.generate_button)
        left_layout.addWidget(self.pair_button)
        left_layout.addStretch(1)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.preview_view = PdfPreviewWidget(main_window=self)
        self.file_list = ImageListWidget(main_window=self)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.preview_view)
        self.splitter.addWidget(self.file_list)
        self.splitter.setSizes([700, 300])

        right_layout.addWidget(self.splitter)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        self.select_images_button.clicked.connect(self.on_select_images)
        self.generate_button.clicked.connect(self.on_generate_pdfs)
        self.pair_button.clicked.connect(self.on_pair_pdfs)
        self.paper_size_combo.currentIndexChanged.connect(self.update_preview)

        self.file_list.select_all_front.stateChanged.connect(self.select_all_front_images)
        self.file_list.select_all_back.stateChanged.connect(self.select_all_back_images)

    def on_select_images(self):
        new_images = select_images(self)
        self.images.extend(new_images)
        self.update_file_list()

    def on_generate_pdfs(self):
        paper_size = self.paper_size_combo.currentText()
        generate_pdfs(self.images, paper_size, self)

    def on_pair_pdfs(self):
        if not self.front_images or not self.back_images:
            QMessageBox.warning(self, "Warning", "Both front and back images are required for pairing")
            return
        paper_size = self.paper_size_combo.currentText()
        pair_pdfs_wrapper(self.front_images, self.back_images, paper_size, self)

    def update_preview(self):
        self.front_images.clear()
        self.back_images.clear()
        for index in range(1, self.file_list.count()):
            item = self.file_list.item(index)
            image_widget = self.file_list.itemWidget(item)
            if image_widget.front_checkbox.isChecked():
                self.front_images.append(image_widget.image_path)
            if image_widget.back_checkbox.isChecked():
                self.back_images.append(image_widget.image_path)

        paper_size = self.paper_size_combo.currentText()
        front_pdfs, back_pdfs = update_preview(self.front_images, self.back_images, paper_size, self.temp_dir)
        self.preview_view.load_pdfs(front_pdfs, back_pdfs)

    def select_all_front_images(self, state):
        for index in range(1, self.file_list.count()):
            item = self.file_list.item(index)
            image_widget = self.file_list.itemWidget(item)
            image_widget.front_checkbox.setChecked(state == Qt.Checked)
        self.update_preview()

    def select_all_back_images(self, state):
        for index in range(1, self.file_list.count()):
            item = self.file_list.item(index)
            image_widget = self.file_list.itemWidget(item)
            image_widget.back_checkbox.setChecked(state == Qt.Checked)
        self.update_preview()

    def handle_file_list_drop(self, files):
        self.images.extend(files)
        self.update_file_list()

    def handle_preview_drop(self, files, is_front):
        self.images.extend(files)
        self.update_file_list(auto_select_front=is_front, auto_select_back=not is_front)

    def update_file_list(self, auto_select_front=False, auto_select_back=False):
        current_count = self.file_list.count() - 1
        for image in self.images[current_count:]:
            image_widget = self.file_list.add_item(image)
            image_widget.front_checkbox.stateChanged.connect(self.update_preview)
            image_widget.back_checkbox.stateChanged.connect(self.update_preview)
            
            if auto_select_front or (not self.front_images and not self.back_images):
                image_widget.front_checkbox.setChecked(True)
            elif auto_select_back or (self.front_images and not self.back_images):
                image_widget.back_checkbox.setChecked(True)

        self.file_list.setMinimumWidth(400)
        self.update_preview()

    def closeEvent(self, event):
        cleanup_temp_files(self.temp_dir)
        super().closeEvent(event)

