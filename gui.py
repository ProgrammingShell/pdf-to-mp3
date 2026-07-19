import asyncio
import threading
import queue
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from core.pdf_reader import extract_text, split_text
from core.tts_engine import EdgeTTSEngine
from core.audio_utils import merge_mp3


class AutocompleteCombobox(tk.Frame):

    def __init__(self, parent, textvariable, values, width=40, **kwargs):
        super().__init__(parent)
        self.all_values = values
        self.var = textvariable
        
        self.entry = ttk.Entry(self, textvariable=self.var, width=width, **kwargs)
        self.entry.pack(side="left", fill="x", expand=True)
        
        self.arrow_btn = ttk.Button(self, text="▼", width=3, command=self._toggle_dropdown)
        self.arrow_btn.pack(side="right")
        
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Double-Button-1>", lambda e: self._show_all_values())

        self.popup = tk.Toplevel(self)
        self.popup.overrideredirect(True)
        self.popup.withdraw()
        
        list_frame = tk.Frame(self.popup)
        list_frame.pack(fill="both", expand=True)
        
        self.scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(
            list_frame, 
            bd=1, 
            relief="solid", 
            selectmode=tk.SINGLE,
            yscrollcommand=self.scrollbar.set
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.listbox.yview)
        
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Return>", self._on_select)
        self.listbox.bind("<Escape>", lambda e: self.hide_popup())

    def update_values(self, new_values):
        self.all_values = list(new_values)

    def _on_key_release(self, event):
        if event.keysym in ("Up", "Down", "Left", "Right", "Return", "Escape", "Tab", "Shift_L", "Shift_R"):
            return

        typed = self.var.get().strip()
        if not typed:
            self._show_all_values()
            return

        typed_lower = typed.lower()
        matches = [val for val in self.all_values if val.lower().startswith(typed_lower)]

        if matches:
            self._fill_listbox(matches)
            self.show_popup()
        else:
            self.hide_popup()

    def _toggle_dropdown(self):
        if self.popup.winfo_viewable():
            self.hide_popup()
        else:
            self.entry.focus_set()
            self._show_all_values()

    def _show_all_values(self):
        if self.all_values:
            self._fill_listbox(self.all_values)
            
            current_val = self.var.get()
            if current_val in self.all_values:
                idx = self.all_values.index(current_val)
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(idx)
                self.listbox.see(idx)
                
            self.show_popup()

    def _fill_listbox(self, items):
        self.listbox.delete(0, tk.END)
        for item in items:
            self.listbox.insert(tk.END, item)

    def show_popup(self):
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        width = self.winfo_width()
        
        num_items = min(self.listbox.size(), 10)
        height = (num_items * 20) + 4
        
        self.popup.geometry(f"{width}x{height}+{x}+{y}")
        self.popup.deiconify()
        self.popup.lift()

    def hide_popup(self):
        self.popup.withdraw()

    def _on_arrow_down(self, event):
        if not self.popup.winfo_viewable():
            self._show_all_values()
        
        if self.listbox.size() > 0:
            self.listbox.focus_set()
            if not self.listbox.curselection():
                self.listbox.selection_set(0)

    def _on_select(self, event=None):
        if not self.listbox.curselection():
            return
        index = self.listbox.curselection()[0]
        val = self.listbox.get(index)
        
        self.var.set(val)
        self.hide_popup()
        self.entry.focus_set()
        self.entry.icursor(tk.END)

    def _on_focus_out(self, event):
        self.after(150, self._check_external_focus)

    def _check_external_focus(self):
        focused = self.focus_get()
        if focused not in (self.entry, self.listbox, self.arrow_btn, self.scrollbar):
            self.hide_popup()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to Speech")
        self.engine = EdgeTTSEngine()
        self.pdf_path = tk.StringVar()
        self.output_path = tk.StringVar(value="output.mp3")
        self.rate = tk.IntVar(value=0)
        self.voice_var = tk.StringVar()
        self.all_voices = []  
        self.status_queue = queue.Queue()

        self._build_ui()
        self._load_voices()
        self._poll_queue()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        frame1 = tk.Frame(self.root)
        frame1.pack(fill="x", **pad)
        tk.Label(frame1, text="PDF file:").pack(side="left")
        tk.Entry(frame1, textvariable=self.pdf_path, width=40).pack(side="left", padx=6)
        tk.Button(frame1, text="Browse", command=self._pick_pdf).pack(side="left")

        frame2 = tk.Frame(self.root)
        frame2.pack(fill="x", **pad)
        tk.Label(frame2, text="Output MP3:").pack(side="left")
        tk.Entry(frame2, textvariable=self.output_path, width=40).pack(side="left", padx=6)
        tk.Button(frame2, text="Choose", command=self._pick_output).pack(side="left")

        frame3 = tk.Frame(self.root)
        frame3.pack(fill="x", **pad)
        tk.Label(frame3, text="Voice:").pack(side="left")
        
        # REPLACED standard ttk.Combobox with our Custom Non-blocking AutocompleteCombobox
        self.voice_dropdown = AutocompleteCombobox(frame3, textvariable=self.voice_var, values=self.all_voices, width=40)
        self.voice_dropdown.pack(side="left", padx=6)

        frame4 = tk.Frame(self.root)
        frame4.pack(fill="x", **pad)
        tk.Label(frame4, text="Speed:").pack(side="left")
        tk.Scale(frame4, from_=-75, to=100, orient="horizontal", variable=self.rate,
                 length=300, resolution=5).pack(side="left", padx=6)
        tk.Label(frame4, text="%").pack(side="left")

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(fill="x", **pad)

        self.status_label = tk.Label(self.root, text="Ready.")
        self.status_label.pack(fill="x", **pad)

        self.start_btn = tk.Button(self.root, text="Convert", command=self._start_conversion)
        self.start_btn.pack(**pad)

    def _pick_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_path.set(path)

    def _pick_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 files", "*.mp3")])
        if path:
            self.output_path.set(path)

    def _load_voices(self):
        def worker():
            try:
                voices = asyncio.run(self.engine.list_voices())
                self.status_queue.put(("voices", voices))
            except Exception as e:
                self.status_queue.put(("error", f"Failed to load voices: {e}"))
        threading.Thread(target=worker, daemon=True).start()
        self.status_label.config(text="Loading voices...")

    def _start_conversion(self):
        pdf_path = self.pdf_path.get()
        output_path = self.output_path.get()
        voice = self.voice_var.get()
        rate = f"{'+' if self.rate.get() >= 0 else ''}{self.rate.get()}%"

        if not pdf_path:
            messagebox.showerror("Error", "Please select a PDF file.")
            return
        if not voice:
            messagebox.showerror("Error", "Please select a voice.")
            return
        if voice not in self.all_voices:
            messagebox.showerror("Error", "That's not a valid voice name. Please pick one from the list.")
            return

        self.start_btn.config(state="disabled")
        self.progress["value"] = 0
        self.status_label.config(text="Starting...")

        def worker():
            try:
                text = extract_text(pdf_path)
                chunks = split_text(text)
                total = len(chunks)
                chunk_paths = []

                for i, chunk in enumerate(chunks):
                    path = f"chunk_{i:03}.mp3"
                    asyncio.run(self.engine.synthesize(chunk, voice, rate, path))
                    chunk_paths.append(path)
                    self.status_queue.put(("progress", (i + 1, total)))

                self.status_queue.put(("status", "Merging chunks..."))
                merge_mp3(chunk_paths, output_path)
                self.status_queue.put(("done", output_path))
            except Exception as e:
                self.status_queue.put(("error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.status_queue.get_nowait()
                if kind == "voices":
                    self.all_voices = list(payload)
                    self.voice_dropdown.update_values(payload)
                    if payload:
                        self.voice_var.set(payload[0])
                    self.status_label.config(text="Ready.")
                elif kind == "progress":
                    i, total = payload
                    self.progress["maximum"] = total
                    self.progress["value"] = i
                    self.status_label.config(text=f"Synthesizing chunk {i}/{total}...")
                elif kind == "status":
                    self.status_label.config(text=payload)
                elif kind == "done":
                    self.status_label.config(text=f"Done. Saved to {payload}")
                    self.start_btn.config(state="normal")
                    messagebox.showinfo("Complete", f"Saved to {payload}")
                elif kind == "error":
                    self.status_label.config(text=f"Error: {payload}")
                    self.start_btn.config(state="normal")
                    messagebox.showerror("Error", payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)


def launch():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    launch()