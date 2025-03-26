import tkinter as tk
from PIL import Image, ImageTk

# Create the main window
meki = tk.Tk()
meki.title("Csöves BigMac!")
meki.state("zoomed")

# Create a red button
red_button = tk.Button(meki, text="Click Me", bg="red")
red_button.pack(pady=20)  # Add some vertical padding

# Function to handle button click
# Function to handle button click
def on_button_click():
    message_label.config(text="Csöves Munkásautó!", font=("Helvetica", 24))  # Change 24 to your desired font size
    image_label.pack(pady=10)  # Show the image when the button is clicked

# Load the image using Pillow
try:
    image = Image.open("munkasautó.png")  # Open the image file
    munkasauto_image = ImageTk.PhotoImage(image)  # Convert to Tkinter-compatible format
except Exception as e:
    print(f"Error loading image: {e}")
    munkasauto_image = None

# Create a label to display the image
image_label = tk.Label(meki, image=munkasauto_image)

# Create a label to display messages
message_label = tk.Label(meki, text="")
message_label.pack(pady=10)  # Add some vertical padding

# Bind the button click to the function
red_button.config(command=on_button_click)

# Set the window size
meki.geometry("300x200")  # Width x Height

# Start the application
meki.mainloop()