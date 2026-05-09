"""
视频批量加水印工具 v3
依赖: pip install PyQt6
外部依赖: ffmpeg.exe / ffprobe.exe（放同目录或加入系统 PATH）
运行: pythonw video_watermark.py
"""

APP_VERSION  = "v1.2.2"
REPO         = "secure-artifacts/video-watermark"
RELEASES_URL = f"https://github.com/{REPO}/releases/latest"
API_URL      = f"https://api.github.com/repos/{REPO}/releases/latest"

import sys, os, subprocess, platform, re, base64, tempfile
import urllib.request, urllib.error, json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QSlider, QFileDialog,
    QProgressBar, QComboBox, QColorDialog, QFrame,
    QGridLayout, QMessageBox, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QIcon, QDragEnterEvent, QDropEvent

NO_WINDOW  = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
SUPPORTED  = {".mp4",".mkv",".mov",".avi",".wmv",".flv",".webm",".m4v",".ts"}
TIME_RE    = re.compile(r"time=(\d+):(\d+):(\d+)\.(\d\d)")
SPEED_RE   = re.compile(r"speed=\s*([\d.]+)x")

class NoScrollCombo(QComboBox):
    """禁止鼠标滚轮切换选项"""
    def wheelEvent(self, e): e.ignore()

class NoScrollSlider(QSlider):
    """禁止鼠标滚轮调节值"""
    def wheelEvent(self, e): e.ignore()


FONTS = {
    "Arial":    "C:/Windows/Fonts/arial.ttf",
    "Segoe UI": "C:/Windows/Fonts/segoeui.ttf",
    "Calibri":  "C:/Windows/Fonts/calibri.ttf",
}

ENCODER_PROFILES = {
    "h264_nvenc": {
        "极压  CRF 35":    ["-c:v","h264_nvenc","-preset","p1","-rc","vbr","-cq","35"],
        "压缩  CRF 28":    ["-c:v","h264_nvenc","-preset","p2","-rc","vbr","-cq","28"],
        "快速  CRF 23":    ["-c:v","h264_nvenc","-preset","p2","-rc","vbr","-cq","23"],
        "高质量  CRF 18":  ["-c:v","h264_nvenc","-preset","p4","-rc","vbr","-cq","18"],
        "近乎无损  CRF 10":["-c:v","h264_nvenc","-preset","p6","-rc","vbr","-cq","10"],
    },
    "h264_qsv": {
        "极压  CRF 35":    ["-c:v","h264_qsv","-preset","fast",  "-global_quality","35"],
        "压缩  CRF 28":    ["-c:v","h264_qsv","-preset","fast",  "-global_quality","28"],
        "快速  CRF 23":    ["-c:v","h264_qsv","-preset","fast",  "-global_quality","23"],
        "高质量  CRF 18":  ["-c:v","h264_qsv","-preset","medium","-global_quality","18"],
        "近乎无损  CRF 10":["-c:v","h264_qsv","-preset","slow",  "-global_quality","10"],
    },
    "h264_amf": {
        "极压  CRF 35":    ["-c:v","h264_amf","-quality","speed",   "-rc","vbr_latency","-b:v","3M"],
        "压缩  CRF 28":    ["-c:v","h264_amf","-quality","speed",   "-rc","vbr_latency","-b:v","5M"],
        "快速  CRF 23":    ["-c:v","h264_amf","-quality","speed",   "-rc","vbr_latency","-b:v","8M"],
        "高质量  CRF 18":  ["-c:v","h264_amf","-quality","balanced","-rc","vbr_peak",   "-b:v","12M"],
        "近乎无损  CRF 10":["-c:v","h264_amf","-quality","quality", "-rc","vbr_peak",   "-b:v","20M"],
    },
    "libx264": {
        "极压  CRF 35":    ["-c:v","libx264","-preset","fast",  "-crf","35"],
        "压缩  CRF 28":    ["-c:v","libx264","-preset","fast",  "-crf","28"],
        "快速  CRF 23":    ["-c:v","libx264","-preset","fast",  "-crf","23"],
        "高质量  CRF 18":  ["-c:v","libx264","-preset","medium","-crf","18"],
        "近乎无损  CRF 10":["-c:v","libx264","-preset","medium","-crf","10"],
    },
}
QUALITY_KEYS = ["极压  CRF 35", "压缩  CRF 28", "快速  CRF 23", "高质量  CRF 18", "近乎无损  CRF 10"]

POSITIONS = {
    "左上角": lambda m: (str(m), str(m)),
    "右上角": lambda m: ("W-tw-"+str(m), str(m)),
    "左下角": lambda m: (str(m), "H-th-"+str(m)),
    "右下角": lambda m: ("W-tw-"+str(m), "H-th-"+str(m)),
}

_ICON_B64 = "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"


def _find_bin(name):
    exe = name + (".exe" if platform.system() == "Windows" else "")
    candidates = []
    if getattr(sys, "frozen", False):
        # onefile: 解压到临时目录 _MEIPASS
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / exe)
        # onedir: exe 同目录
        candidates.append(Path(sys.executable).parent / exe)
    else:
        candidates.append(Path(__file__).parent / exe)
    for p in candidates:
        if p.exists():
            return str(p)
    return name  # 回退到系统 PATH


def detect_encoder():
    """
    检测可用硬件编码器。
    第一步：查 ffmpeg -encoders 确认编码器存在。
    第二步：用最小参数实际编码 0.1 秒验证可用。
    RTX 50 / 新驱动 兼容。
    """
    ff = _find_bin("ffmpeg")

    # 先拿到所有可用编码器列表
    try:
        r = subprocess.run([ff, "-encoders"], capture_output=True,
                           text=True, timeout=5, creationflags=NO_WINDOW)
        encoder_list = r.stdout + r.stderr
    except Exception:
        encoder_list = ""

    candidates = []
    if "h264_nvenc" in encoder_list:
        candidates.append("h264_nvenc")
    if "h264_qsv" in encoder_list:
        candidates.append("h264_qsv")
    if "h264_amf" in encoder_list:
        candidates.append("h264_amf")

    for enc in candidates:
        try:
            # 用 nullsrc 避免 lavfi color 在某些版本上的兼容问题
            r = subprocess.run(
                [ff,
                 "-f", "lavfi", "-i", "nullsrc=s=320x240:d=0.1",
                 "-vf", "format=yuv420p",
                 "-c:v", enc,
                 "-frames:v", "1",
                 "-f", "null", "-"],
                capture_output=True, timeout=10, creationflags=NO_WINDOW)
            # returncode 0 = 成功；同时排除 "No NVENC capable devices" 类错误
            stderr_out = r.stderr.decode(errors="replace") if isinstance(r.stderr, bytes) else r.stderr
            if r.returncode == 0 and "No capable" not in stderr_out and "Cannot load" not in stderr_out:
                return enc
        except Exception:
            pass

    return "libx264"


def get_duration_ms(path):
    try:
        r = subprocess.run(
            [_find_bin("ffprobe"),"-v","error",
             "-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=3, creationflags=NO_WINDOW)
        val = r.stdout.strip()
        return float(val) * 1000 if val else 0.0
    except Exception:
        return 0.0


def parse_time_ms(line):
    m = TIME_RE.search(line)
    if not m: return None
    h,mi,s,cs = int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4))
    return (h*3600 + mi*60 + s) * 1000 + cs * 10


def parse_speed(line):
    m = SPEED_RE.search(line)
    return m.group(1) if m else None


class UpdateChecker(QThread):
    result = pyqtSignal(str, str)
    error  = pyqtSignal(str)

    def run(self):
        try:
            req = urllib.request.Request(
                API_URL, headers={"User-Agent": "video-watermark-updater"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "")
            url = data.get("html_url", RELEASES_URL)
            self.result.emit(tag, url)
        except Exception as e:
            self.error.emit(str(e))


class WatermarkWorker(QThread):
    progress         = pyqtSignal(int, int, str)
    file_done        = pyqtSignal(int, bool, str)
    all_done         = pyqtSignal()
    encoder_detected = pyqtSignal(str)

    def __init__(self, tasks, params):
        super().__init__()
        self.tasks  = tasks
        self.params = params
        self._stop  = False

    def stop(self): self._stop = True

    def run(self):
        manual = self.params.get("manual_encoder")
        encoder = manual if manual else detect_encoder()
        self.encoder_detected.emit(encoder)

        p = self.params
        # 转义水印文字
        text = p["text"].replace("\\","\\\\").replace("'","\\'").replace(":","\\:")

        color_hex = p["color"].lstrip("#")
        opacity   = p["opacity"] / 100.0
        margin    = p["margin"]
        x_expr, y_expr = POSITIONS[p["position"]](margin)
        enc_args  = ENCODER_PROFILES[encoder][p["quality"]]

        # 字体文件路径（FFmpeg drawtext 冒号需转义）
        font_file = FONTS.get(p["font"], "C:/Windows/Fonts/arial.ttf")
        font_ff   = font_file.replace(":", "\\:")
        fs  = str(p["font_size"])
        op  = f"{opacity:.2f}"
        vf  = (f"drawtext=text='{text}':fontfile='{font_ff}':"
               f"fontsize={fs}:fontcolor=0x{color_hex}@{op}:"
               f"x={x_expr}:y={y_expr}:"
               f"shadowcolor=black@0.45:shadowx=1:shadowy=1")
        for idx, task in enumerate(self.tasks):
            if self._stop: break
            inp, out = task["input"], task["output"]
            out_dir  = os.path.dirname(out)
            if out_dir: os.makedirs(out_dir, exist_ok=True)
            dur_ms = get_duration_ms(inp)
            cmd = [_find_bin("ffmpeg"),"-y","-i",inp,"-vf",vf] + enc_args + ["-c:a","copy",out]
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace",
                    creationflags=NO_WINDOW, bufsize=1)
                last_pct = 0
                for line in proc.stderr:
                    if self._stop: proc.kill(); break
                    t   = parse_time_ms(line)
                    spd = parse_speed(line)
                    if t is not None and dur_ms > 0:
                        pct = min(int(t / dur_ms * 100), 99)
                        if pct != last_pct:
                            last_pct = pct
                            self.progress.emit(idx, pct, spd or "")
                ret = proc.wait()
                if ret == 0:
                    self.progress.emit(idx, 100, "")
                    self.file_done.emit(idx, True, "完成")
                else:
                    self.file_done.emit(idx, False, f"FFmpeg 返回错误码 {ret}")
            except FileNotFoundError:
                self.file_done.emit(idx, False,
                    "未找到 ffmpeg.exe\n请将 ffmpeg.exe 和 ffprobe.exe 放到程序同目录")
                break
            except Exception as e:
                self.file_done.emit(idx, False, str(e))
        self.all_done.emit()


class DropZone(QLabel):
    files_dropped = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("将视频文件拖拽到此处\n或点击选择文件\n\nMP4  MKV  MOV  AVI  WMV 等格式")
        self.setMinimumHeight(110)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._s(False)
    def _s(self, h):
        c  = "#3498DB" if h else "#3a3a3a"
        bg = "rgba(52,152,219,0.07)" if h else "rgba(255,255,255,0.02)"
        self.setStyleSheet(f"QLabel{{border:2px dashed {c};border-radius:10px;background:{bg};color:#777;font-size:13px;padding:14px;}}")
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls(): e.acceptProposedAction(); self._s(True)
    def dragLeaveEvent(self, e): self._s(False)
    def dropEvent(self, e: QDropEvent):
        self._s(False)
        paths = [u.toLocalFile() for u in e.mimeData().urls()
                 if Path(u.toLocalFile()).suffix.lower() in SUPPORTED]
        if paths: self.files_dropped.emit(paths)
    def mousePressEvent(self, e):
        paths, _ = QFileDialog.getOpenFileNames(self,"选择视频文件","",
            "Videos (*.mp4 *.mkv *.mov *.avi *.wmv *.flv *.webm *.m4v *.ts)")
        valid = [p for p in paths if Path(p).suffix.lower() in SUPPORTED]
        if valid: self.files_dropped.emit(valid)


class FileRowWidget(QWidget):
    remove_clicked = pyqtSignal()
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self._build()
    def _build(self):
        p  = Path(self.filepath)
        vl = QVBoxLayout(self)
        vl.setContentsMargins(10,8,10,8); vl.setSpacing(3)
        top = QHBoxLayout(); top.setSpacing(8)
        icon = QLabel("▶"); icon.setFixedWidth(18)
        icon.setStyleSheet("color:#3498DB;font-size:13px;")
        name = QLabel(p.name)
        name.setStyleSheet("font-size:13px;font-weight:600;color:#ddd;")
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status = QLabel("等待"); self.status.setFixedWidth(72)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_s("wait")
        rm = QPushButton("✕"); rm.setFixedSize(18,18)
        rm.setStyleSheet("QPushButton{border:none;color:#555;background:transparent;}QPushButton:hover{color:#e74c3c;}")
        rm.clicked.connect(self.remove_clicked)
        top.addWidget(icon); top.addWidget(name); top.addWidget(self.status); top.addWidget(rm)
        sz   = self._fmt(p.stat().st_size) if p.exists() else ""
        info = QLabel(f"{sz}  ·  {p.suffix.upper().lstrip('.')}  ·  {str(p.parent)[:48]}")
        info.setStyleSheet("font-size:11px;color:#555;margin-left:26px;")
        self.bar = QProgressBar()
        self.bar.setRange(0,100); self.bar.setValue(0)
        self.bar.setTextVisible(False); self.bar.setFixedHeight(3)
        self.bar.setStyleSheet("QProgressBar{background:#2d2d2d;border-radius:1px;border:none;}QProgressBar::chunk{background:#3498DB;border-radius:1px;}")
        self.bar.hide()
        vl.addLayout(top); vl.addWidget(info); vl.addWidget(self.bar)
        self.setStyleSheet("FileRowWidget{background:#272727;border-radius:8px;}")
    def _set_s(self, state):
        d = {"wait":("等待","#333","#888"),"run":("","#1a3a5c","#3498DB"),
             "done":("✓ 完成","#1a3d2b","#27ae60"),"fail":("✗ 失败","#3d1a1a","#e74c3c")}
        txt,bg,fg = d[state]
        if txt: self.status.setText(txt)
        self.status.setStyleSheet(f"font-size:11px;border-radius:10px;padding:2px 4px;background:{bg};color:{fg};")
    def set_progress(self, pct):
        self.bar.show(); self.bar.setValue(pct)
        self._set_s("run"); self.status.setText(f"{pct}%")
    def set_done(self, ok):
        self.bar.setValue(100 if ok else 0)
        if ok:
            self.bar.setStyleSheet("QProgressBar{background:#2d2d2d;border-radius:1px;border:none;}QProgressBar::chunk{background:#27ae60;border-radius:1px;}")
        self._set_s("done" if ok else "fail")
    def reset(self):
        self.bar.hide(); self.bar.setValue(0)
        self.bar.setStyleSheet("QProgressBar{background:#2d2d2d;border-radius:1px;border:none;}QProgressBar::chunk{background:#3498DB;border-radius:1px;}")
        self._set_s("wait")
    @staticmethod
    def _fmt(b):
        for u in ["B","KB","MB","GB"]:
            if b < 1024: return f"{b:.1f} {u}"
            b //= 1024
        return f"{b:.1f} TB"


class ColorSwatch(QPushButton):
    def __init__(self, color="#FFFFFF"):
        super().__init__()
        self.color = color
        self.setFixedSize(28,28)
        self._a()
        self.clicked.connect(self._pick)
    def _a(self):
        self.setStyleSheet(f"QPushButton{{background:{self.color};border:2px solid #555;border-radius:5px;}}QPushButton:hover{{border-color:#999;}}")
    def _pick(self):
        c = QColorDialog.getColor(QColor(self.color), self, "选择颜色")
        if c.isValid(): self.color = c.name().upper(); self._a()
    def get(self): return self.color


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频批量加水印")
        self.setMinimumSize(1080, 680)
        self.resize(1200, 740)
        self.file_rows    = []
        self.worker       = None
        self._current_pos = "左上角"
        self._done_count  = 0
        self._total       = 0
        self._task_done = False
        self._theme()
        self._build_ui()
        self._set_icon()
        QTimer.singleShot(200, self._check_ffmpeg)
        QTimer.singleShot(1500, self._auto_check_update)  # 启动后静默检测

    def _set_icon(self):
        try:
            data = base64.b64decode(_ICON_B64)
            tmp  = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
            tmp.write(data); tmp.close()
            self.setWindowIcon(QIcon(tmp.name))
            os.unlink(tmp.name)
        except Exception:
            pass

    def _theme(self):
        self.setStyleSheet("""
            QMainWindow,QWidget{background:#1e1e1e;color:#ddd;
                font-family:'PingFang SC','Microsoft YaHei','Segoe UI',sans-serif;font-size:13px;}
            QLineEdit,QComboBox{background:#2a2a2a;border:1px solid #3a3a3a;border-radius:6px;padding:6px 9px;color:#ddd;}
            QLineEdit:focus,QComboBox:focus{border-color:#3498DB;}
            QComboBox::drop-down{border:none;width:20px;}
            QComboBox QAbstractItemView{background:#2a2a2a;border:1px solid #444;selection-background-color:#3498DB;padding:4px;}
            QSlider::groove:horizontal{height:4px;background:#3a3a3a;border-radius:2px;}
            QSlider::handle:horizontal{width:16px;height:16px;border-radius:8px;background:#3498DB;margin:-6px 0;}
            QSlider::sub-page:horizontal{background:#3498DB;border-radius:2px;}
            QScrollBar:vertical{background:#1e1e1e;width:5px;border-radius:2px;}
            QScrollBar::handle:vertical{background:#3a3a3a;border-radius:2px;min-height:20px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
        """)

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        hl = QHBoxLayout(root); hl.setContentsMargins(0,0,0,0); hl.setSpacing(0)
        hl.addWidget(self._left_panel(), stretch=1)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setStyleSheet("color:#2a2a2a;")
        hl.addWidget(sep)
        hl.addWidget(self._right_panel(), stretch=0)

    def _left_panel(self):
        w  = QWidget(); w.setStyleSheet("background:#1e1e1e;")
        vl = QVBoxLayout(w); vl.setContentsMargins(20,18,20,14); vl.setSpacing(10)
        title = QLabel("视频批量加水印")
        title.setStyleSheet("font-size:18px;font-weight:700;color:#fff;")
        self.tag_lbl = QLabel("  检测中…")
        self.tag_lbl.setStyleSheet("font-size:11px;background:#2a2a2a;color:#777;border-radius:10px;padding:2px 10px;")

        hr = QHBoxLayout()
        hr.addWidget(title); hr.addWidget(self.tag_lbl); hr.addStretch()
        vl.addLayout(hr)
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._add_files)
        vl.addWidget(self.drop_zone)
        lh = QHBoxLayout()
        self.files_lbl = QLabel("已选文件 (0)")
        self.files_lbl.setStyleSheet("font-size:11px;color:#555;letter-spacing:1px;")
        clr = QPushButton("清空列表")
        clr.setStyleSheet("QPushButton{border:none;color:#555;background:transparent;font-size:11px;}QPushButton:hover{color:#e74c3c;}")
        clr.clicked.connect(self._clear_files)
        lh.addWidget(self.files_lbl); lh.addStretch(); lh.addWidget(clr)
        vl.addLayout(lh)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;}")
        self.file_box = QWidget(); self.file_box.setStyleSheet("background:transparent;")
        self.file_vl  = QVBoxLayout(self.file_box)
        self.file_vl.setContentsMargins(0,0,4,0); self.file_vl.setSpacing(6)
        self.file_vl.addStretch()
        scroll.setWidget(self.file_box)
        vl.addWidget(scroll, stretch=1)

        # 左下角版本号 + 检测更新（紧挨在一起）
        bot = QHBoxLayout()
        bot.setContentsMargins(0, 4, 0, 0)
        bot.setSpacing(6)
        self.ver_lbl = QLabel(f"版本  {APP_VERSION}")
        self.ver_lbl.setStyleSheet("font-size:11px;color:#555;")
        self.update_btn = QPushButton("检测更新")
        self.update_btn.setFixedHeight(22)
        self.update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_btn.setStyleSheet(
            "QPushButton{background:transparent;border:1px solid #3a3a3a;"
            "border-radius:11px;color:#666;font-size:11px;padding:0 10px;}"
            "QPushButton:hover{border-color:#3498DB;color:#3498DB;}")
        self.update_btn.clicked.connect(self._check_update)
        bot.addWidget(self.ver_lbl)
        bot.addWidget(self.update_btn)
        bot.addStretch()
        vl.addLayout(bot)

        return w

    def _right_panel(self):
        panel = QWidget(); panel.setFixedWidth(320)
        panel.setStyleSheet("background:#252525;")
        outer = QVBoxLayout(panel); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:#252525;}")
        inner = QWidget(); inner.setStyleSheet("background:#252525;")
        vl = QVBoxLayout(inner); vl.setContentsMargins(18,16,18,12); vl.setSpacing(10)

        vl.addWidget(self._sec("水印文字"))
        self.wm_text = QLineEdit("AI-Generated (Audio & Visuals)")
        vl.addWidget(self.wm_text)

        vl.addWidget(self._sec("水印字体"))
        self.font_cb = QComboBox()
        for fn in FONTS: self.font_cb.addItem(fn)
        self.font_cb.setCurrentIndex(0)
        vl.addWidget(self.font_cb)

        vl.addWidget(self._sec("字体大小"))
        self.font_sl  = QSlider(Qt.Orientation.Horizontal)
        self.font_sl.setRange(8,120); self.font_sl.setValue(20)
        self.font_val = QLabel("20 px"); self.font_val.setFixedWidth(44)
        self.font_val.setStyleSheet("color:#3498DB;font-size:12px;")
        self.font_sl.valueChanged.connect(lambda v: self.font_val.setText(f"{v} px"))
        r = QHBoxLayout(); r.addWidget(self.font_sl); r.addWidget(self.font_val)
        vl.addLayout(r)

        vl.addWidget(self._sec("水印颜色"))
        cr = QHBoxLayout(); cr.setSpacing(7)
        self.color_sw = ColorSwatch("#FFFFFF"); cr.addWidget(self.color_sw)
        for c in ["#FFFFFF","#FFD700","#FF4444","#00FF88","#000000"]:
            b = QPushButton(); b.setFixedSize(24,24)
            b.setStyleSheet(f"QPushButton{{background:{c};border:1px solid #555;border-radius:4px;}}QPushButton:hover{{border-color:#bbb;}}")
            b.clicked.connect(lambda _,col=c: self._set_color(col)); cr.addWidget(b)
        cr.addStretch(); vl.addLayout(cr)

        vl.addWidget(self._sec("透明度"))
        self.op_sl  = QSlider(Qt.Orientation.Horizontal)
        self.op_sl.setRange(10,100); self.op_sl.setValue(80)
        self.op_val = QLabel("80%"); self.op_val.setFixedWidth(36)
        self.op_val.setStyleSheet("color:#3498DB;font-size:12px;")
        self.op_sl.valueChanged.connect(lambda v: self.op_val.setText(f"{v}%"))
        r2 = QHBoxLayout(); r2.addWidget(self.op_sl); r2.addWidget(self.op_val)
        vl.addLayout(r2)

        vl.addWidget(self._div())

        vl.addWidget(self._sec("水印位置"))
        pg = QGridLayout(); pg.setSpacing(6)
        self.pos_btns = {}
        for name,row,col in [("左上角",0,0),("右上角",0,1),("左下角",1,0),("右下角",1,1)]:
            b = QPushButton(name); b.setCheckable(True); b.setFixedHeight(34)
            b.clicked.connect(lambda _,n=name: self._sel_pos(n))
            self.pos_btns[name] = b; pg.addWidget(b,row,col)
        self._sel_pos("左上角"); vl.addLayout(pg)

        vl.addWidget(self._sec("边距（水印距画面边缘 px）"))
        self.mg_sl  = NoScrollSlider(Qt.Orientation.Horizontal)
        self.mg_sl.setRange(0,200); self.mg_sl.setValue(10)
        self.mg_val = QLabel("10 px"); self.mg_val.setFixedWidth(44)
        self.mg_val.setStyleSheet("color:#3498DB;font-size:12px;")
        self.mg_sl.valueChanged.connect(lambda v: self.mg_val.setText(f"{v} px"))
        r3 = QHBoxLayout(); r3.addWidget(self.mg_sl); r3.addWidget(self.mg_val)
        vl.addLayout(r3)

        vl.addWidget(self._div())

        vl.addWidget(self._sec("编码器"))
        self.enc_cb = NoScrollCombo()
        self.enc_cb.addItem("🔍 自动检测")
        self.enc_cb.addItem("🟢 NVIDIA GPU  (h264_nvenc)")
        self.enc_cb.addItem("🟢 Intel GPU   (h264_qsv)")
        self.enc_cb.addItem("🟢 AMD GPU     (h264_amf)")
        self.enc_cb.addItem("🟡 CPU 软件编码 (libx264)")
        self.enc_cb.setCurrentIndex(0)
        self.enc_cb.setToolTip("自动检测失败时可手动指定显卡")
        vl.addWidget(self.enc_cb)
        self.enc_hint = QLabel("编码器检测中…")
        self.enc_hint.setStyleSheet("font-size:12px;color:#888;")
        self.enc_hint.setWordWrap(True)
        vl.addWidget(self.enc_hint)

        vl.addWidget(self._sec("输出质量"))
        self.quality_cb = NoScrollCombo()
        for k in QUALITY_KEYS: self.quality_cb.addItem(k)
        self.quality_cb.setCurrentIndex(4)
        vl.addWidget(self.quality_cb)

        vl.addWidget(self._div())

        vl.addWidget(self._sec("输出文件名前缀"))
        self.prefix_edit = QLineEdit("加水印-")
        vl.addWidget(self.prefix_edit)

        vl.addWidget(self._sec("输出目录"))
        or_ = QHBoxLayout(); or_.setSpacing(6)
        self.out_edit = QLineEdit(); self.out_edit.setPlaceholderText("默认：原视频所在目录")
        browse = QPushButton("浏览"); browse.setFixedWidth(50)
        browse.setStyleSheet("QPushButton{background:#2d2d2d;border:1px solid #3a3a3a;border-radius:6px;color:#ccc;padding:6px;}QPushButton:hover{background:#333;}")
        browse.clicked.connect(self._browse_out)
        or_.addWidget(self.out_edit); or_.addWidget(browse)
        vl.addLayout(or_)
        vl.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll, stretch=1)

        bottom = QWidget(); bottom.setStyleSheet("background:#252525;border-top:1px solid #2a2a2a;")
        bl = QVBoxLayout(bottom); bl.setContentsMargins(18,10,18,16); bl.setSpacing(5)
        self.info_lbl = QLabel("")
        self.info_lbl.setStyleSheet("font-size:11px;color:#666;")
        self.info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_lbl.hide()
        self.total_bar = QProgressBar()
        self.total_bar.setRange(0,100); self.total_bar.setValue(0)
        self.total_bar.setTextVisible(False); self.total_bar.setFixedHeight(5)
        self.total_bar.hide()
        self.total_bar.setStyleSheet("QProgressBar{background:#2d2d2d;border-radius:2px;border:none;}QProgressBar::chunk{background:#27ae60;border-radius:2px;}")
        self.start_btn = QPushButton("开始处理")
        self.start_btn.setFixedHeight(44)
        self.start_btn.setStyleSheet(self._bstyle("#3498DB","#2980b9"))
        self.start_btn.clicked.connect(self._start_stop)
        bl.addWidget(self.info_lbl); bl.addWidget(self.total_bar); bl.addWidget(self.start_btn)
        outer.addWidget(bottom)
        return panel

    def _sec(self, t):
        l = QLabel(t)
        l.setStyleSheet("font-size:12px;font-weight:600;color:#aaa;margin-top:4px;")
        return l

    def _div(self):
        f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); f.setStyleSheet("color:#2a2a2a;"); return f

    def _bstyle(self, bg, hv):
        return (f"QPushButton{{background:{bg};color:white;border:none;border-radius:8px;font-size:14px;font-weight:600;}}"
                f"QPushButton:hover{{background:{hv};}}QPushButton:pressed{{background:{hv};}}"
                f"QPushButton:disabled{{background:#2d2d2d;color:#555;}}")

    def _sel_pos(self, name):
        self._current_pos = name
        act = "QPushButton{background:#1a3d2b;border:1.5px solid #27ae60;border-radius:6px;color:#27ae60;font-size:13px;}"
        idl = "QPushButton{background:#2a2a2a;border:1px solid #3a3a3a;border-radius:6px;color:#777;font-size:13px;}QPushButton:hover{border-color:#555;color:#bbb;}"
        for n,b in self.pos_btns.items():
            b.setChecked(n==name); b.setStyleSheet(act if n==name else idl)

    def _set_color(self, c):
        self.color_sw.color = c; self.color_sw._a()

    def _browse_out(self):
        d = QFileDialog.getExistingDirectory(self,"选择输出目录")
        if d: self.out_edit.setText(d)

    def _add_files(self, paths):
        # 上一批任务已完成，拖入新文件时自动清空旧记录
        if self._task_done:
            self._clear_files()
            self._task_done = False
        existing = {r.filepath for r in self.file_rows}
        for p in paths:
            if p not in existing:
                row = FileRowWidget(p)
                row.remove_clicked.connect(lambda r=row: self._remove(r))
                self.file_rows.append(row)
                self.file_vl.insertWidget(self.file_vl.count()-1, row)
        self._refresh()

    def _remove(self, row):
        self.file_rows.remove(row); row.setParent(None); row.deleteLater(); self._refresh()

    def _clear_files(self):
        for r in self.file_rows: r.setParent(None); r.deleteLater()
        self.file_rows.clear(); self._refresh()

    def _set_right_panel_enabled(self, enabled: bool):
        """处理中禁用右侧所有控件（开始按钮除外）"""
        skip = {self.start_btn}
        for w in [self.wm_text, self.font_cb, self.font_sl, self.color_sw,
                  self.op_sl, self.mg_sl, self.enc_cb, self.quality_cb,
                  self.prefix_edit, self.out_edit]:
            w.setEnabled(enabled)
        for btn in self.pos_btns.values():
            btn.setEnabled(enabled)
        # 颜色快选按钮
        for w in self.findChildren(QPushButton):
            if w not in skip:
                if hasattr(w, '_is_color_btn'):
                    w.setEnabled(enabled)

    def _refresh(self):
        n = len(self.file_rows)
        self.files_lbl.setText(f"已选文件 ({n})")
        self.start_btn.setText(f"开始处理  ({n} 个文件)" if n else "开始处理")

    def _start_stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop(); self.start_btn.setText("正在停止…"); self.start_btn.setEnabled(False)
        self._set_right_panel_enabled(True); self._task_done = True; return
        if not self.file_rows:
            QMessageBox.information(self,"提示","请先添加视频文件"); return
        for r in self.file_rows: r.reset()
        self.total_bar.setValue(0); self.total_bar.show()
        self.info_lbl.setText("正在检测编码器…"); self.info_lbl.show()
        prefix  = self.prefix_edit.text().strip() or "加水印-"
        out_dir = self.out_edit.text().strip()
        tasks   = []
        for r in self.file_rows:
            p = Path(r.filepath)
            d = Path(out_dir) if out_dir else p.parent
            tasks.append({"input":str(p),"output":str(d/(prefix+p.name))})
        params = {
            "text":      self.wm_text.text(),
            "font":      self.font_cb.currentText(),
            "font_size": self.font_sl.value(),
            "color":     self.color_sw.get(),
            "opacity":   self.op_sl.value(),
            "position":  self._current_pos,
            "margin":    self.mg_sl.value(),
            "quality":   self.quality_cb.currentText(),
        }
        # 手动指定编码器
        enc_map = {
            0: None,               # 自动检测
            1: "h264_nvenc",
            2: "h264_qsv",
            3: "h264_amf",
            4: "libx264",
        }
        manual_enc = enc_map.get(self.enc_cb.currentIndex())
        params["manual_encoder"] = manual_enc

        self._done_count = 0; self._total = len(tasks)
        self.worker = WatermarkWorker(tasks, params)
        self.worker.encoder_detected.connect(self._on_encoder)
        self.worker.progress.connect(self._on_prog)
        self.worker.file_done.connect(self._on_done)
        self.worker.all_done.connect(self._on_all_done)
        self.worker.start()
        self.start_btn.setText("停止处理")
        self.start_btn.setStyleSheet(self._bstyle("#c0392b","#a93226"))
        self._set_right_panel_enabled(False)

    def _on_encoder(self, enc):
        name_map = {"h264_nvenc":"NVIDIA GPU 加速","h264_qsv":"Intel GPU 加速",
                    "h264_amf":"AMD GPU 加速","libx264":"CPU 软件编码"}
        label = name_map.get(enc, enc)
        color = "#27ae60" if enc != "libx264" else "#f39c12"
        self.enc_hint.setText(f"当前编码器：{label}")
        self.enc_hint.setStyleSheet(f"font-size:11px;color:{color};")

    def _on_prog(self, idx, pct, speed):
        if idx < len(self.file_rows): self.file_rows[idx].set_progress(pct)
        if self._total > 0:
            tot = int((self._done_count * 100 + pct) / self._total)
            self.total_bar.setValue(tot)
            spd = f"  速度 {speed}x" if speed else ""
            self.info_lbl.setText(f"第 {idx+1}/{self._total} 个  {pct}%{spd}  —  总进度 {tot}%")

    def _on_done(self, idx, ok, msg):
        if idx < len(self.file_rows): self.file_rows[idx].set_done(ok)
        self._done_count += 1
        if not ok: QMessageBox.warning(self,"处理失败",f"第 {idx+1} 个文件失败:\n{msg}")

    def _on_all_done(self):
        self.worker = None
        self.total_bar.setValue(100)
        self.info_lbl.setText(f"✓ 全部完成  ({self._total} 个文件)")
        self.start_btn.setEnabled(True)
        self.start_btn.setText(f"开始处理  ({len(self.file_rows)} 个文件)")
        self.start_btn.setStyleSheet(self._bstyle("#3498DB","#2980b9"))
        self._set_right_panel_enabled(True)
        self._task_done = True
        QMessageBox.information(self,"完成",f"全部 {self._total} 个文件处理完毕！")

    def _check_ffmpeg(self):
        ff = _find_bin("ffmpeg")
        try:
            r   = subprocess.run([ff,"-version"],capture_output=True,text=True,timeout=5,creationflags=NO_WINDOW)
            ver = r.stdout.split("version")[1].split()[0] if "version" in r.stdout else ""
            self.tag_lbl.setText(f"  ✓  FFmpeg {ver}")
            self.tag_lbl.setStyleSheet("font-size:11px;background:#1a3d2b;color:#27ae60;border-radius:10px;padding:2px 10px;")
            QTimer.singleShot(100, self._detect_enc_async)
        except Exception:
            self.tag_lbl.setText("  ✗  未找到 FFmpeg")
            self.tag_lbl.setStyleSheet("font-size:11px;background:#3d1a1a;color:#e74c3c;border-radius:10px;padding:2px 10px;")
            self.start_btn.setEnabled(False)

    def _detect_enc_async(self):
        self._on_encoder(detect_encoder())

    # ── 更新检测 ─────────────────────────────────────────────────
    _update_url = ""   # 记录最新版下载链接

    def _auto_check_update(self):
        """启动时静默检测，结果只更新按钮状态，绝不弹窗"""
        self._run_checker(silent=True)

    def _check_update(self):
        """用户手动点击：若已知有更新直接弹窗；否则重新检测"""
        if self.update_btn.text() == "有可用更新" and MainWindow._update_url:
            # 已经检测过有新版，直接弹下载对话框
            import webbrowser
            ret = QMessageBox.information(
                self, "发现新版本",
                f"当前版本：{APP_VERSION}\n\n前往下载页面？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret == QMessageBox.StandardButton.Yes:
                webbrowser.open(MainWindow._update_url)
            return
        self._run_checker(silent=False)

    def _run_checker(self, silent):
        self._checking_silent = silent
        self.update_btn.setEnabled(False)
        if silent:
            self.update_btn.setText("检测更新")
        else:
            self.update_btn.setText("检测中…")
        checker = UpdateChecker()
        checker.result.connect(self._on_update_result)
        checker.error.connect(self._on_update_error)
        checker.start()
        self._updater = checker   # 防止被 GC

    def _btn_style_default(self):
        return ("QPushButton{background:transparent;border:1px solid #3a3a3a;"
                "border-radius:11px;color:#666;font-size:11px;padding:0 10px;}"
                "QPushButton:hover{border-color:#3498DB;color:#3498DB;}")

    def _on_update_result(self, latest, url):
        self.update_btn.setEnabled(True)
        silent = self._checking_silent
        MainWindow._update_url = url

        if latest and latest != APP_VERSION:
            # 有可用更新 → 橙色背景显眼提示
            self.update_btn.setText("有可用更新")
            self.update_btn.setStyleSheet(
                "QPushButton{background:#e67e22;border:none;"
                "border-radius:11px;color:#fff;font-size:11px;"
                "font-weight:600;padding:0 12px;}"
                "QPushButton:hover{background:#d35400;}"
                "QPushButton:pressed{background:#b94600;}")
            self.update_btn.setToolTip(f"新版本 {latest} 可用，点击下载")
            # 手动点击才弹窗
            if not silent:
                self._show_update_dialog(latest, url)
        else:
            # 已是最新 → 绿色文字
            self.update_btn.setText("当前最新版 ✓")
            self.update_btn.setStyleSheet(
                "QPushButton{background:transparent;border:1px solid #27ae60;"
                "border-radius:11px;color:#27ae60;font-size:11px;padding:0 10px;}"
                "QPushButton:hover{background:rgba(39,174,96,0.1);}")
            self.update_btn.setToolTip("")
            if not silent:
                QMessageBox.information(
                    self, "检测更新", f"当前已是最新版本  {APP_VERSION} 🎉")

    def _on_update_error(self, msg):
        self.update_btn.setEnabled(True)
        silent = self._checking_silent
        # 无论静默还是手动，网络失败都不弹窗，仅恢复按钮
        self.update_btn.setText("检测更新")
        self.update_btn.setStyleSheet(self._btn_style_default())
        self.update_btn.setToolTip("")
        # 手动点击时才提示网络错误
        if not silent:
            QMessageBox.warning(
                self, "检测失败", "无法连接更新服务器，请检查网络连接。")

    def _show_update_dialog(self, latest, url):
        ret = QMessageBox.information(
            self, "发现新版本",
            f"当前版本：{APP_VERSION}\n最新版本：{latest}\n\n前往下载页面？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            import webbrowser
            webbrowser.open(url)

    def closeEvent(self, e):
        if self.worker and self.worker.isRunning(): self.worker.stop(); self.worker.wait(3000)
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("视频批量加水印")
    MainWindow().show()
    sys.exit(app.exec())
