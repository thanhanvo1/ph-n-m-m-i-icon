"""
Folder Icon Changer for External Drives
Thay đổi icon thư mục - hoạt động khi chuyển sang máy khác
Yêu cầu: Windows, Python 3.7+
"""

import os
import sys
import shutil
import ctypes
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path


# ──────────────────────────────────────────────
# Core Logic
# ──────────────────────────────────────────────

def set_folder_icon(folder_path: str, icon_path: str) -> tuple[bool, str]:
    """
    Gắn icon vào thư mục bằng cách tạo desktop.ini.
    Icon file (.ico) sẽ được copy vào thư mục để đi cùng khi chuyển máy.
    """
    folder = Path(folder_path)
    icon_src = Path(icon_path)

    if not folder.is_dir():
        return False, "Thư mục không tồn tại."
    if not icon_src.is_file() or icon_src.suffix.lower() != ".ico":
        return False, "File icon phải là định dạng .ico"

    # Copy icon vào thư mục (tên chuẩn để tránh conflict)
    icon_dest_name = ".folder_icon.ico"
    icon_dest = folder / icon_dest_name
    try:
        shutil.copy2(icon_src, icon_dest)
    except Exception as e:
        return False, f"Không thể copy icon: {e}"

    # Tạo desktop.ini
    ini_path = folder / "desktop.ini"
    if ini_path.exists():
        subprocess.run(["attrib", "-h", "-s", "-r", str(ini_path)], capture_output=True)

    ini_content = (
        "[.ShellClassInfo]\n"
        f"IconResource={icon_dest_name},0\n"
        "IconIndex=0\n"
        "[ViewState]\n"
        "Mode=\n"
        "Vid=\n"
        "FolderType=Generic\n"
    )
    try:
        ini_path.write_text(ini_content, encoding="utf-8")
    except Exception as e:
        return False, f"Không thể ghi desktop.ini: {e}"

    # Đặt thuộc tính ẩn + hệ thống cho desktop.ini và icon
    try:
        subprocess.run(
            ["attrib", "+h", "+s", str(ini_path)],
            check=True, capture_output=True
        )
        subprocess.run(
            ["attrib", "+h", str(icon_dest)],
            check=True, capture_output=True
        )
    except Exception as e:
        return False, f"Không thể đặt thuộc tính file: {e}"

    # Đặt thuộc tính System cho thư mục cha (bắt buộc để Windows nhận icon)
    try:
        subprocess.run(
            ["attrib", "+s", str(folder)],
            check=True, capture_output=True
        )
    except Exception as e:
        return False, f"Không thể đặt System attribute cho thư mục: {e}"

    # Làm mới icon trong Explorer
    _refresh_explorer(str(folder))

    return True, "Đã đặt icon thành công! ✅"


def reset_folder_icon(folder_path: str) -> tuple[bool, str]:
    """Xóa icon tùy chỉnh, khôi phục icon mặc định."""
    folder = Path(folder_path)
    if not folder.is_dir():
        return False, "Thư mục không tồn tại."

    removed = []

    for fname in ["desktop.ini", ".folder_icon.ico"]:
        fpath = folder / fname
        if fpath.exists():
            try:
                subprocess.run(["attrib", "-h", "-s", "-r", str(fpath)], capture_output=True)
                fpath.unlink()
                removed.append(fname)
            except Exception as e:
                return False, f"Không xóa được {fname}: {e}"

    # Bỏ System attribute khỏi thư mục
    try:
        subprocess.run(["attrib", "-s", str(folder)], capture_output=True)
    except Exception:
        pass

    _refresh_explorer(str(folder))

    if removed:
        return True, f"Đã xóa: {', '.join(removed)} ✅"
    return True, "Thư mục chưa có icon tùy chỉnh."


def set_drive_icon(drive_path: str, icon_path: str) -> tuple[bool, str]:
    """
    Gắn icon vào ổ đĩa bằng cách tạo autorun.inf.
    Icon file (.ico) sẽ được copy vào gốc ổ đĩa để đi cùng khi cắm sang máy khác.
    """
    drive = Path(drive_path)
    icon_src = Path(icon_path)

    if not drive.is_dir():
        return False, "Ổ đĩa không tồn tại."
    if not icon_src.is_file() or icon_src.suffix.lower() != ".ico":
        return False, "File icon phải là định dạng .ico"

    icon_dest_name = ".drive_icon.ico"
    icon_dest = drive / icon_dest_name
    try:
        shutil.copy2(icon_src, icon_dest)
    except Exception as e:
        return False, f"Không thể copy icon: {e}"

    # Tạo autorun.inf
    inf_path = drive / "autorun.inf"
    inf_content = (
        "[autorun]\n"
        f"icon={icon_dest_name}\n"
    )
    try:
        if inf_path.exists():
            subprocess.run(["attrib", "-h", "-s", "-r", str(inf_path)], capture_output=True)
        inf_path.write_text(inf_content, encoding="utf-8")
    except Exception as e:
        return False, f"Không thể ghi autorun.inf: {e}"

    # Đặt thuộc tính ẩn + hệ thống
    try:
        subprocess.run(
            ["attrib", "+h", "+s", str(inf_path)],
            check=True, capture_output=True
        )
        subprocess.run(
            ["attrib", "+h", "+s", str(icon_dest)],
            check=True, capture_output=True
        )
    except Exception as e:
        return False, f"Không thể đặt thuộc tính file: {e}"

    _refresh_explorer(str(drive))

    return True, "Đã đặt icon ổ đĩa thành công! ✅ (Rút ra cắm lại USB để cập nhật)"


def reset_drive_icon(drive_path: str) -> tuple[bool, str]:
    """Xóa icon tùy chỉnh của ổ đĩa."""
    drive = Path(drive_path)
    if not drive.is_dir():
        return False, "Ổ đĩa không tồn tại."

    removed = []

    for fname in ["autorun.inf", ".drive_icon.ico"]:
        fpath = drive / fname
        if fpath.exists():
            try:
                subprocess.run(["attrib", "-h", "-s", "-r", str(fpath)], capture_output=True)
                fpath.unlink()
                removed.append(fname)
            except Exception as e:
                return False, f"Không xóa được {fname}: {e}"

    _refresh_explorer(str(drive))

    if removed:
        return True, f"Đã xóa: {', '.join(removed)} ✅ (Rút ra cắm lại USB để cập nhật)"
    return True, "Ổ đĩa chưa có icon tùy chỉnh."


def _refresh_explorer(folder_path: str):
    """Làm mới Windows Explorer để hiển thị icon mới ngay."""
    try:
        shell32 = ctypes.windll.shell32
        # SHChangeNotify: SHCNE_UPDATEDIR | SHCNF_PATH
        shell32.SHChangeNotify(0x00002000, 0x0005, folder_path, None)
    except Exception:
        pass


def get_external_drives() -> list[str]:
    """Lấy danh sách ổ đĩa ngoài (Removable + Fixed USB)."""
    drives = []
    if sys.platform != "win32":
        return drives
    try:
        import win32api
        import win32con
        drive_list = win32api.GetLogicalDriveStrings().split("\x00")
        for d in drive_list:
            if d:
                dtype = win32api.GetDriveType(d)
                # DRIVE_REMOVABLE = 2, DRIVE_FIXED = 3
                if dtype in (2, 3):
                    drives.append(d)
    except ImportError:
        # Fallback: kiểm tra tất cả ổ đĩa A-Z
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    return drives


def check_admin() -> bool:
    """Kiểm tra quyền Admin (cần để thay đổi thuộc tính hệ thống)."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():
    """Khởi động lại chương trình với quyền Admin."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()


# ──────────────────────────────────────────────
# GUI
# ──────────────────────────────────────────────

class App(tk.Tk):
    COLORS = {
        "bg":       "#0f0f13",
        "surface":  "#1a1a24",
        "border":   "#2a2a3a",
        "accent":   "#7c6aff",
        "accent2":  "#ff6ab0",
        "success":  "#4ade80",
        "warning":  "#fbbf24",
        "error":    "#f87171",
        "text":     "#e8e8f0",
        "muted":    "#6b6b8a",
        "card":     "#141420",
    }

    def __init__(self):
        super().__init__()

        # ── Cửa sổ ──
        self.title("Folder Icon Changer")
        self.geometry("680x560")
        self.minsize(600, 500)
        self.configure(bg=self.COLORS["bg"])
        self.resizable(True, True)

        # Căn giữa màn hình
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 680) // 2
        y = (self.winfo_screenheight() - 560) // 2
        self.geometry(f"+{x}+{y}")

        # Biến
        self.folder_var = tk.StringVar()
        self.icon_var   = tk.StringVar()
        self.status_var = tk.StringVar(value="Sẵn sàng.")

        self._build_ui()
        self._check_admin_banner()

    # ── Xây UI ──────────────────────────────

    def _build_ui(self):
        c = self.COLORS

        # Header
        hdr = tk.Frame(self, bg=c["surface"], pady=0)
        hdr.pack(fill="x")

        # Gradient strip top
        strip = tk.Frame(hdr, bg=c["accent"], height=3)
        strip.pack(fill="x")

        inner_hdr = tk.Frame(hdr, bg=c["surface"], padx=28, pady=18)
        inner_hdr.pack(fill="x")

        tk.Label(
            inner_hdr, text="📁  Folder & Drive Icon Changer",
            font=("Segoe UI", 18, "bold"),
            fg=c["text"], bg=c["surface"]
        ).pack(side="left")

        tk.Label(
            inner_hdr, text="External Drive Edition",
            font=("Segoe UI", 10),
            fg=c["muted"], bg=c["surface"]
        ).pack(side="left", padx=(10, 0), pady=(6, 0))

        # Admin banner placeholder
        self.admin_banner = tk.Frame(self, bg=c["warning"], padx=16, pady=6)
        self.admin_lbl = tk.Label(
            self.admin_banner,
            text="⚠  Chưa có quyền Admin — một số thư mục có thể không thay đổi được. "
                 "[Nhấn để chạy lại với Admin]",
            font=("Segoe UI", 9),
            fg="#1a1a00", bg=c["warning"], cursor="hand2"
        )
        self.admin_lbl.pack()
        self.admin_lbl.bind("<Button-1>", lambda e: relaunch_as_admin())

        # Main content
        body = tk.Frame(self, bg=c["bg"], padx=28, pady=22)
        body.pack(fill="both", expand=True)

        # ─ Bước 1: Chọn thư mục ─
        self._section(body, "1", "Chọn thư mục hoặc ổ đĩa cần đổi icon")

        row1 = tk.Frame(body, bg=c["bg"])
        row1.pack(fill="x", pady=(0, 14))

        self._entry(row1, self.folder_var).pack(side="left", fill="x", expand=True)
        self._btn(row1, "Duyệt…", self._browse_folder, outline=True).pack(side="left", padx=(8, 0))
        self._btn(row1, "Ổ đĩa", self._pick_drive, outline=True).pack(side="left", padx=(6, 0))

        # ─ Bước 2: Chọn icon ─
        self._section(body, "2", "Chọn file icon (.ico)")

        row2 = tk.Frame(body, bg=c["bg"])
        row2.pack(fill="x", pady=(0, 22))

        self._entry(row2, self.icon_var).pack(side="left", fill="x", expand=True)
        self._btn(row2, "Duyệt…", self._browse_icon, outline=True).pack(side="left", padx=(8, 0))

        # Icon preview
        self.preview_lbl = tk.Label(
            body, text="Chưa chọn icon",
            font=("Segoe UI", 9), fg=c["muted"], bg=c["bg"]
        )
        self.preview_lbl.pack(anchor="w", pady=(0, 16))

        # ─ Nút hành động ─
        btn_row = tk.Frame(body, bg=c["bg"])
        btn_row.pack(fill="x", pady=(0, 20))

        self._btn(
            btn_row, "✅  Áp dụng Icon",
            self._apply, primary=True, padx=22, pady=10
        ).pack(side="left")

        self._btn(
            btn_row, "🔄  Khôi phục mặc định",
            self._reset, padx=16, pady=10
        ).pack(side="left", padx=(12, 0))

        # ─ Hướng dẫn ─
        info = tk.Frame(body, bg=c["card"], padx=16, pady=12,
                        highlightbackground=c["border"], highlightthickness=1)
        info.pack(fill="x")

        guide_lines = [
            ("💡", "Hỗ trợ đổi icon cho cả thư mục và ổ đĩa (USB/Ổ cứng)"),
            ("🧳", "Icon sẽ tự động theo cùng khi cắm USB sang máy khác"),
            ("🔑", "Cần quyền Admin để thay đổi thuộc tính hệ thống"),
            ("🖼", "Dùng file .ico — có thể dùng Convertio/CloudConvert để chuyển đổi"),
            ("🔁", "Sau khi áp dụng (với ổ đĩa): có thể cần rút USB ra cắm lại để cập nhật"),
        ]
        for icon, text in guide_lines:
            row = tk.Frame(info, bg=c["card"])
            row.pack(anchor="w", pady=1)
            tk.Label(row, text=icon, font=("Segoe UI", 10), bg=c["card"],
                     fg=c["text"]).pack(side="left", padx=(0, 6))
            tk.Label(row, text=text, font=("Segoe UI", 9), bg=c["card"],
                     fg=c["muted"], wraplength=540, justify="left").pack(side="left")

        # ─ Status bar ─
        status_bar = tk.Frame(self, bg=c["surface"], padx=18, pady=8)
        status_bar.pack(fill="x", side="bottom")

        self.status_dot = tk.Label(status_bar, text="●", font=("Segoe UI", 10),
                                   fg=c["muted"], bg=c["surface"])
        self.status_dot.pack(side="left")
        tk.Label(status_bar, textvariable=self.status_var,
                 font=("Segoe UI", 9), fg=c["muted"],
                 bg=c["surface"]).pack(side="left", padx=(4, 0))

    def _section(self, parent, num, text):
        c = self.COLORS
        f = tk.Frame(parent, bg=c["bg"])
        f.pack(fill="x", pady=(0, 6))
        badge = tk.Label(f, text=f" {num} ", font=("Segoe UI", 9, "bold"),
                         bg=c["accent"], fg="white", padx=4)
        badge.pack(side="left")
        tk.Label(f, text=f"  {text}", font=("Segoe UI", 10, "bold"),
                 fg=c["text"], bg=c["bg"]).pack(side="left")

    def _entry(self, parent, var):
        c = self.COLORS
        e = tk.Entry(
            parent, textvariable=var,
            font=("Consolas", 10),
            bg=c["surface"], fg=c["text"],
            insertbackground=c["text"],
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=c["border"],
            highlightcolor=c["accent"],
        )
        e.configure(highlightcolor=c["accent"])
        return e

    def _btn(self, parent, text, cmd, primary=False, outline=False, padx=12, pady=6):
        c = self.COLORS
        if primary:
            bg, fg, active_bg = c["accent"], "white", "#6050e0"
        elif outline:
            bg, fg, active_bg = c["surface"], c["text"], c["border"]
        else:
            bg, fg, active_bg = c["border"], c["text"], c["surface"]

        b = tk.Button(
            parent, text=text, command=cmd,
            font=("Segoe UI", 9, "bold" if primary else "normal"),
            bg=bg, fg=fg, activebackground=active_bg,
            activeforeground=fg,
            relief="flat", bd=0,
            padx=padx, pady=pady,
            cursor="hand2"
        )
        return b

    # ── Admin banner ─────────────────────────

    def _check_admin_banner(self):
        if not check_admin():
            self.admin_banner.pack(fill="x", after=self.winfo_children()[0])

    # ── Actions ──────────────────────────────

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Chọn thư mục hoặc ổ đĩa cần đổi icon")
        if path:
            self.folder_var.set(path.replace("/", "\\"))
            self._set_status(f"Đã chọn: {path}", "info")

    def _browse_icon(self):
        path = filedialog.askopenfilename(
            title="Chọn file icon",
            filetypes=[("Icon files", "*.ico"), ("Tất cả", "*.*")]
        )
        if path:
            self.icon_var.set(path.replace("/", "\\"))
            self.preview_lbl.config(text=f"🖼  {Path(path).name}")
            self._set_status(f"Icon: {Path(path).name}", "info")

    def _pick_drive(self):
        """Popup chọn nhanh ổ đĩa."""
        drives = get_external_drives()
        if not drives:
            messagebox.showinfo("Thông báo", "Không tìm thấy ổ đĩa ngoài nào.")
            return

        popup = tk.Toplevel(self)
        popup.title("Chọn ổ đĩa")
        popup.configure(bg=self.COLORS["bg"])
        popup.geometry("260x200")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()

        tk.Label(popup, text="Chọn ổ đĩa:",
                 font=("Segoe UI", 10, "bold"),
                 fg=self.COLORS["text"], bg=self.COLORS["bg"],
                 pady=12).pack()

        lb = tk.Listbox(popup, font=("Consolas", 11),
                        bg=self.COLORS["surface"], fg=self.COLORS["text"],
                        selectbackground=self.COLORS["accent"],
                        relief="flat", bd=0, activestyle="none")
        lb.pack(fill="both", expand=True, padx=16)
        for d in drives:
            lb.insert("end", d)

        def confirm():
            sel = lb.curselection()
            if sel:
                self.folder_var.set(drives[sel[0]])
            popup.destroy()

        self._btn(popup, "Chọn", confirm, primary=True).pack(pady=10)

    def _apply(self):
        folder = self.folder_var.get().strip()
        icon = self.icon_var.get().strip()

        if not folder:
            self._set_status("⚠  Vui lòng chọn thư mục hoặc ổ đĩa!", "warning")
            return
        if not icon:
            self._set_status("⚠  Vui lòng chọn file icon (.ico)!", "warning")
            return

        folder_path = Path(folder).resolve()
        is_drive = folder_path.parent == folder_path

        if is_drive:
            ok, msg = set_drive_icon(str(folder_path), icon)
        else:
            ok, msg = set_folder_icon(str(folder_path), icon)

        self._set_status(msg, "success" if ok else "error")
        if not ok:
            messagebox.showerror("Lỗi", msg)

    def _reset(self):
        folder = self.folder_var.get().strip()
        if not folder:
            self._set_status("⚠  Vui lòng chọn thư mục hoặc ổ đĩa!", "warning")
            return

        folder_path = Path(folder).resolve()
        is_drive = folder_path.parent == folder_path

        if is_drive:
            ok, msg = reset_drive_icon(str(folder_path))
        else:
            ok, msg = reset_folder_icon(str(folder_path))

        self._set_status(msg, "success" if ok else "error")

    def _set_status(self, msg: str, level: str = "info"):
        colors = {
            "info":    self.COLORS["muted"],
            "success": self.COLORS["success"],
            "warning": self.COLORS["warning"],
            "error":   self.COLORS["error"],
        }
        self.status_var.set(msg)
        color = colors.get(level, self.COLORS["muted"])
        self.status_dot.config(fg=color)


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if sys.platform != "win32":
        print("❌ Chương trình chỉ chạy trên Windows!")
        sys.exit(1)

    app = App()
    app.mainloop()