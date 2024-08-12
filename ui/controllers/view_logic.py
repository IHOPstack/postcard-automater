import os
import shutil
import tempfile
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtCore import Qt
import fitz

from business_logic.image_operations import is_supported_image
from business_logic.pdf_operations import create_postcard_pdf, pair_pdfs

def select_images(parent_widget):
    files, _ = QFileDialog.getOpenFileNames(parent_widget, "Select Images", "", "Image Files (*.png *.jpg *.bmp)")
    return [f for f in files if is_supported_image(f)]

def generate_pdfs(images, paper_size, parent_widget):
    if not images:
        QMessageBox.warning(parent_widget, "Warning", "No images selected")
        return

    output_dir = QFileDialog.getExistingDirectory(parent_widget, "Select Output Directory")
    if output_dir:
        for image_path in images:
            output_pdf = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}.pdf")
            create_postcard_pdf(image_path, output_pdf, paper_size)
        QMessageBox.information(parent_widget, "Success", "PDFs generated successfully")

def pair_pdfs_wrapper(front_images, back_images, paper_size, parent_widget):
    output_dir = QFileDialog.getExistingDirectory(parent_widget, "Select Output Directory for Paired PDFs")
    if output_dir:
        with tempfile.TemporaryDirectory() as temp_dir:
            front_pdfs = [create_temp_pdf(img, temp_dir, paper_size, i, 'front') for i, img in enumerate(front_images)]
            back_pdfs = [create_temp_pdf(img, temp_dir, paper_size, i, 'back') for i, img in enumerate(back_images)]
            paired_pdfs = pair_pdfs(front_pdfs, back_pdfs, output_dir)
        
        QMessageBox.information(parent_widget, "Success", f"{len(paired_pdfs)} PDFs paired successfully")

def create_preview_pdfs(front_images, back_images, paper_size, temp_dir):
    front_pdfs = [create_temp_pdf(img, temp_dir, paper_size, i, 'front') for i, img in enumerate(front_images)]
    back_pdfs = [create_temp_pdf(img, temp_dir, paper_size, i, 'back') for i, img in enumerate(back_images)]
    return front_pdfs, back_pdfs

def create_temp_pdf(image_path, temp_dir, paper_size, index, side, force_create=False):
    temp_pdf = os.path.join(temp_dir, f"{side}_{index}.pdf")
    if force_create or not os.path.exists(temp_pdf):
        create_postcard_pdf(image_path, temp_pdf, paper_size)
    return temp_pdf

def get_pdf_pixmap(pdf_path, max_width, max_height):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)  # Load the first page
    
    # Print the original page size
    print(f"Original PDF page size: {page.rect.width}x{page.rect.height}")
    
    zoom_x = max_width / page.rect.width
    zoom_y = max_height / page.rect.height
    zoom = min(zoom_x, zoom_y) * 0.95  # 0.95 to leave a small margin
    
    # Print the calculated zoom factor
    print(f"Calculated zoom factor: {zoom}")
    
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

def cleanup_temp_files(temp_dir):
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error removing temporary directory: {e}")
