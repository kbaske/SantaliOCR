import os
import sys
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pytesseract
import pypdfium2 as pdfium

# ==========================================
# DYNAMIC PATH RESOLUTION FOR ENGINE BUNDLING
# ==========================================
def resource_path(relative_path):
    """ Resolves path variables safely for standard runs and PyInstaller executables """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Point directly to the portable, bundled Tesseract binaries
TESSERACT_DIR = resource_path("Tesseract-OCR")
TESSERACT_PATH = os.path.join(TESSERACT_DIR, "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class SantaliOCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Santali (Ol Chiki) OCR")
        self.root.geometry("1050x760")
        self.root.configure(bg="#f4f6f9")

        # Document State Memory Buffer
        self.image_path = None
        self.is_pdf = False
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.active_view = None

        # --- Visual Banner Header ---
        self.header_frame = tk.Frame(root, bg="#2c3e50", pady=12)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        self.load_app_logo(self.header_frame)

        # Updated to use "Nirmala UI" to render header text natively
        title_label = tk.Label(
            self.header_frame, text="ᱥᱟᱱᱛᱟᱲᱤ (Ol Chiki) OCR",
            font=("Nirmala UI", 16, "bold"), bg="#2c3e50", fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=(10, 30))

        # --- Inline Navigation Links with Increased Text Size ---
        self.nav_buttons = {}
        nav_items = [
            ("Workspace", self.show_workspace_view),
            ("User Manual & Guide", self.show_guide_view),
            ("Developer & Contact", self.show_developer_view),
            ("Our Affiliates", self.show_affiliates_view)
        ]

        for label_text, command_func in nav_items:
            btn = tk.Button(
                self.header_frame, text=label_text, 
                font=("Arial", 12, "bold"),  
                bg="#2c3e50", fg="#bdc3c7", activebackground="#2c3e50", activeforeground="#ffffff",
                borderwidth=0, cursor="hand2", 
                padx=16,  
                command=command_func
            )
            btn.pack(side=tk.LEFT, anchor=tk.CENTER, pady=(2, 0))
            self.nav_buttons[label_text] = btn

        # --- Base Body Multi-Panel Container ---
        self.body_container = tk.Frame(root, bg="#f4f6f9")
        self.body_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Initialize and build the target workspaces
        self.show_workspace_view()
        self.verify_tesseract()

    def load_app_logo(self, parent_frame):
        logo_filename = resource_path("logo.png")
        if os.path.exists(logo_filename):
            try:
                logo_img = Image.open(logo_filename)
                logo_img = logo_img.resize((35, 35), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(parent_frame, image=self.logo_photo, bg="#2c3e50")
                logo_label.pack(side=tk.LEFT, padx=(20, 5))
                self.root.iconphoto(True, self.logo_photo)
            except Exception:
                pass

    def verify_tesseract(self):
        if not os.path.exists(TESSERACT_PATH):
            messagebox.showerror("Engine Configuration Alert", f"Internal Tesseract binary engine missing at:\n{TESSERACT_PATH}")

    def open_url(self, url):
        webbrowser.open_new_tab(url)

    def update_header_highlight(self, active_label):
        """ Dynamically updates active link button colors inside header block """
        for label_text, btn in self.nav_buttons.items():
            if label_text == active_label:
                btn.config(fg="#2ecc71") # Green highlight indicator
            else:
                btn.config(fg="#bdc3c7")

    def clear_body_container(self):
        """ Drops active window views before loading alternatives """
        for widget in self.body_container.winfo_children():
            widget.pack_forget()

    # ==========================================
    # CORE ROUTING VIEW 1: OCR WORKSPACE
    # ==========================================
    def show_workspace_view(self):
        self.clear_body_container()
        self.update_header_highlight("Workspace")

        # Workspace Main Master Panel Layout
        workspace_view = tk.Frame(self.body_container, bg="#f4f6f9")
        workspace_view.pack(fill=tk.BOTH, expand=True)

        # --- Dynamic Page Navigation Bar ---
        self.nav_frame = tk.Frame(workspace_view, bg="#e5e8e8", pady=6)
        if self.is_pdf:
            self.nav_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))
        
        self.btn_prev = tk.Button(self.nav_frame, text="⏮️ Previous Page", command=self.prev_page, font=("Arial", 10), bg="#ffffff", relief=tk.GROOVE)
        self.btn_prev.pack(side=tk.LEFT, padx=20)
        
        # Combined Label showing: [📄 filename.pdf]   |   Page X of Y
        display_text = "Page 0 of 0"
        if self.total_pages and self.image_path:
            file_name = os.path.basename(self.image_path)
            display_text = f"📄  {file_name}      |      Page {self.current_page + 1} of {self.total_pages}"
            
        # Updated to use "Nirmala UI" to preserve Ol Chiki symbols inside uploaded filenames safely
        self.page_label = tk.Label(self.nav_frame, text=display_text, font=("Nirmala UI", 11, "bold"), bg="#e5e8e8", fg="#2c3e50")
        self.page_label.pack(side=tk.LEFT, expand=True)
        
        self.btn_next = tk.Button(self.nav_frame, text="Next Page ⏭️", command=self.next_page, font=("Arial", 10), bg="#ffffff", relief=tk.GROOVE)
        self.btn_next.pack(side=tk.RIGHT, padx=20)
        
        self.btn_prev.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)

        # --- Bottom Control Buttons Tray ---
        btn_frame = tk.Frame(workspace_view, bg="#f4f6f9", pady=15)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_load = tk.Button(btn_frame, text="📁 1. Open Image/PDF", font=("Arial", 11, "bold"), bg="#3498db", fg="white", command=self.load_file, width=22, relief=tk.FLAT)
        self.btn_load.pack(side=tk.LEFT, padx=30)

        self.btn_ocr = tk.Button(btn_frame, text="⚡ 2. Run Text OCR", font=("Arial", 11, "bold"), bg="#2ecc71", fg="white", command=self.run_ocr, width=20, relief=tk.FLAT)
        self.btn_ocr.pack(side=tk.LEFT, padx=10)
        self.btn_ocr.config(state=tk.NORMAL if self.image_path else tk.DISABLED)

        self.btn_copy = tk.Button(btn_frame, text="📋 3. Copy Text", font=("Arial", 11, "bold"), bg="#9b59b6", fg="white", command=self.copy_text, width=20, relief=tk.FLAT)
        self.btn_copy.pack(side=tk.RIGHT, padx=30)

        # --- Main Split Workspace Frame ---
        self.main_frame = tk.Frame(workspace_view, bg="#f4f6f9")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Column Workspace: Image Viewer
        left_frame = tk.LabelFrame(self.main_frame, text=" Document Viewer ", font=("Arial", 10, "bold"), bg="#ffffff", fg="#2c3e50")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.image_canvas = tk.Label(left_frame, bg="#eaeded", fg="#7f8c8d")
        self.image_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if hasattr(self, 'current_display_img') and self.current_display_img:
            self.image_canvas.config(image=self.current_display_img, text="")
        else:
            self.image_canvas.config(text="No Document Opened Yet\n\nClick 'Open Image/PDF' below to upload files.", font=("Arial", 11))

        # Right Column Workspace: Unicode Text Output
        right_frame = tk.LabelFrame(self.main_frame, text=" Digitized Unicode Output ", font=("Arial", 10, "bold"), bg="#ffffff", fg="#2c3e50")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        current_text = self.text_output.get("1.0", tk.END) if hasattr(self, 'text_output') else ""
        self.text_output = tk.Text(right_frame, wrap=tk.WORD, font=("Nirmala UI", 13), bg="#fafbfc", fg="#2c3e50", height=15, relief=tk.SOLID, bd=1)
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if current_text and not current_text.startswith("[Page"):
            self.text_output.insert("1.0", current_text.strip())

    # ==========================================
    # CORE ROUTING VIEW 2: USER MANUAL GUIDE
    # ==========================================
    def show_guide_view(self):
        self.clear_body_container()
        self.update_header_highlight("User Manual & Guide")

        panel = tk.Frame(self.body_container, bg="#ffffff", padx=25, pady=20, highlightthickness=1, highlightbackground="#eaeded")
        panel.pack(fill=tk.BOTH, expand=True)

        guide_text = tk.Text(panel, wrap=tk.WORD, font=("Arial", 11), bg="#ffffff", fg="#2c3e50", relief=tk.FLAT)
        guide_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(panel, command=guide_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        guide_text.config(yscrollcommand=scrollbar.set)

        guide_text.insert(tk.END, "📚 SANTALI OCR SCANNER SYSTEM USER MANUAL\n", "doc_title")
        guide_text.insert(tk.END, "="*60 + "\n\n", "divider")
        guide_text.insert(tk.END, "1. Processing Standard Graphic Images\n", "section_title")
        guide_text.insert(tk.END, "• Switch to the 'Workspace' tab from the top header bar panel.\n• Click '1. Open Image/PDF' to import image segments (.png, .jpg, .jpeg, .tiff).\n• Click '2. Run Text OCR' to extract and convert text shapes to editable outputs.\n\n")
        guide_text.insert(tk.END, "2. Processing Multi-Page PDF Handbooks\n", "section_title")
        guide_text.insert(tk.END, "• Upload your digital handbook (.pdf) from your storage files.\n• A grey tracking tracker subheader row will reveal context layout configurations.\n• Use the 'Previous Page' and 'Next Page' links to scroll through books cleanly.\n• Execute OCR operations on pages matching your exact visual viewport layout selection.\n\n")
        guide_text.insert(tk.END, "3. Data Export Sync Routines\n", "section_title")
        guide_text.insert(tk.END, "• Extracted text characters map directly to standardized modern Ol Chiki Unicode layouts.\n• Use the purple '3. Copy Text' button to move contents directly into your system clipboard.")

        guide_text.tag_config("doc_title", font=("Arial", 15, "bold"), foreground="#2c3e50")
        guide_text.tag_config("divider", foreground="#bdc3c7")
        guide_text.tag_config("section_title", font=("Arial", 12, "bold"), foreground="#2980b9")
        guide_text.config(state=tk.DISABLED)

    # ==========================================
    # CORE ROUTING VIEW 3: DEVELOPER PROFILE
    # ==========================================
    def show_developer_view(self):
        self.clear_body_container()
        self.update_header_highlight("Developer & Contact")

        panel = tk.Frame(self.body_container, bg="#ffffff", padx=40, pady=30, highlightthickness=1, highlightbackground="#eaeded")
        panel.pack(fill=tk.BOTH, expand=True)

        card = tk.LabelFrame(panel, text=" Professional Engineer Matrix ", font=("Arial", 11, "bold"), bg="#ffffff", fg="#2c3e50", padx=25, pady=20)
        card.pack(fill=tk.X)

        dev_title = tk.Label(card, text="Santali OCR Core Project Lead Team", font=("Arial", 14, "bold"), bg="#ffffff", fg="#2c3e50")
        dev_title.pack(anchor=tk.W, pady=(0, 5))
        
        dev_desc = tk.Label(card, text="Specialized in compiling localization models, advanced optical text recognition arrays, and portable Windows automation frameworks.", font=("Arial", 10, "italic"), bg="#ffffff", fg="#7f8c8d")
        dev_desc.pack(anchor=tk.W, pady=(0, 20))

        info_frame = tk.Frame(card, bg="#ffffff")
        info_frame.pack(fill=tk.X)

        fields = [
            ("📧 Primary Project Email :", "professor@santals.in", "mailto:professor@santals.in"),
            ("🌐 Source Code Repository :", "https://github.com/kbaske/SantaliOCR", "https://github.com/kbaske/SantaliOCR"),
            ("💬 Project Developer :", "Karia Baskey", "https://facebook.com/karyabaske")
        ]

        for i, (label_txt, value_txt, destination_url) in enumerate(fields):
            lbl = tk.Label(info_frame, text=label_txt, font=("Arial", 10, "bold"), bg="#ffffff", fg="#34495e")
            lbl.grid(row=i, column=0, sticky=tk.W, pady=8, padx=(0, 15))

            link_btn = tk.Button(info_frame, text=value_txt, font=("Arial", 10), bg="#ffffff", fg="#2980b9", activebackground="#ffffff", activeforeground="#2471a3", borderwidth=0, cursor="hand2", command=lambda url=destination_url: self.open_url(url))
            link_btn.grid(row=i, column=1, sticky=tk.W, pady=8)

    # ==========================================
    # CORE ROUTING VIEW 4: CORPORATE AFFILIATES
    # ==========================================
    def show_affiliates_view(self):
        self.clear_body_container()
        self.update_header_highlight("Our Affiliates")

        panel = tk.Frame(self.body_container, bg="#ffffff", padx=40, pady=30, highlightthickness=1, highlightbackground="#eaeded")
        panel.pack(fill=tk.BOTH, expand=True)

        heading = tk.Label(panel, text="Institutional Affiliates & Research Partners", font=("Arial", 14, "bold"), bg="#ffffff", fg="#2c3e50")
        heading.pack(anchor=tk.W, pady=(0, 5))
        
        subheading = tk.Label(panel, text="This standalone system infrastructure was compiled with the help of the following technical collectives:", font=("Arial", 10), bg="#ffffff", fg="#7f8c8d")
        subheading.pack(anchor=tk.W, pady=(0, 25))

        affiliates_data = [
            {"name": "Santal Voices", "role": "Chief Editor", "web": "https://santalvoices.org"},
            {"name": "Wikimedians of Santali Language User Group", "role": "Santali Language User Group", "web": "https://w.wiki/6pz8"},
            {"name": "Our Wiki Clubs", "role": "Region-based community clubs", "web": "https://w.wiki/SpWN"}
        ]

        for entity in affiliates_data:
            frame_box = tk.Frame(panel, bg="#fcfcfc", highlightbackground="#eaeded", highlightthickness=1, bd=0, pady=12, padx=15)
            frame_box.pack(fill=tk.X, pady=6)

            title_lbl = tk.Label(frame_box, text=entity["name"], font=("Arial", 11, "bold"), bg="#fcfcfc", fg="#2c3e50")
            title_lbl.pack(side=tk.LEFT, anchor=tk.W)

            desc_lbl = tk.Label(frame_box, text=f"({entity['role']})", font=("Arial", 10), bg="#fcfcfc", fg="#95a5a6")
            desc_lbl.pack(side=tk.LEFT, anchor=tk.W, padx=10)

            url_btn = tk.Button(frame_box, text="Open Portal 🌐", font=("Arial", 9, "bold"), bg="#eaeded", fg="#34495e", activebackground="#d5dbdb", relief=tk.FLAT, cursor="hand2", padx=10, command=lambda url=entity["web"]: self.open_url(url))
            url_btn.pack(side=tk.RIGHT)

    # ==========================================
    # WORKSPACE DATA STREAM INPUT PROCESSING
    # ==========================================
    def load_file(self):
        file_types = [
            ("Supported Files", "*.jpg *.jpeg *.png *.bmp *.tiff *.pdf"),
            ("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("PDF Documents", "*.pdf")
        ]
        file_path = filedialog.askopenfilename(title="Select Document", filetypes=file_types)
        
        if not file_path:
            return

        self.image_path = file_path
        if hasattr(self, 'text_output'):
            self.text_output.delete("1.0", tk.END)
        
        if file_path.lower().endswith('.pdf'):
            self.is_pdf = True
            try:
                self.pdf_document = pdfium.PdfDocument(file_path)
                self.total_pages = len(self.pdf_document)
                self.current_page = 0
                
                self.show_workspace_view()
                self.update_page_view()
            except Exception as e:
                messagebox.showerror("PDF Rendering Error", f"Could not render PDF document:\n{str(e)}")
        else:
            self.is_pdf = False
            self.pdf_document = None
            self.total_pages = 0
            self.current_page = 0
            
            img = Image.open(file_path)
            self.show_workspace_view()
            self.display_image_on_canvas(img)

    def update_page_view(self):
        if not self.pdf_document:
            return
        
        page = self.pdf_document[self.current_page]
        bitmap = page.render(scale=2)  
        pil_img = bitmap.to_pil()
        
        self.display_image_on_canvas(pil_img)
        
        file_name = os.path.basename(self.image_path)
        self.page_label.config(text=f"📄  {file_name}      |      Page {self.current_page + 1} of {self.total_pages}")
        
        self.text_output.delete("1.0", tk.END)
        self.text_output.insert(tk.END, f"[Page {self.current_page + 1} loaded. Press 'Run Text OCR' to execute analysis.]")
        self.btn_prev.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)

    def display_image_on_canvas(self, pil_img):
        preview_img = pil_img.copy()
        preview_img.thumbnail((420, 480))
        self.current_display_img = ImageTk.PhotoImage(preview_img)
        self.image_canvas.config(image=self.current_display_img, text="")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_view()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page_view()

    def get_current_image(self):
        if self.is_pdf:
            page = self.pdf_document[self.current_page]
            return page.render(scale=3).to_pil() 
        return Image.open(self.image_path)

    def run_ocr(self):
        self.text_output.delete("1.0", tk.END)
        self.text_output.insert(tk.END, "Running Tesseract character translation... Please wait...\n")
        self.root.update_idletasks()

        try:
            custom_config = r'--oem 3 --psm 3 -l sat'
            img = self.get_current_image()
            extracted_text = pytesseract.image_to_string(img, config=custom_config)

            self.text_output.delete("1.0", tk.END)
            if extracted_text.strip():
                self.text_output.insert(tk.END, extracted_text)
            else:
                self.text_output.insert(tk.END, "[OCR finished processing. No clean text shapes were discovered.]")
        except Exception as e:
            self.text_output.delete("1.0", tk.END)
            messagebox.showerror("OCR Calculation Error", f"Character parsing execution dropped:\n{str(e)}")

    def copy_text(self):
        text = self.text_output.get("1.0", tk.END).strip()
        if text and not text.startswith("["):
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Sync Success", "Santali text string copied to system clipboard layout!")
        else:
            messagebox.showwarning("Copy Blocked", "No printable character logs found to copy.")


if __name__ == "__main__":
    root = tk.Tk()
    app = SantaliOCRApp(root)
    root.mainloop()