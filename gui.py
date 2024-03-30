# -*- coding: utf-8 -*-
"""
Created on Sat Mar 30 09:20:14 2024

@author: Windows
"""
import sys
import os
from PIL import Image
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QFileDialog
from PyQt5.QtCore import Qt
import pandas as pd
import matplotlib.patches as patches

class InteractiveCanvas(FigureCanvas):
    def __init__(self, parent=None, dpi=100):
        self.fig = Figure(dpi=dpi)
        self.axes = self.fig.add_subplot(121)
        self.axes_target = self.fig.add_subplot(122)
        
        self.axes_target.axis('off')  # Turn off axes for the target subplot
        self.axes_target.set_aspect('equal')  # Set aspect ratio to be equal to avoid stretching
        super().__init__(self.fig)
        self.setParent(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.mainWindow = parent

        self.images_folder = ''
        self.images = []
        self.current_img_idx = -1
        self.rect_start = None
        self.rect_end = None
        self.cropped_img = None  # To store the cropped image temporarily
        self.target_img = np.ones((512, 512, 3), dtype=np.uint8) * 255  # White target image
        self.axes_target.imshow(self.target_img, extent=[0, 512, 0, 512], aspect='equal')
        self.df = pd.DataFrame(columns=['Source Path', 'Src_X1', 'Src_Y1', 'Src_X2', 'Src_Y2', 'Trg_X1', 'Trg_Y1'])
        self.update_target_display()
        self.load_images()

        self.mpl_connect('button_press_event', self.on_click)
        self.mpl_connect('key_press_event', self.on_key_press)

    def load_images(self):
        self.images_folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.images_folder:
            self.images = [os.path.join(self.images_folder, f) for f in os.listdir(self.images_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            self.adjust_figure_size()
            self.next_image()
    
    def adjust_figure_size(self):
        max_width, max_height = get_max_image_size(self.images_folder)
        self.fig.set_size_inches((max_width + 512) / self.fig.dpi, max(max_height, 512) / self.fig.dpi, forward=True)
        self.draw()

    def next_image(self):
        if self.images:
            self.current_img_idx = (self.current_img_idx + 1) % len(self.images)
            image_path = self.images[self.current_img_idx]
            img = Image.open(image_path)
            img_arr = np.array(img)
            self.axes.clear()
            self.axes.imshow(img_arr)
            self.axes.axis('off')
            self.axes.set_title("Source Image")
            self.draw()
            self.rect_start=None
            self.rect_end=None

    def update_target_display(self):
        # Reset the target image to a blank state if needed
        self.target_img = np.ones((512, 512, 3), dtype=np.uint8) * 255  # White target image
        
        # Iterate through the DataFrame to place each cropped image
        for idx, row in self.df.iterrows():
            src_path = row['Source Path']
            src_img = Image.open(src_path)
            src_coords = (row['Src_X1'], row['Src_Y1'], row['Src_X2'], row['Src_Y2'])
            trg_coords = (row['Trg_X1'], row['Trg_Y1'])
            
            # Crop the source image
            cropped_img = np.array(src_img.crop(src_coords))
            
            # Calculate target position and dimensions
            trg_x1, trg_y1 = trg_coords
            height, width, _ = cropped_img.shape
            
            # Place cropped image onto target image, ensuring bounds checking
            for i in range(height):
                for j in range(width):
                    if 0 <= trg_y1+i < 512 and 0 <= trg_x1+j < 512:  # Ensure within target bounds
                        self.target_img[trg_y1+i, trg_x1+j, :] = cropped_img[i, j, :]
        
        # Display the updated target image
        self.axes_target.clear()
        self.axes_target.imshow(self.target_img, aspect='equal', extent=[0, 512, 0, 512])
        self.axes_target.axis('off')
        
        # Optionally, add a 1-pixel wide black box around the target image as requested
        rect = matplotlib.patches.Rectangle((1, 1), 512 , 512 , linewidth=1, edgecolor='black', facecolor='none')
        self.axes_target.add_patch(rect)
        
        self.axes_target.set_title("Target Image")  # Add title if needed
        self.draw()
        
   
    def on_click(self, event):
        #print (event.inaxes,event.xdata,event.ydata)
        if event.inaxes == self.axes and self.rect_start is None:
            self.rect_start = (int(event.xdata), int(event.ydata))
        elif event.inaxes == self.axes and self.rect_start is not None:
            x0, y0 = self.rect_start
            x1, y1 = (int(event.xdata), int(event.ydata))
            width = x1 - x0
            height = y1 - y0
            self.rect_end = x1,y1

            rect = matplotlib.patches.Rectangle(self.rect_start, width, height, linewidth=1, edgecolor='magenta', facecolor='none')
            self.axes.add_patch(rect)
            self.draw()

            # Cropping and storing the selected part of the image
            image_path = self.images[self.current_img_idx]
            img = Image.open(image_path)
            self.cropped_img = img.crop((x0, y0, event.xdata, event.ydata))
 
        if event.inaxes == self.axes_target and self.cropped_img is not None:
            trg_x, trg_y = (int(event.xdata), 512-int(event.ydata))
            src_path = self.images[self.current_img_idx]
            x0, x1 = min( self.rect_start[0], self.rect_end[0]), max ( self.rect_start[0], self.rect_end[0])
            y0, y1 = min( self.rect_start[1], self.rect_end[1]), max ( self.rect_start[1], self.rect_end[1])
            new_index = len(self.df)
            self.df.loc[new_index] = [src_path, x0, y0, x1, y1, trg_x, trg_y]
            self.update_target_display()
            self.rect_start = None
            self.cropped_img = None
            
    def on_key_press(self, event):
        if event.key == ' ':
            self.next_image()
        elif event.key == 'escape':
            save_dataframe_to_csv(self.df, 'target_image')
            save_image_to_png(self.target_img, 'target_image')
            self.mainWindow.close()

class ApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Image Cropping and Placing")

        widget = QWidget(self)
        self.setCentralWidget(widget)

        layout = QVBoxLayout(widget)
        canvas = InteractiveCanvas(self)
        layout.addWidget(canvas)

def get_max_image_size(images_folder):
    max_width, max_height = 0, 0
    for img_name in os.listdir(images_folder):
        if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(images_folder, img_name)
            with Image.open(img_path) as img:
                width, height = img.size
                max_width, max_height = max(max_width, width), max(max_height, height)
    return max_width, max_height

def save_dataframe_to_csv(df, base_filename):
    """
    Saves a DataFrame to a CSV file. If the target file exists, appends a numeric suffix to ensure uniqueness.

    :param df: pandas DataFrame to be saved.
    :param base_filename: String base filename without extension or numeric suffix.
    """
    filename = f'{base_filename}.csv'
    counter = 1
    # Check if the file exists and increment the counter until finding a unique filename
    while os.path.exists(filename):
        filename = f'{base_filename}_{counter}.csv'
        counter += 1
    # Save the DataFrame to the new unique filename
    df.to_csv(filename, index=False)
    print(f"DataFrame saved to '{filename}'.")

def save_image_to_png(image_array, base_filename):
    """
    Saves an image array to a PNG file. If the target file exists, appends a numeric suffix to ensure uniqueness.

    :param image_array: Numpy array representing the image to be saved.
    :param base_filename: String base filename without extension or numeric suffix.
    """
    filename = f'{base_filename}.png'
    counter = 1
    # Check if the file exists and increment the counter until finding a unique filename
    while os.path.exists(filename):
        filename = f'{base_filename}_{counter}.png'
        counter += 1
    # Save the image to the new unique filename
    img = Image.fromarray(image_array)
    img.save(filename)
    print(f"Image saved to '{filename}'.")    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ApplicationWindow()
    main_window.show()
    sys.exit(app.exec_())
