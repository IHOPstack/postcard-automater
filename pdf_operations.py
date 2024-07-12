import os
import itertools
from PyPDF2 import PdfReader, PdfWriter
import os
import math
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import black
from tkinter import Tk, filedialog, simpledialog
from config import PAPER_SIZES

def combine_pdfs(front_pdf, back_pdf, output_path):
    pdf_writer = PdfWriter()
    pdf_reader1 = PdfReader(front_pdf)
    pdf_reader2 = PdfReader(back_pdf)

    page1 = pdf_reader1.pages[0]
    page2 = pdf_reader2.pages[0]

    pdf_writer.add_page(page1)
    pdf_writer.add_page(page2)

    with open(output_path, 'wb') as fh:
        pdf_writer.write(fh)

def pair_pdfs(front_pdfs, back_pdfs, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    paired_pdfs = []

    for front_pdf, back_pdf in zip(front_pdfs, back_pdfs):
        front_name = os.path.basename(front_pdf)
        back_name = os.path.basename(back_pdf)
        output_filename = os.path.join(output_folder, f'{front_name}&{back_name}.pdf')
        combine_pdfs(front_pdf, back_pdf, output_filename)
        paired_pdfs.append(output_filename)

    return paired_pdfs

def select_image():
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
    return file_path

def select_output_folder():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    return folder_path

def select_paper_size():
    root = Tk()
    root.withdraw()
    sizes = list(PAPER_SIZES.keys())
    choice = simpledialog.askinteger("Paper Size", "Select paper size:\n" + "\n".join([f"{i+1}. {size}" for i, size in enumerate(sizes)]), minvalue=1, maxvalue=len(sizes))
    return list(PAPER_SIZES.keys())[choice-1] if choice else None

def calculate_optimal_layout(card_width, card_height, paper_width, paper_height, margin, min_spacing=1):
    usable_width = paper_width - 2 * margin
    usable_height = paper_height - 2 * margin

    def calc_fit(w, h):
        cols = math.floor((usable_width + min_spacing) / (w + min_spacing))
        rows = math.floor((usable_height + min_spacing) / (h + min_spacing))
        return cols * rows, cols, rows

    # Calculate fits for both orientations
    standard_fit, standard_cols, standard_rows = calc_fit(card_width, card_height)
    rotated_fit, rotated_cols, rotated_rows = calc_fit(card_height, card_width)

    # Determine the best layout
    if rotated_fit > standard_fit or (rotated_fit == standard_fit and card_height > card_width):
        total = rotated_fit
        cols = rotated_cols
        rows = rotated_rows
        card_width, card_height = card_height, card_width
        rotated = True
    else:
        total = standard_fit
        cols = standard_cols
        rows = standard_rows
        rotated = False

    x_spacing = (usable_width - cols * card_width) / (cols + 1)
    y_spacing = (usable_height - rows * card_height) / (rows + 1)

    return {
        'total': total,
        'cols': cols,
        'rows': rows,
        'card_width': card_width,
        'card_height': card_height,
        'x_spacing': x_spacing,
        'y_spacing': y_spacing,
        'rotated': rotated
    }
def create_postcard_pdf(image_path, output_pdf, paper_size_name):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with Image.open(image_path) as img:
        original_card_width = img.width * 25.4 / 300
        original_card_height = img.height * 25.4 / 300

    paper_width, paper_height = PAPER_SIZES[paper_size_name]
    margin = 6.35  # 0.25 inch margin in mm

    print(f"Paper size: {paper_width}mm x {paper_height}mm")
    print(f"Original card size: {original_card_width}mm x {original_card_height}mm")

    layout = calculate_optimal_layout(original_card_width, original_card_height, paper_width, paper_height, margin, min_spacing=1)

    print(f"Layout: {layout}")

    c = canvas.Canvas(output_pdf, pagesize=(paper_width*mm, paper_height*mm))
    
    def place_image(x, y, width, height, rotated):
        print(f"Placing image at: x={x}mm, y={y}mm, width={width}mm, height={height}mm, rotated={rotated}")
        if rotated:
            c.saveState()
            c.translate((x+width)*mm, y*mm)
            c.rotate(90)
            c.drawImage(image_path, 0, 0, width=height*mm, height=width*mm, preserveAspectRatio=True)
            c.restoreState()
        else:
            c.drawImage(image_path, x*mm, y*mm, width=width*mm, height=height*mm, preserveAspectRatio=True)

    # Calculate total width and height of the layout
    total_width = layout['cols'] * layout['card_width'] + (layout['cols'] - 1) * layout['x_spacing']
    total_height = layout['rows'] * layout['card_height'] + (layout['rows'] - 1) * layout['y_spacing']

    # Calculate starting positions to center the layout
    x_start = (paper_width - total_width) / 2
    y_start = (paper_height - total_height) / 2

    print(f"Layout dimensions: {total_width}mm x {total_height}mm")
    print(f"Starting position: x={x_start}mm, y={y_start}mm")

    # Place images
    for row in range(layout['rows']):
        for col in range(layout['cols']):
            x = x_start + col * (layout['card_width'] + layout['x_spacing'])
            y = paper_height - (y_start + (row + 1) * layout['card_height'] + row * layout['y_spacing'])
            place_image(x, y, layout['card_width'], layout['card_height'], layout['rotated'])

    # Add guidelines
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.setDash(6, 3)
    
    # Vertical guidelines
    for i in range(layout['cols'] + 1):
        x = x_start + i * (layout['card_width'] + layout['x_spacing'])
        c.line(x*mm, 0, x*mm, margin*mm)  # Bottom
        c.line(x*mm, paper_height*mm, x*mm, (paper_height - margin)*mm)  # Top
    
    # Horizontal guidelines
    for i in range(layout['rows'] + 1):
        y = paper_height - (y_start + i * (layout['card_height'] + layout['y_spacing']))
        c.line(0, y*mm, margin*mm, y*mm)  # Left
        c.line(paper_width*mm, y*mm, (paper_width - margin)*mm, y*mm)  # Right
    
    # Save the PDF
    c.save()
    print(f"PDF saved: {output_pdf}")
    return layout['total']