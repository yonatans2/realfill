import os
import pandas as pd
from tkinter import Tk, Canvas, filedialog, Toplevel
from PIL import Image, ImageTk, ImageDraw


# Global variable to hold references to the cropped ImageTk.PhotoImage objects
cropped_images = []

def select_folder():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    root.destroy()
    return folder_path

def create_empty_image(size):
    return Image.new("RGB", size, "white")

def on_mouse_click(event):
    global corners, canvas, img_id, empty_img_id, mode, cropped_img_id, cropped_images
    if mode == "select":
        if len(corners) < 2:
            corners.append((event.x, event.y))
            canvas.create_oval(event.x - 2, event.y - 2, event.x + 2, event.y + 2, fill='red', outline='red')
            if len(corners) == 2:
                canvas.create_rectangle(corners[0][0], corners[0][1], corners[1][0], corners[1][1], outline='green')
                crop_rectangle = (corners[0][0], corners[0][1], corners[1][0], corners[1][1])
                cropped_img = img.crop(crop_rectangle)
                cropped_img_id = ImageTk.PhotoImage(cropped_img)  # Prepare for placing
                mode = "place"  # Change mode
    elif mode == "place":
        # Add the cropped image to the list to ensure it stays on the canvas
        cropped_images.append((cropped_img_id, event.x, event.y))
        empty_canvas.create_image(event.x, event.y, anchor="nw", image=cropped_img_id)
        # Save the placement along with bounding box coordinates
        bounding_boxes.append([current_file, *corners[0], *corners[1], event.x, event.y])
        corners = []  # Reset corners
        mode = "select"  # Switch back to select mode
        
def on_key_press(event):
    global corners, bounding_boxes, current_file, root, canvas, mode
    if event.keysym == 'Return' and mode == "select" and len(corners) == 2:
        bounding_boxes.append([current_file, *corners[0], *corners[1]])
        corners = []
        mode = "place"  # Change mode to allow placing the cropped image
    elif event.keysym == 'Escape':
        root.destroy()  # Destroy the current window to move to the next image

def process_images(folder_path):
    global corners, bounding_boxes, current_file, root, canvas, img_id, empty_canvas, empty_img_id, img, mode
    bounding_boxes = []
    corners = []
    mode = "select"  # Start in "select" mode for drawing bounding boxes
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    for image_file in image_files:
        root = Toplevel()
        root.bind('<Escape>', on_key_press)
        root.bind('<Return>', on_key_press)
        root.bind("<Button-1>", on_mouse_click)
        current_file = os.path.join(folder_path, image_file)
        current_file = os.path.normpath(current_file)
        img = Image.open(current_file)
        img_id = ImageTk.PhotoImage(img)

        # Original image canvas
        canvas = Canvas(root, width=img.width, height=img.height)
        canvas.grid(row=0, column=0)
        canvas.create_image(0, 0, anchor='nw', image=img_id)

        # Empty image canvas
        empty_img = create_empty_image(img.size)
        empty_img_id = ImageTk.PhotoImage(empty_img)
        empty_canvas = Canvas(root, width=img.width, height=img.height)
        empty_canvas.grid(row=0, column=1)
        empty_canvas.create_image(0, 0, anchor='nw', image=empty_img_id)

        corners = []  # Reset corners for the new image
        root.mainloop()

    return bounding_boxes

# Adjust the save_to_csv function to include the placement of the cropped images
def save_to_csv(bounding_boxes):
    base_filename = 'bounding_boxes'
    filename = base_filename + '.csv'
    counter = 1
    
    while os.path.exists(filename):
        filename = f"{base_filename}_{counter}.csv"
        counter += 1
    
    df = pd.DataFrame(bounding_boxes, columns=['File Path', 'X1', 'Y1', 'X2', 'Y2', 'Placement X', 'Placement Y'])
    df.to_csv(filename, index=False)
    print(f"Bounding boxes saved to '{filename}'.")


if __name__ == '__main__':
    folder_path = select_folder()
    if folder_path:
        bounding_boxes = process_images(folder_path)
        save_to_csv(bounding_boxes)
