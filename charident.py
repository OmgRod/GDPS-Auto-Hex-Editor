import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

def select_file():
    file_path = filedialog.askopenfilename(
        title="Select a File",
        filetypes=[("All Files", "*.*")]
    )
    if file_path:
        process_file(file_path)

def process_file(file_path):
    encodings = ['utf-8', 'latin1', 'ISO-8859-1']
    
    content = ""
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as file:
                content = file.read()
            break  # Break the loop if successful
        except UnicodeDecodeError:
            continue  # Try the next encoding if there's a decode error
    else:
        messagebox.showerror("Error", "Unable to read the file with available encodings.")
        return

    # Encode non-printable ASCII and non-ASCII characters
    encoded_content = ''.join(
        f'\\u{ord(char):04x}' if (ord(char) > 127 or not (32 <= ord(char) <= 126)) else char
        for char in content
    )
    
    save_file(encoded_content)

def save_file(encoded_content):
    save_path = filedialog.asksaveasfilename(
        title="Save File",
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if save_path:
        try:
            with open(save_path, 'w', encoding='utf-8') as file:
                file.write(encoded_content)
            messagebox.showinfo("Success", "File has been saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    select_file()

if __name__ == "__main__":
    main()