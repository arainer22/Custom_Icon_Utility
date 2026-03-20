# IconForge

Modern Windows 11 desktop app to change shortcut icons, hide shortcut arrows, and hide icon labels — all from a single, portable `.exe`.

---

### Features

- **Drag-and-drop icon changer** — drop `.lnk` shortcuts and a new image, hit Apply
- **Batch support** — change multiple shortcut icons at once
- **Hide shortcut arrows** globally (registry-based, reversible)
- **Hide icon text labels** with invisible Unicode names
- **Restore all originals** — every change is tracked and fully reversible
- **Dark / Light / System theme** powered by customtkinter
- **Single `.exe`** — no install needed, runs from anywhere

### Screenshots

![Change Icon](assets/screenshot1.png)

*(placeholder — replace with actual screenshots)*

---

### Download

👉 **[Download IconForge.exe](https://github.com/YOUR_USERNAME/IconForge/releases/latest/download/IconForge.exe)**

---

### First-time SmartScreen Warning

Windows may show a "Windows protected your PC" dialog the first time you run the `.exe`.
Click **More info → Run anyway**. This warning disappears automatically after approximately 20 downloads.

---

### Building from Source

```bash
git clone https://github.com/YOUR_USERNAME/IconForge.git
cd IconForge
pip install -r requirements.txt
python main.py          # run directly
```

#### Build standalone `.exe`

```bash
pyinstaller --onefile --windowed --icon=assets/iconforge.ico ^
  --add-data "assets;assets" ^
  --add-data "C:/Python312/Lib/site-packages/tkinterdnd2/tkdnd;tkinterdnd2/tkdnd" ^
  --hidden-import tkinterdnd2 ^
  --hidden-import customtkinter ^
  --hidden-import win32com.client ^
  --hidden-import PIL.ImageTk ^
  --hidden-import CTkMessagebox ^
  --collect-all customtkinter ^
  --specpath=build IconForge.spec
```

> **Note:** Adjust the `tkinterdnd2/tkdnd` path to match your Python installation.

---

### License

MIT — see [LICENSE](LICENSE).
