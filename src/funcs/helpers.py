import os
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

def extract_gga_gsv_lines(file_path, output_path, gga=False, gsv=False):
    # Get the original file name without extension
    base_name = os.path.basename(file_path)
    file_name, file_extension = os.path.splitext(base_name)

    # Determine mode for the output file name
    mode = ""
    if gga and gsv:
        mode = "gga_gsv"
    elif gga:
        mode = "gga"
    elif gsv:
        mode = "gsv"

    # Add timestamp to the output file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_path, f"{mode}_{file_name}_{timestamp}.txt")

    try:
        # Open the input file and output file
        with open(file_path, 'r') as infile, open(output_file, 'w') as outfile:
            # Read the file line by line
            for line in infile:
                # Check if the line starts with "$GNGGA" or any "$**GSV" pattern
                if gga and line.startswith("$GNGGA"):
                    outfile.write(line)
                if gsv and "$G" in line[:5] and "GSV" in line:
                    outfile.write(line)

        messagebox.showinfo("Success", f"GNGGA and GSV lines extracted to {output_file}")
    except FileNotFoundError:
        messagebox.showerror("Error", f"The file {file_path} does not exist.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def create_gui():
    def browse_file():
        file = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file:
            file_path_var.set(file)

    def browse_folder():
        folder = filedialog.askdirectory()
        if folder:
            output_path_var.set(folder)

    def extract():
        file_path = file_path_var.get()
        output_path = output_path_var.get()
        extract_gga = gga_var.get()
        extract_gsv = gsv_var.get()

        if not file_path:
            messagebox.showwarning("Warning", "Please select a file.")
            return

        if not output_path:
            messagebox.showwarning("Warning", "Please select an output folder.")
            return

        if not (extract_gga or extract_gsv):
            messagebox.showwarning("Warning", "Please select at least one extraction option (GGA or GSV).")
            return

        extract_gga_gsv_lines(file_path, output_path, gga=extract_gga, gsv=extract_gsv)

    # Main window
    root = tk.Tk()
    root.title("Helper - GGA and GSV Extractor")

    # File selection
    tk.Label(root, text="Select File:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    file_path_var = tk.StringVar()
    tk.Entry(root, textvariable=file_path_var, width=50).grid(row=0, column=1, padx=10, pady=5)
    tk.Button(root, text="Browse", command=browse_file).grid(row=0, column=2, padx=10, pady=5)

    # Output folder selection
    tk.Label(root, text="Output Folder:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    output_path_var = tk.StringVar()
    tk.Entry(root, textvariable=output_path_var, width=50).grid(row=1, column=1, padx=10, pady=5)
    tk.Button(root, text="Browse", command=browse_folder).grid(row=1, column=2, padx=10, pady=5)

    # Extraction options
    gga_var = tk.BooleanVar()
    gsv_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Extract GGA", variable=gga_var).grid(row=2, column=0, padx=10, pady=5, sticky="w")
    tk.Checkbutton(root, text="Extract GSV", variable=gsv_var).grid(row=2, column=1, padx=10, pady=5, sticky="w")

    # Extract button
    tk.Button(root, text="Extract", command=extract, width=15).grid(row=3, column=0, columnspan=3, pady=20)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
