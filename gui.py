# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 16:22:56 2024

@author: Windows
"""

import os
import pandas as pd
from tkinter import Tk, Canvas, filedialog, Toplevel
from PIL import Image, ImageTk

def select_folder():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    root.destroy()
    return folder_path

def on_mouse_click(event):
    global corners, canvas, img_id
    if len(corners) < 2:
        corners.append((event.x, event.y))
        canvas.create_oval(event.x - 2, event.y - 2, event.x + 2, event.y + 2, fill='red', outline='red')
        if len(corners) == 2:
            # Temporarily show the current selection in green
            canvas.create_rectangle(corners[0][0], corners[0][1], corners[1][0], corners[1][1], outline='green')

def on_key_press(event):
    global corners, bounding_boxes, current_file, root, canvas
    if event.keysym == 'Return' and len(corners) == 2:
        bounding_boxes.append([current_file, *corners[0], *corners[1]])
        # Draw the finalized bounding box in a different color (e.g., blue) and reset corners
        canvas.create_rectangle(corners[0][0], corners[0][1], corners[1][0], corners[1][1], outline='blue')
        corners = []
    elif event.keysym == 'Escape':
        root.destroy()  # Destroy the current window to move to the next image

def process_images(folder_path):
    global corners, bounding_boxes, current_file, root, canvas, img_id
    bounding_boxes = []
    corners = []
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    for image_file in image_files:
        root = Toplevel()  # Use Toplevel to properly manage window closure
        root.bind('<Escape>', on_key_press)
        root.bind('<Return>', on_key_press)
        root.bind("<Button-1>", on_mouse_click)
        current_file = os.path.join(folder_path, image_file)
        current_file = os.path.normpath(current_file)  # Normalize the file path
        img = Image.open(current_file)
        img_id = ImageTk.PhotoImage(img)

        canvas = Canvas(root, width=img.width, height=img.height)
        canvas.pack()
        canvas.create_image(0, 0, anchor='nw', image=img_id)

        corners = []  # Reset corners for the new image
        root.mainloop()  # Start the event loop for the current window

    return bounding_boxes



def save_to_csv(bounding_boxes):
    base_filename = 'bounding_boxes'
    filename = base_filename + '.csv'
    counter = 1
    
    # Check if the file exists and increment the counter until finding a unique filename
    while os.path.exists(filename):
        filename = f"{base_filename}_{counter}.csv"
        counter += 1
    
    # Save the DataFrame to the new unique filename
    df = pd.DataFrame(bounding_boxes, columns=['File Path', 'X1', 'Y1', 'X2', 'Y2'])
    df.to_csv(filename, index=False)
    print(f"Bounding boxes saved to '{filename}'.")


if __name__ == '__main__':
    folder_path = select_folder()
    if folder_path:
        bounding_boxes = process_images(folder_path)
        save_to_csv(bounding_boxes)

