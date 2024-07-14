import os
import tempfile

from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QComboBox, QLabel, QListWidget, QMessageBox, QListWidgetItem, QCheckBox, QSplitter
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
import fitz

from pdf_operations import pair_pdfs, create_postcard_pdf
from image_processing import PreviewGenerator
from config import PAPER_SIZES

class ImageListItem(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        self.front_checkbox = QCheckBox("Front")
        self.back_checkbox = QCheckBox("Back")
        self.name_label = QLabel(os.path.basename(image_path))
        self.name_label.setMinimumWidth(200)  # Adjust this value as needed
        layout.addWidget(self.front_checkbox)
        layout.addWidget(self.back_checkbox)
        layout.addWidget(self.name_label)
        layout.addStretch()

class ImageListWidgetItem(QListWidgetItem):
    def __init__(self, image_path, list_widget):
        super().__init__(list_widget)
        self.image_widget = ImageListItem(image_path)
        list_widget.setItemWidget(self, self.image_widget)
        self.setFlags(self.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)

class PdfPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.front_label = QLabel("No front image selected")
        self.back_label = QLabel("No back image selected")
        self.front_label.setAlignment(Qt.AlignCenter)
        self.back_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.front_label)
        self.layout.addWidget(self.back_label)
        self.front_pdf_path = None
        self.back_pdf_path = None

    def load_pdfs(self, front_pdf_path=None, back_pdf_path=None):
        self.front_pdf_path = front_pdf_path
        self.back_pdf_path = back_pdf_path
        self.update_preview()

    def update_preview(self):
        self.update_side(self.front_label, self.front_pdf_path, "No front image selected")
        self.update_side(self.back_label, self.back_pdf_path, "No back image selected")

    def update_side(self, label, pdf_path, default_text):
        if pdf_path and isinstance(pdf_path, str) and os.path.exists(pdf_path):
            pixmap = self.get_pdf_pixmap(pdf_path, label.width(), label.height())
            label.setPixmap(pixmap)
        else:
            label.setText(default_text)

    def get_pdf_pixmap(self, pdf_path, max_width, max_height):
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)  # Load the first page
        
        zoom_x = max_width / page.rect.width
        zoom_y = max_height / page.rect.height
        zoom = min(zoom_x, zoom_y) * 0.95  # 0.95 to leave a small margin
        
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        
        # Draw a border around the pixmap
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(pixmap.rect())
        painter.end()
        
        return pixmap

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()

    def sizeHint(self):
        return QSize(800, 400)  # Suggest a default size

class PostcardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.images = []
        self.preview_generator = None
        self.initUI()
        self.setMinimumSize(1000, 600)  # Adjust these values as needed

    def initUI(self):
        self.setWindowTitle('Postcard Printer')
        self.setGeometry(100, 100, 1000, 600)

        # Create a central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

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

        # Right side - Preview and File List
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.preview_view = PdfPreviewWidget()
        self.file_list = QListWidget()

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.preview_view)
        splitter.addWidget(self.file_list)
        splitter.setSizes([700, 300])  # Adjust these values to change initial sizes

        right_layout.addWidget(splitter)

        # Add left and right widgets to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        # Connect buttons to functions
        self.select_images_button.clicked.connect(self.select_images)
        self.generate_button.clicked.connect(self.generate_pdfs)
        self.pair_button.clicked.connect(self.pair_pdfs)
        self.file_list.itemClicked.connect(self.update_preview)
        self.paper_size_combo.currentIndexChanged.connect(self.update_preview)

    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Image Files (*.png *.jpg *.bmp)")
        if files:
            self.images.extend(files)
            self.update_file_list()

    def update_file_list(self):
        self.file_list.clear()
        for image in self.images:
            item = ImageListWidgetItem(image, self.file_list)
            item.image_widget.front_checkbox.stateChanged.connect(self.update_preview)
            item.image_widget.back_checkbox.stateChanged.connect(self.update_preview)
        self.file_list.setMinimumWidth(400)  # Adjust this value as needed

    def generate_pdfs(self):
        if not self.images:
            QMessageBox.warning(self, "Warning", "No images selected")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if output_dir:
            paper_size = self.paper_size_combo.currentText()
            for index in range(self.file_list.count()):
                item = self.file_list.item(index)
                image_widget = self.file_list.itemWidget(item)
                image_path = image_widget.image_path
                if image_widget.front_checkbox.isChecked():
                    output_pdf = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}_front.pdf")
                    create_postcard_pdf(image_path, output_pdf, paper_size)
                if image_widget.back_checkbox.isChecked():
                    output_pdf = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}_back.pdf")
                    create_postcard_pdf(image_path, output_pdf, paper_size)
            QMessageBox.information(self, "Success", "PDFs generated successfully")

    def pair_pdfs(self):
        front_images = []
        back_images = []
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            image_widget = self.file_list.itemWidget(item)
            if image_widget.front_checkbox.isChecked():
                front_images.append(image_widget.image_path)
            if image_widget.back_checkbox.isChecked():
                back_images.append(image_widget.image_path)

        if not front_images or not back_images:
            QMessageBox.warning(self, "Warning", "Both front and back images are required for pairing")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory for Paired PDFs")
        if output_dir:
            paper_size = self.paper_size_combo.currentText()
            with tempfile.TemporaryDirectory() as temp_dir:
                front_pdfs = []
                back_pdfs = []
                for i, (front, back) in enumerate(zip(front_images, back_images)):
                    front_pdf = os.path.join(temp_dir, f"front_{i}.pdf")
                    back_pdf = os.path.join(temp_dir, f"back_{i}.pdf")
                    create_postcard_pdf(front, front_pdf, paper_size)
                    create_postcard_pdf(back, back_pdf, paper_size)
                    front_pdfs.append(front_pdf)
                    back_pdfs.append(back_pdf)
                
                paired_pdfs = pair_pdfs(front_pdfs, back_pdfs, output_dir)
            
            QMessageBox.information(self, "Success", f"{len(paired_pdfs)} PDFs paired successfully")

    def update_preview(self):
        front_image = None
        back_image = None
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            image_widget = self.file_list.itemWidget(item)
            if image_widget.front_checkbox.isChecked() and not front_image:
                front_image = image_widget.image_path
            if image_widget.back_checkbox.isChecked() and not back_image:
                back_image = image_widget.image_path
            if front_image and back_image:
                break

        front_pdf = self.create_temp_pdf(front_image)
        back_pdf = self.create_temp_pdf(back_image)

        self.preview_view.load_pdfs(front_pdf, back_pdf)

    def create_temp_pdf(self, image_path):
        if not image_path:
            return None
        try:
            temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_pdf.close()
            paper_size = self.paper_size_combo.currentText()
            create_postcard_pdf(image_path, temp_pdf.name, paper_size)
            return temp_pdf.name
        except Exception as e:
            print(f"Error creating temporary PDF: {e}")
            return None
    
    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred while generating the preview: {error_message}")

    def set_preview(self, pdf_path):
        self.preview_view.load_pdf(pdf_path)

    def cleanup_temp_files(self):
        if hasattr(self, 'temp_pdf_path'):
            try:
                os.remove(self.temp_pdf_path)
            except Exception as e:
                print(f"Error removing temporary file: {e}")

    def closeEvent(self, event):
        self.cleanup_temp_files()
        super().closeEvent(event)
