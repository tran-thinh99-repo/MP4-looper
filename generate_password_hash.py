import hashlib
import tkinter as tk
from tkinter import ttk, messagebox

def generate_hash(password):
    """Generate a hash for MP4 Looper authentication"""
    salt = "mp4_looper_salt"
    combined = f"{password}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def copy_to_clipboard(text, root):
    root.clipboard_clear()
    root.clipboard_append(text)
    messagebox.showinfo("Copied", "Hash copied to clipboard!")

def create_ui():
    root = tk.Tk()
    root.title("MP4 Looper Password Hash Generator")
    root.geometry("600x300")
    root.resizable(True, True)
    
    # Configure style
    style = ttk.Style()
    style.configure("TLabel", font=("Segoe UI", 11))
    style.configure("TButton", font=("Segoe UI", 10))
    style.configure("TEntry", font=("Segoe UI", 10))
    
    # Main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="MP4 Looper Password Hash Generator", font=("Segoe UI", 14, "bold"))
    title_label.pack(pady=(0, 15))
    
    # Description
    desc_label = ttk.Label(main_frame, text="Generate password hashes for the MP4 Looper authentication system.")
    desc_label.pack(pady=(0, 5))
    
    salt_info = ttk.Label(main_frame, text="Using salt: mp4_looper_salt")
    salt_info.pack(pady=(0, 15))
    
    # Password entry frame
    password_frame = ttk.Frame(main_frame)
    password_frame.pack(fill=tk.X, pady=5)
    
    password_label = ttk.Label(password_frame, text="Password:")
    password_label.pack(side=tk.LEFT, padx=(0, 10))
    
    password_var = tk.StringVar()
    password_entry = ttk.Entry(password_frame, textvariable=password_var, width=40)
    password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    
    generate_button = ttk.Button(
        password_frame, 
        text="Generate Hash", 
        command=lambda: update_hash(password_var.get())
    )
    generate_button.pack(side=tk.LEFT)
    
    # Hash output frame
    hash_frame = ttk.Frame(main_frame)
    hash_frame.pack(fill=tk.X, pady=15)
    
    hash_label = ttk.Label(hash_frame, text="Generated Hash:")
    hash_label.pack(side=tk.LEFT, padx=(0, 10))
    
    hash_var = tk.StringVar()
    hash_entry = ttk.Entry(hash_frame, textvariable=hash_var, width=40, state="readonly")
    hash_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    
    copy_button = ttk.Button(
        hash_frame, 
        text="Copy to Clipboard",
        command=lambda: copy_to_clipboard(hash_var.get(), root)
    )
    copy_button.pack(side=tk.LEFT)
    
    # Status bar
    status_var = tk.StringVar()
    status_bar = ttk.Label(main_frame, textvariable=status_var, font=("Segoe UI", 10, "italic"))
    status_bar.pack(pady=(15, 0))
    
    # Function to update hash
    def update_hash(password):
        if not password:
            status_var.set("Please enter a password")
            hash_var.set("")
            return
            
        hash_value = generate_hash(password)
        hash_var.set(hash_value)
        status_var.set(f"Hash generated for password: {password}")
    
    # Bind Enter key to generate hash
    password_entry.bind("<Return>", lambda event: update_hash(password_var.get()))
    
    # Focus password entry
    password_entry.focus()
    
    return root

if __name__ == "__main__":
    root = create_ui()
    root.mainloop()