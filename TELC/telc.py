import os
import random
import tkinter as tk
from tkinter import ttk, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk

class TELCQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TELC Sınav Pratik Uygulaması")
        self.root.geometry("1450x880")
        self.root.configure(bg="#0f172a")

        self.base_folder = r"D:\TELC"
        self.selected_subfolder = ""
        
        self.all_pdf_files = []
        self.remaining_pdf_files = []
        self.current_pdf_path = None

        self.images_left = []
        self.images_right = []
        self.images_single = []

        # LV3 Özel Durum Değişkenleri
        self.lv3_doc = None
        self.lv3_current_left_page = 0

        self.apply_styles()
        self.setup_ui()
        self.load_subfolders()

    def apply_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TCombobox", fieldbackground="#1e293b", background="#334155", foreground="#ffffff", borderwidth=0)
        style.map("TCombobox", fieldbackground=[('readonly', '#1e293b')], foreground=[('readonly', '#ffffff')])
        style.configure("TPanedwindow", background="#0f172a")

    def setup_ui(self):
        # --- ÜST PANEL ---
        top_frame = tk.Frame(self.root, bg="#020617")
        top_frame.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            top_frame, 
            text="TELC SINAV UYGULAMASI", 
            fg="#f8fafc", 
            bg="#020617", 
            font=("Helvetica", 13, "bold")
        ).pack(side=tk.LEFT, padx=15, pady=12)

        tk.Label(
            top_frame, 
            text="Sınav Bölümü:", 
            fg="#94a3b8", 
            bg="#020617", 
            font=("Helvetica", 10, "bold")
        ).pack(side=tk.LEFT, padx=(10, 5))

        self.combo_subfolder = ttk.Combobox(top_frame, state="readonly", width=10, font=("Helvetica", 10, "bold"))
        self.combo_subfolder.pack(side=tk.LEFT, padx=5)
        self.combo_subfolder.bind("<<ComboboxSelected>>", self.on_folder_changed)

        btn_random = tk.Button(
            top_frame, 
            text="🎲 Rastgele Test Getir", 
            bg="#10b981", 
            fg="white", 
            activebackground="#059669",
            activeforeground="white",
            font=("Helvetica", 10, "bold"),
            command=self.load_random_pdf,
            relief=tk.FLAT,
            padx=12,
            pady=3,
            cursor="hand2"
        )
        btn_random.pack(side=tk.LEFT, padx=15)

        self.lbl_current_file = tk.Label(
            top_frame, 
            text="Lütfen bir bölüm seçin...", 
            fg="#cbd5e1", 
            bg="#020617", 
            font=("Helvetica", 10, "bold")
        )
        self.lbl_current_file.pack(side=tk.LEFT, padx=10)

        # --- ANA İÇERİK ALANI ---
        self.container = tk.Frame(self.root, bg="#0f172a")
        self.container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.setup_layouts()

    def setup_layouts(self):
        # 1. TEK PANELLİ DÜZEN (HV1, HV2 vb. için)
        self.frame_single = tk.Frame(self.container, bg="#0f172a")
        
        frame_single_inner = tk.LabelFrame(
            self.frame_single, text=" Soru / Doküman ", font=("Helvetica", 10, "bold"), 
            bg="#1e293b", fg="#94a3b8", bd=1, relief=tk.SOLID
        )
        frame_single_inner.pack(fill=tk.BOTH, expand=True)

        self.canvas_single = tk.Canvas(frame_single_inner, bg="#0f172a", highlightthickness=0)
        scroll_y_single = ttk.Scrollbar(frame_single_inner, orient=tk.VERTICAL, command=self.canvas_single.yview)
        scroll_x_single = ttk.Scrollbar(frame_single_inner, orient=tk.HORIZONTAL, command=self.canvas_single.xview)
        self.canvas_single.configure(yscrollcommand=scroll_y_single.set, xscrollcommand=scroll_x_single.set)

        scroll_y_single.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x_single.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas_single.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 2. ÇİFT PANELLİ DÜZEN (LV1, LV2, LV3 vb. için)
        self.frame_split = tk.Frame(self.container, bg="#0f172a")
        self.pane_split = ttk.PanedWindow(self.frame_split, orient=tk.HORIZONTAL)
        self.pane_split.pack(fill=tk.BOTH, expand=True)

        # Sol Panel
        self.left_box = tk.LabelFrame(
            self.pane_split, text=" Sol Sayfa (Soru / Metin) ", font=("Helvetica", 10, "bold"), 
            bg="#1e293b", fg="#94a3b8", bd=1, relief=tk.SOLID
        )
        self.pane_split.add(self.left_box, weight=1)

        # LV3 İnce Sayfa Değiştirme Barı (Sol Panel Altında)
        self.lv3_nav_bar = tk.Frame(self.left_box, bg="#334155", height=30)
        
        self.btn_lv3_prev = tk.Button(
            self.lv3_nav_bar, text="◀ Sayfa 1", font=("Helvetica", 8, "bold"), bg="#2563eb", fg="white",
            activebackground="#1d4ed8", activeforeground="white",
            command=lambda: self.switch_lv3_page(0), cursor="hand2", relief=tk.FLAT, padx=10, pady=2
        )
        self.btn_lv3_prev.pack(side=tk.LEFT, padx=8, pady=2)

        self.lbl_lv3_page = tk.Label(self.lv3_nav_bar, text="Sayfa: 1 / 2", font=("Helvetica", 9, "bold"), bg="#334155", fg="#f8fafc")
        self.lbl_lv3_page.pack(side=tk.LEFT, expand=True)

        self.btn_lv3_next = tk.Button(
            self.lv3_nav_bar, text="Sayfa 2 ▶", font=("Helvetica", 8, "bold"), bg="#2563eb", fg="white",
            activebackground="#1d4ed8", activeforeground="white",
            command=lambda: self.switch_lv3_page(1), cursor="hand2", relief=tk.FLAT, padx=10, pady=2
        )
        self.btn_lv3_next.pack(side=tk.RIGHT, padx=8, pady=2)

        self.canvas_left = tk.Canvas(self.left_box, bg="#0f172a", highlightthickness=0)
        scroll_y_left = ttk.Scrollbar(self.left_box, orient=tk.VERTICAL, command=self.canvas_left.yview)
        scroll_x_left = ttk.Scrollbar(self.left_box, orient=tk.HORIZONTAL, command=self.canvas_left.xview)
        self.canvas_left.configure(yscrollcommand=scroll_y_left.set, xscrollcommand=scroll_x_left.set)

        scroll_y_left.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x_left.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Sağ Panel
        self.right_box = tk.LabelFrame(
            self.pane_split, text=" Sağ Sayfa (Seçenekler / Cevaplar) ", font=("Helvetica", 10, "bold"), 
            bg="#1e293b", fg="#94a3b8", bd=1, relief=tk.SOLID
        )
        self.pane_split.add(self.right_box, weight=1)

        self.canvas_right = tk.Canvas(self.right_box, bg="#0f172a", highlightthickness=0)
        scroll_y_right = ttk.Scrollbar(self.right_box, orient=tk.VERTICAL, command=self.canvas_right.yview)
        scroll_x_right = ttk.Scrollbar(self.right_box, orient=tk.HORIZONTAL, command=self.canvas_right.xview)
        self.canvas_right.configure(yscrollcommand=scroll_y_right.set, xscrollcommand=scroll_x_right.set)

        scroll_y_right.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x_right.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Mouse Wheel
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        widget = event.widget
        if isinstance(widget, tk.Canvas):
            widget.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_subfolders(self):
        if not os.path.exists(self.base_folder):
            os.makedirs(self.base_folder)

        subfolders = [d for d in os.listdir(self.base_folder) if os.path.isdir(os.path.join(self.base_folder, d))]
        subfolders.sort()

        if subfolders:
            self.combo_subfolder['values'] = subfolders
            self.combo_subfolder.current(0)
            self.on_folder_changed(None)
        else:
            self.lbl_current_file.config(text=f"'{self.base_folder}' klasöründe hiç bölüm (HV1, LV1 vb.) bulunamadı!")

    def on_folder_changed(self, event):
        self.selected_subfolder = self.combo_subfolder.get()
        folder_path = os.path.join(self.base_folder, self.selected_subfolder)
        
        files = os.listdir(folder_path)
        self.all_pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        self.remaining_pdf_files = list(self.all_pdf_files)
        
        self.current_pdf_path = None
        self.load_random_pdf()

    def load_random_pdf(self):
        if not self.all_pdf_files:
            self.lbl_current_file.config(text=f"{self.selected_subfolder} klasöründe PDF bulunamadı!")
            self.hide_all_layouts()
            return

        if not self.remaining_pdf_files:
            self.remaining_pdf_files = list(self.all_pdf_files)
            messagebox.showinfo("Bölüm Tamamlandı!", f"'{self.selected_subfolder}' bölümündeki tüm testleri tamamladınız. Havuz sıfırlandı.")

        selected_file = random.choice(self.remaining_pdf_files)
        self.remaining_pdf_files.remove(selected_file)

        self.current_pdf_path = selected_file
        pdf_full_path = os.path.join(self.base_folder, self.selected_subfolder, selected_file)

        self.display_pdf(pdf_full_path)

        total_count = len(self.all_pdf_files)
        remaining_count = len(self.remaining_pdf_files)
        self.lbl_current_file.config(
            text=f"Bölüm: {self.selected_subfolder} | Dosya: {selected_file} | (Kalan: {remaining_count + 1}/{total_count})"
        )

    def hide_all_layouts(self):
        self.frame_single.pack_forget()
        self.frame_split.pack_forget()
        self.lv3_nav_bar.pack_forget()

    def render_page_fit(self, doc, page_num, canvas):
        """Sayfayı Canvas genişliğine tam sığacak ve okunabilir yapacak şekilde işler"""
        if page_num >= len(doc):
            return None
            
        canvas.update_idletasks()
        target_w = canvas.winfo_width() - 20
        target_h = canvas.winfo_height() - 20

        if target_w <= 10 or target_h <= 10:
            target_w, target_h = 650, 800

        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Sayfanın genişliğe göre orantılı boyutlandırılması
        ratio = target_w / float(img.size[0])
        new_w = int(float(img.size[0]) * ratio)
        new_h = int(float(img.size[1]) * ratio)

        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)

    def add_image_centered(self, canvas, tk_img, y_pos):
        """Görseli Canvas'ın tam ortasına yerleştirir"""
        canvas.update_idletasks()
        c_width = canvas.winfo_width()
        x_pos = max(10, (c_width - tk_img.width()) // 2)
        canvas.create_image(x_pos, y_pos, anchor=tk.NW, image=tk_img)

    def display_pdf(self, pdf_path):
        self.hide_all_layouts()
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        folder = self.selected_subfolder.upper()

        # --- DÜZEN 1: HV1 veya HV2 ---
        if "HV1" in folder or "HV2" in folder:
            self.frame_single.pack(fill=tk.BOTH, expand=True)
            self.canvas_single.delete("all")
            self.images_single.clear()

            y_offset = 10
            max_w = 0

            for p in range(page_count):
                tk_img = self.render_page_fit(doc, p, self.canvas_single)
                if tk_img:
                    self.images_single.append(tk_img)
                    self.add_image_centered(self.canvas_single, tk_img, y_offset)
                    y_offset += tk_img.height() + 20
                    max_w = max(max_w, tk_img.width())

            self.canvas_single.config(scrollregion=(0, 0, max_w + 20, y_offset))

        # --- DÜZEN 2: LV3 VE 3 SAYFALI PDF ---
        elif "LV3" in folder and page_count >= 3:
            self.frame_split.pack(fill=tk.BOTH, expand=True)
            self.lv3_nav_bar.pack(fill=tk.X, side=tk.BOTTOM)

            self.lv3_doc = doc
            self.lv3_current_left_page = 0
            self.update_lv3_left_canvas()

            # Sağ Panel -> 3. Sayfa (Cevaplar)
            self.canvas_right.delete("all")
            self.images_right.clear()

            tk_img_right = self.render_page_fit(doc, 2, self.canvas_right)
            if tk_img_right:
                self.images_right.append(tk_img_right)
                self.add_image_centered(self.canvas_right, tk_img_right, 10)
                self.canvas_right.config(scrollregion=(0, 0, tk_img_right.width() + 20, tk_img_right.height() + 20))

        # --- DÜZEN 3: LV1, LV2 VEYA DİĞER ÇİFT PANELLER ---
        else:
            self.frame_split.pack(fill=tk.BOTH, expand=True)

            self.canvas_left.delete("all")
            self.canvas_right.delete("all")
            self.images_left.clear()
            self.images_right.clear()

            # Sol Panel -> Sayfa 1
            tk_img_left = self.render_page_fit(doc, 0, self.canvas_left)
            if tk_img_left:
                self.images_left.append(tk_img_left)
                self.add_image_centered(self.canvas_left, tk_img_left, 10)
                self.canvas_left.config(scrollregion=(0, 0, tk_img_left.width() + 20, tk_img_left.height() + 20))

            # Sağ Panel -> Sayfa 2 (Varsa diğer sayfalar alt alta)
            y_offset = 10
            max_w = 0

            for p in range(1, page_count):
                tk_img_r = self.render_page_fit(doc, p, self.canvas_right)
                if tk_img_r:
                    self.images_right.append(tk_img_r)
                    self.add_image_centered(self.canvas_right, tk_img_r, y_offset)
                    y_offset += tk_img_r.height() + 20
                    max_w = max(max_w, tk_img_r.width())

            self.canvas_right.config(scrollregion=(0, 0, max_w + 20, y_offset))

    def switch_lv3_page(self, page_index):
        """LV3 modunda sol taraftaki sayfayı 1 veya 2 yapar"""
        self.lv3_current_left_page = page_index
        self.update_lv3_left_canvas()

    def update_lv3_left_canvas(self):
        if not self.lv3_doc:
            return

        self.canvas_left.delete("all")
        self.images_left.clear()

        tk_img = self.render_page_fit(self.lv3_doc, self.lv3_current_left_page, self.canvas_left)
        if tk_img:
            self.images_left.append(tk_img)
            self.add_image_centered(self.canvas_left, tk_img, 10)
            self.canvas_left.config(scrollregion=(0, 0, tk_img.width() + 20, tk_img.height() + 20))

        self.lbl_lv3_page.config(text=f"Sayfa: {self.lv3_current_left_page + 1} / 2")

if __name__ == "__main__":
    root = tk.Tk()
    app = TELCQuizApp(root)
    root.mainloop()