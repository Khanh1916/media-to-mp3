"""
Tab cắt & ghép nhạc: danh sách đoạn (ghép theo thứ tự), dạng sóng để kéo chọn khoảng cắt,
hiệu ứng fade / crossfade / âm lượng và xuất ra MP3, M4A, WAV, FLAC.
"""
import os
import queue
import threading
import tkinter as tk
from dataclasses import dataclass, field
from typing import List, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox

import audio_tools as at
from downloader import AUDIO_FORMATS
from i18n import t
from platform_utils import open_path_in_explorer, play_audio_file

FORMAT_LABELS = {key: spec["label"] for key, spec in AUDIO_FORMATS.items()}
BITRATE_LABELS = {b: f"{b} kbps" for b in AUDIO_FORMATS["mp3"]["bitrates"]}
AUDIO_PATTERNS = "*.mp3 *.m4a *.aac *.wav *.flac *.ogg *.opus *.webm *.mp4 *.wma"
MIN_LENGTH = 0.1

WAVE_BG = "#161B22"
WAVE_SELECTION = "#1F3A56"
WAVE_COLOR = "#4FC3F7"
WAVE_DIM = "#2B5876"
START_COLOR = "#66BB6A"
END_COLOR = "#EF5350"
PLAYHEAD_COLOR = "#FFD54F"
TEXT_COLOR = "#9AA4B2"


@dataclass
class Clip:
    path: str
    duration: float
    start: float = 0.0
    end: float = 0.0
    title: str = ""
    artist: str = ""
    has_cover: bool = False
    peaks: Optional[List[float]] = None

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    def spec(self) -> at.ClipSpec:
        return at.ClipSpec(self.path, self.start, self.end)


@dataclass
class EditorState:
    """Dữ liệu của tab, giữ lại khi giao diện được dựng lại (vd. đổi ngôn ngữ)"""
    clips: List[Clip] = field(default_factory=list)
    selected: int = -1
    fade_in: str = "0"
    fade_out: str = "0"
    crossfade: str = "0"
    gain_db: float = 0.0
    normalize: bool = False
    out_format: str = "mp3"
    out_bitrate: str = "320"
    out_title: str = ""
    out_artist: str = ""
    keep_cover: bool = True
    last_export: str = ""
    exporting: bool = False
    cancel_event: threading.Event = field(default_factory=threading.Event)
    # File chờ đọc: một luồng duy nhất đọc lần lượt để danh sách giữ đúng thứ tự thêm vào
    load_queue: queue.Queue = field(default_factory=queue.Queue)
    load_lock: threading.Lock = field(default_factory=threading.Lock)
    loader: Optional[threading.Thread] = None


class WaveformView(tk.Canvas):
    """Vẽ dạng sóng của một đoạn, kéo để chọn khoảng [start, end], bấm để dời mốc gần nhất."""
    PAD = 10
    GRAB = 8

    def __init__(self, master, on_change, height=130):
        super().__init__(master, height=height, bg=WAVE_BG, highlightthickness=0)
        self.on_change = on_change
        self.clip: Optional[Clip] = None
        self.message = ""
        self._drag = None
        self._anchor = 0.0
        self._press_x = 0
        self._moved = False
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Motion>", self._on_hover)

    def set_clip(self, clip: Optional[Clip], message: str = ""):
        self.clip, self.message = clip, message
        self.redraw()

    # Toạ độ <-> thời gian
    def _usable_width(self) -> float:
        return max(1, self.winfo_width() - 2 * self.PAD)

    def _x_to_time(self, x: float) -> float:
        frac = min(1.0, max(0.0, (x - self.PAD) / self._usable_width()))
        return frac * self.clip.duration

    def _time_to_x(self, seconds: float) -> float:
        return self.PAD + (seconds / max(self.clip.duration, 1e-6)) * self._usable_width()

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if self.clip is None:
            self.create_text(w / 2, h / 2, text=self.message, fill=TEXT_COLOR, font=("", 11), width=w - 40)
            return

        clip = self.clip
        x0, x1 = self._time_to_x(clip.start), self._time_to_x(clip.end)
        self.create_rectangle(x0, 0, x1, h, fill=WAVE_SELECTION, width=0)

        mid, amp = h / 2, h / 2 - 16
        if clip.peaks:
            columns = self._columns(amp)
            self._draw_wave(columns, mid, WAVE_DIM)
            # Phần nằm trong vùng chọn vẽ sáng hơn
            self._draw_wave([c for c in columns if x0 <= c[0] <= x1], mid, WAVE_COLOR)
        elif clip.peaks is None:
            self.create_text(w / 2, mid, text=t("ed_wave_loading"), fill=TEXT_COLOR, font=("", 11))
        self.create_line(self.PAD, mid, w - self.PAD, mid, fill="#2A3340")

        for x, color in ((x0, START_COLOR), (x1, END_COLOR)):
            self.create_line(x, 0, x, h, fill=color, width=2)
            self.create_polygon(x - 6, 0, x + 6, 0, x, 9, fill=color, outline="")
        self.create_text(max(x0 + 4, 4), h - 4, text=at.format_time(clip.start), fill=START_COLOR,
                         anchor="sw", font=("", 9))
        self.create_text(min(x1 - 4, w - 4), h - 4, text=at.format_time(clip.end), fill=END_COLOR,
                         anchor="se", font=("", 9))
        self.create_text(self.PAD, 4, text="0:00", fill=TEXT_COLOR, anchor="nw", font=("", 9))
        self.create_text(w - self.PAD, 4, text=at.format_time(clip.duration, precise=False), fill=TEXT_COLOR,
                         anchor="ne", font=("", 9))
        self.create_text(w / 2, 4, text=t("ed_wave_hint"), fill=TEXT_COLOR, anchor="n", font=("", 8))

    def _columns(self, amp: float):
        """(x, chiều cao) cho mỗi cột pixel, lấy đỉnh lớn nhất trong các khoảng peaks thuộc cột đó"""
        peaks = self.clip.peaks
        n, usable = len(peaks), int(self._usable_width())
        columns = []
        for px in range(usable):
            i0 = px * n // usable
            i1 = max(i0 + 1, (px + 1) * n // usable)
            columns.append((self.PAD + px, max(peaks[i0:i1]) * amp + 0.5))
        return columns

    def _draw_wave(self, columns, mid: float, color: str):
        if len(columns) < 2:
            return
        points = [v for x, p in columns for v in (x, mid - p)]
        points += [v for x, p in reversed(columns) for v in (x, mid + p)]
        self.create_polygon(points, fill=color, outline="")

    def show_playhead(self, seconds: Optional[float]):
        self.delete("playhead")
        if self.clip is not None and seconds is not None:
            x = self._time_to_x(seconds)
            self.create_line(x, 0, x, self.winfo_height(), fill=PLAYHEAD_COLOR, width=2, tags="playhead")

    # Chuột
    def _near_marker(self, x) -> Optional[str]:
        if self.clip is None:
            return None
        if abs(x - self._time_to_x(self.clip.start)) <= self.GRAB:
            return "start"
        if abs(x - self._time_to_x(self.clip.end)) <= self.GRAB:
            return "end"
        return None

    def _on_hover(self, event):
        self.configure(cursor="sb_h_double_arrow" if self._near_marker(event.x) else "crosshair")

    def _on_press(self, event):
        if self.clip is None:
            return
        self._press_x, self._moved = event.x, False
        self._drag = self._near_marker(event.x) or "new"
        self._anchor = self._x_to_time(event.x)

    def _on_drag(self, event):
        if self.clip is None or not self._drag:
            return
        if abs(event.x - self._press_x) > 3:
            self._moved = True
        if not self._moved:
            return
        clip, pos = self.clip, self._x_to_time(event.x)
        if self._drag == "start":
            clip.start = min(pos, clip.end - MIN_LENGTH)
        elif self._drag == "end":
            clip.end = max(pos, clip.start + MIN_LENGTH)
        else:
            clip.start, clip.end = sorted((self._anchor, pos))
        self._clamp()
        self.redraw()
        self.on_change(False)

    def _on_release(self, event):
        if self.clip is None or not self._drag:
            return
        clip = self.clip
        if not self._moved:
            pos = self._x_to_time(event.x)
            if self._drag == "start" or (self._drag == "new" and abs(pos - clip.start) <= abs(pos - clip.end)):
                clip.start = min(pos, clip.end - MIN_LENGTH)
            else:
                clip.end = max(pos, clip.start + MIN_LENGTH)
        elif clip.end - clip.start < MIN_LENGTH:
            clip.end = clip.start + MIN_LENGTH
        self._drag = None
        self._clamp()
        self.redraw()
        self.on_change(True)

    def _clamp(self):
        clip = self.clip
        clip.start = min(max(0.0, clip.start), max(0.0, clip.duration - MIN_LENGTH))
        clip.end = min(clip.duration, max(clip.end, clip.start + MIN_LENGTH))


class EditorTab:
    def __init__(self, master, app):
        self.app = app
        self.state: EditorState = app.editor_state
        self.player: at.AudioPlayer = app.player
        self._playhead_job = None
        self._build(master)
        self.select(self.state.selected)
        self._update_export_ui()

    def _post(self, method: str, *args):
        """Gọi method của tab hiện tại trên luồng giao diện (tab có thể đã được dựng lại khi đổi ngôn ngữ)"""
        self.app.post(self.app.call_editor, method, *args)

    # ---------- Giao diện ----------
    def _build(self, master):
        s = self.state
        bold = ctk.CTkFont(size=13, weight="bold")
        small = ctk.CTkFont(size=12)

        # 1. Danh sách đoạn
        clips_frame = ctk.CTkFrame(master, corner_radius=10)
        clips_frame.pack(fill="x", padx=8, pady=(2, 4))
        header = ctk.CTkFrame(clips_frame, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(6, 2))
        ctk.CTkLabel(header, text=t("ed_clips_title"), font=bold).pack(side="left")
        ctk.CTkButton(header, text=t("ed_clear"), width=90, height=28, fg_color="#374151", hover_color="#4B5563",
                      command=self.clear_clips).pack(side="right")
        ctk.CTkButton(header, text=t("ed_add_files"), width=130, height=28,
                      command=self._ask_add_files).pack(side="right", padx=(0, 8))
        self.clip_list = ctk.CTkScrollableFrame(clips_frame, height=70, fg_color="transparent")
        # Thanh cuộn của CustomTkinter tự đòi cao tối thiểu 200px, làm danh sách cao hơn mức đặt
        scrollbar = getattr(self.clip_list, "_scrollbar", None)
        if scrollbar is not None:
            scrollbar.configure(height=0)
        self.clip_list.pack(fill="x", padx=8, pady=(0, 6))

        # 2. Dạng sóng + điểm cắt
        wave_frame = ctk.CTkFrame(master, corner_radius=10)
        wave_frame.pack(fill="x", padx=8, pady=4)
        scaling = ctk.ScalingTracker.get_widget_scaling(wave_frame)
        self.waveform = WaveformView(wave_frame, on_change=self._on_wave_changed, height=round(96 * scaling))
        self.waveform.pack(fill="x", padx=12, pady=(10, 4))

        ctrl = ctk.CTkFrame(wave_frame, fg_color="transparent")
        ctrl.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(ctrl, text=t("ed_start"), font=small, text_color=START_COLOR).pack(side="left")
        self.start_entry = ctk.CTkEntry(ctrl, width=80, height=28)
        self.start_entry.pack(side="left", padx=(4, 12))
        ctk.CTkLabel(ctrl, text=t("ed_end"), font=small, text_color=END_COLOR).pack(side="left")
        self.end_entry = ctk.CTkEntry(ctrl, width=80, height=28)
        self.end_entry.pack(side="left", padx=(4, 12))
        for entry in (self.start_entry, self.end_entry):
            entry.bind("<Return>", lambda e: self._apply_time_entries())
            entry.bind("<FocusOut>", lambda e: self._apply_time_entries())
        self.length_label = ctk.CTkLabel(ctrl, text="", font=small, text_color="gray75")
        self.length_label.pack(side="left", padx=(0, 12))
        ctk.CTkButton(ctrl, text=t("ed_select_all"), width=80, height=28, fg_color="#374151",
                      hover_color="#4B5563", command=self._select_whole).pack(side="left")
        self.btn_stop = ctk.CTkButton(ctrl, text=t("ed_stop"), width=80, height=28, fg_color="#757575",
                                      hover_color="#616161", command=self.stop_preview)
        self.btn_stop.pack(side="right")
        self.btn_preview = ctk.CTkButton(ctrl, text=t("ed_preview"), width=130, height=28, fg_color="#2E7D32",
                                         hover_color="#1B5E20", command=self._preview)
        self.btn_preview.pack(side="right", padx=(0, 6))

        # 3. Hiệu ứng | Xuất file (2 cột) + hàng nút xuất
        bottom = ctk.CTkFrame(master, corner_radius=10)
        bottom.pack(fill="x", padx=8, pady=(4, 2))
        bottom.grid_columnconfigure((0, 1), weight=1, uniform="col")

        fx = ctk.CTkFrame(bottom, fg_color="transparent")
        fx.grid(row=0, column=0, sticky="nsew", padx=(14, 6), pady=(8, 0))
        fx.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(fx, text=t("ed_effects_title"), font=bold).grid(row=0, column=0, columnspan=4, sticky="w")
        self.fade_in_entry = self._entry(fx, 1, 0, t("ed_fade_in"), s.fade_in)
        self.fade_out_entry = self._entry(fx, 1, 2, t("ed_fade_out"), s.fade_out)
        ctk.CTkLabel(fx, text=t("ed_crossfade"), font=small).grid(row=2, column=0, columnspan=3, sticky="w", pady=2)
        self.crossfade_entry = ctk.CTkEntry(fx, width=56, height=28)
        self.crossfade_entry.insert(0, s.crossfade)
        self.crossfade_entry.grid(row=2, column=3, sticky="w", padx=(4, 0), pady=2)
        self.crossfade_entry.bind("<KeyRelease>", lambda e: self._update_total())
        self.volume_label = ctk.CTkLabel(fx, text=t("ed_volume", db=s.gain_db), font=small)
        self.volume_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)
        self.volume_slider = ctk.CTkSlider(fx, from_=-12, to=12, number_of_steps=24, command=self._on_volume)
        self.volume_slider.set(s.gain_db)
        self.volume_slider.grid(row=3, column=2, columnspan=2, sticky="ew", padx=(4, 0), pady=2)
        self.normalize_check = ctk.CTkCheckBox(fx, text=t("ed_normalize"), font=small)
        self.normalize_check.select() if s.normalize else self.normalize_check.deselect()
        self.normalize_check.grid(row=4, column=0, columnspan=4, sticky="w", pady=(4, 2))

        out = ctk.CTkFrame(bottom, fg_color="transparent")
        out.grid(row=0, column=1, sticky="nsew", padx=(6, 14), pady=(8, 0))
        out.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(out, text=t("ed_output_title"), font=bold).grid(row=0, column=0, columnspan=2, sticky="w")
        self.out_format_seg = ctk.CTkSegmentedButton(out, values=list(FORMAT_LABELS.values()),
                                                     command=self._on_out_format)
        self.out_format_seg.set(FORMAT_LABELS[s.out_format])
        self.out_format_seg.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        quality = ctk.CTkFrame(out, fg_color="transparent")
        quality.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)
        self.out_bitrate_seg = ctk.CTkSegmentedButton(quality, values=list(BITRATE_LABELS.values()),
                                                      command=lambda v: setattr(s, "out_bitrate", v.split()[0]))
        self.out_bitrate_seg.set(BITRATE_LABELS[s.out_bitrate])
        self.out_bitrate_seg.pack(side="left")
        self.cover_check = ctk.CTkCheckBox(quality, text=t("ed_keep_cover"), font=small)
        self.cover_check.select() if s.keep_cover else self.cover_check.deselect()
        self.cover_check.pack(side="left", padx=(12, 0))
        self.title_entry = self._entry(out, 3, 0, t("ed_title"), s.out_title, width=None)
        self.artist_entry = self._entry(out, 4, 0, t("ed_artist"), s.out_artist, width=None)

        actions = ctk.CTkFrame(bottom, fg_color="transparent")
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(8, 10))
        self.btn_export = ctk.CTkButton(actions, text=t("ed_export"), width=150, height=34, font=bold,
                                        fg_color="#1976D2", hover_color="#1565C0", command=self._export)
        self.btn_export.pack(side="left", padx=(0, 6))
        self.btn_cancel_export = ctk.CTkButton(actions, text=t("ed_cancel_export"), width=70, height=34,
                                               fg_color="#757575", hover_color="#616161",
                                               command=self.state.cancel_event.set)
        self.btn_cancel_export.pack(side="left", padx=(0, 10))
        self.btn_play_export = ctk.CTkButton(actions, text=t("ed_play_export"), width=140, height=34,
                                             fg_color="#2E7D32", hover_color="#1B5E20",
                                             command=lambda: play_audio_file(self.state.last_export))
        self.btn_play_export.pack(side="right")
        self.btn_open_export = ctk.CTkButton(actions, text=t("ed_open_folder"), width=110, height=34,
                                             fg_color="#374151", hover_color="#4B5563",
                                             command=lambda: open_path_in_explorer(self.state.last_export))
        self.btn_open_export.pack(side="right", padx=(0, 6))
        # Giữa hàng nút: dòng trạng thái (tổng thời lượng / tiến trình / kết quả) và thanh tiến trình
        progress = ctk.CTkFrame(actions, fg_color="transparent")
        progress.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.total_label = ctk.CTkLabel(progress, text="", font=ctk.CTkFont(size=11), text_color="gray75",
                                        anchor="w", height=16)
        self.total_label.pack(fill="x")
        self.export_bar = ctk.CTkProgressBar(progress, height=6)
        self.export_bar.set(0)
        self.export_bar.pack(fill="x", pady=(2, 0))
        self._on_out_format(FORMAT_LABELS[s.out_format])

    @staticmethod
    def _entry(master, row, column, label, value, width=56):
        ctk.CTkLabel(master, text=label, font=ctk.CTkFont(size=12)).grid(row=row, column=column, sticky="w", pady=2)
        entry = ctk.CTkEntry(master, height=28, **({"width": width} if width else {}))
        entry.insert(0, value)
        entry.grid(row=row, column=column + 1, sticky="w" if width else "ew", padx=(4, 12 if width else 0), pady=2)
        return entry

    # ---------- Danh sách đoạn ----------
    def _ask_add_files(self):
        paths = filedialog.askopenfilenames(
            parent=self.app,
            initialdir=self.app.settings["download_dir"],
            filetypes=[(t("ed_audio_files"), AUDIO_PATTERNS), (t("ed_all_files"), "*.*")],
        )
        if paths:
            self.add_files(list(paths))

    def add_files(self, paths: List[str]):
        """Thêm file vào cuối danh sách: đọc thông tin và dạng sóng trong luồng nền."""
        s = self.state
        self.set_status(t("ed_loading"))
        for path in paths:
            s.load_queue.put(path)
        with s.load_lock:
            if s.loader is None:
                s.loader = threading.Thread(target=self._load_worker, daemon=True, name="EditorLoader")
                s.loader.start()

    def _load_worker(self):
        s = self.state
        errors = []
        while True:
            try:
                path = s.load_queue.get_nowait()
            except queue.Empty:
                with s.load_lock:
                    if s.load_queue.empty():
                        s.loader = None
                        break
                continue
            try:
                info = at.probe(path)
            except Exception as e:
                errors.append(t("ed_err_load", name=os.path.basename(path), error=e))
                continue
            clip = Clip(path=path, duration=info.duration, end=info.duration, title=info.title,
                        artist=info.artist, has_cover=info.has_cover)
            self._post("on_clip_added", clip)
            try:
                clip.peaks = at.load_peaks(path, info.duration)
            except Exception:
                clip.peaks = []
            self._post("on_peaks_ready", clip)
        self._post("on_add_finished", errors)

    def on_clip_added(self, clip: Clip):
        s = self.state
        s.clips.append(clip)
        if len(s.clips) == 1:
            # Điền sẵn tên bài / ca sĩ từ đoạn đầu tiên
            if not self.title_entry.get().strip():
                self.title_entry.insert(0, clip.title or os.path.splitext(clip.name)[0])
            if not self.artist_entry.get().strip() and clip.artist:
                self.artist_entry.insert(0, clip.artist)
        self.select(len(s.clips) - 1)

    def on_peaks_ready(self, clip: Clip):
        if self._selected_clip() is clip:
            self.waveform.redraw()

    def on_add_finished(self, errors: List[str]):
        self.set_status("")
        if errors:
            messagebox.showerror(t("dlg_error_title"), "\n".join(errors), parent=self.app)

    def refresh_clip_list(self):
        for child in self.clip_list.winfo_children():
            child.destroy()
        s = self.state
        if not s.clips:
            ctk.CTkLabel(self.clip_list, text=t("ed_empty"), font=ctk.CTkFont(size=12),
                         text_color="gray60").pack(pady=14)
        for i, clip in enumerate(s.clips):
            selected = i == s.selected
            row = ctk.CTkFrame(self.clip_list, corner_radius=6, fg_color="#1F3A56" if selected else "#1E293B")
            row.pack(fill="x", padx=4, pady=2)
            text = (f"{i + 1}. {clip.name[:60]}   [{at.format_time(clip.start)} → {at.format_time(clip.end)}]"
                    f"   ({at.format_time(clip.end - clip.start)})")
            label = ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12, weight="bold" if selected else "normal"),
                                 anchor="w", cursor="hand2")
            label.pack(side="left", fill="x", expand=True, padx=10, pady=3)
            label.bind("<Button-1>", lambda e, idx=i: self.select(idx))
            for symbol, command in (("▲", lambda idx=i: self._move(idx, -1)),
                                    ("▼", lambda idx=i: self._move(idx, 1)),
                                    ("✖", lambda idx=i: self._remove(idx))):
                ctk.CTkButton(row, text=symbol, width=28, height=24, fg_color="#374151", hover_color="#4B5563",
                              command=command).pack(side="left", padx=2, pady=3)
        self._update_total()

    def select(self, index: int):
        s = self.state
        s.selected = index if 0 <= index < len(s.clips) else (len(s.clips) - 1 if s.clips else -1)
        self.stop_preview()
        self.refresh_clip_list()
        clip = self._selected_clip()
        self.waveform.set_clip(clip, t("ed_empty"))
        self._update_time_entries()

    def _selected_clip(self) -> Optional[Clip]:
        s = self.state
        return s.clips[s.selected] if 0 <= s.selected < len(s.clips) else None

    def _move(self, index: int, delta: int):
        s, target = self.state, index + delta
        if 0 <= target < len(s.clips):
            s.clips[index], s.clips[target] = s.clips[target], s.clips[index]
            s.selected = target if s.selected == index else (index if s.selected == target else s.selected)
            self.refresh_clip_list()

    def _remove(self, index: int):
        s = self.state
        del s.clips[index]
        self.select(max(0, min(s.selected if s.selected < index else s.selected - 1, len(s.clips) - 1)))

    def clear_clips(self):
        self.state.clips.clear()
        self.select(-1)

    # ---------- Điểm cắt ----------
    def _on_wave_changed(self, final: bool):
        self._update_time_entries()
        if final:
            self.refresh_clip_list()

    def _update_time_entries(self):
        clip = self._selected_clip()
        for entry, value in ((self.start_entry, clip.start if clip else None),
                             (self.end_entry, clip.end if clip else None)):
            entry.delete(0, "end")
            if value is not None:
                entry.insert(0, at.format_time(value))
        self.length_label.configure(
            text=t("ed_length", length=at.format_time(clip.end - clip.start)) if clip else "")

    def _apply_time_entries(self):
        clip = self._selected_clip()
        if clip is None:
            return
        try:
            start = at.parse_time(self.start_entry.get())
            end = at.parse_time(self.end_entry.get())
        except ValueError as e:
            self.set_status(t("ed_err_time", value=e), "#EF5350")
            self._update_time_entries()
            return
        start = min(max(0.0, start), clip.duration - MIN_LENGTH)
        clip.start, clip.end = start, min(clip.duration, max(end, start + MIN_LENGTH))
        self.set_status("")
        self.waveform.redraw()
        self._update_time_entries()
        self.refresh_clip_list()

    def _select_whole(self):
        clip = self._selected_clip()
        if clip:
            clip.start, clip.end = 0.0, clip.duration
            self.waveform.redraw()
            self._on_wave_changed(True)

    # ---------- Nghe thử ----------
    def _preview(self):
        clip = self._selected_clip()
        if clip is None:
            return
        if not at.AudioPlayer.available():
            # Không có trình phát dòng lệnh: xuất đoạn ra file rồi mở bằng trình phát mặc định
            messagebox.showinfo(t("dlg_notice_title"), t("ed_err_player"), parent=self.app)
            return
        spec = clip.spec()
        wav = os.path.join(self.app.temp_dir, "preview.wav")
        self.stop_preview()

        def worker():
            try:
                at.render_preview(spec, wav)
            except Exception as e:
                self._post("set_status", t("ed_err_load", name=clip.name, error=e), "#EF5350")
                return
            self._post("play_preview", wav, spec)

        threading.Thread(target=worker, daemon=True, name="EditorPreview").start()

    def play_preview(self, wav: str, spec: at.ClipSpec):
        try:
            self.player.play(wav, spec.length)
        except at.AudioToolError:
            messagebox.showinfo(t("dlg_notice_title"), t("ed_err_player"), parent=self.app)
            return
        self._tick_playhead(spec.start)

    def _tick_playhead(self, offset: float):
        pos = self.player.position()
        self.waveform.show_playhead(None if pos is None else offset + pos)
        self._playhead_job = self.waveform.after(50, self._tick_playhead, offset) if pos is not None else None

    def stop_preview(self):
        self.player.stop()
        if self._playhead_job:
            self.waveform.after_cancel(self._playhead_job)
            self._playhead_job = None
        self.waveform.show_playhead(None)

    # ---------- Hiệu ứng & xuất file ----------
    def _on_volume(self, value):
        self.state.gain_db = round(float(value))
        self.volume_label.configure(text=t("ed_volume", db=self.state.gain_db))

    def _on_out_format(self, label: str):
        fmt = next(k for k, v in FORMAT_LABELS.items() if v == label)
        self.state.out_format = fmt
        self.out_bitrate_seg.configure(state="normal" if fmt == "mp3" else "disabled")
        self.cover_check.configure(state="normal" if fmt in at.COVER_FORMATS else "disabled")

    def collect_state(self):
        """Lưu giá trị đang nhập vào state (gọi trước khi dựng lại giao diện)"""
        s = self.state
        s.fade_in, s.fade_out = self.fade_in_entry.get(), self.fade_out_entry.get()
        s.crossfade = self.crossfade_entry.get()
        s.normalize = bool(self.normalize_check.get())
        s.out_title, s.out_artist = self.title_entry.get(), self.artist_entry.get()
        s.keep_cover = bool(self.cover_check.get())

    def _read_seconds(self, entry) -> float:
        text = entry.get().strip() or "0"
        try:
            value = at.parse_time(text)
        except ValueError:
            raise ValueError(t("ed_err_number", value=text))
        return value

    def _update_total(self):
        if self.state.exporting:
            return
        specs = [c.spec() for c in self.state.clips]
        try:
            crossfade = self._read_seconds(self.crossfade_entry)
        except ValueError:
            crossfade = 0.0
        text = t("ed_total", total=at.format_time(at.output_duration(specs, crossfade))) if specs else ""
        self.total_label.configure(text=text, text_color="gray75")

    def _export(self):
        s = self.state
        self.collect_state()
        if not s.clips:
            messagebox.showwarning(t("dlg_notice_title"), t("ed_err_no_clips"), parent=self.app)
            return
        for clip in s.clips:
            if clip.end - clip.start < MIN_LENGTH:
                messagebox.showerror(t("dlg_error_title"), t("ed_err_range", name=clip.name), parent=self.app)
                return
        try:
            fade_in = self._read_seconds(self.fade_in_entry)
            fade_out = self._read_seconds(self.fade_out_entry)
            crossfade = self._read_seconds(self.crossfade_entry)
        except ValueError as e:
            messagebox.showerror(t("dlg_error_title"), str(e), parent=self.app)
            return

        first = s.clips[0]
        base = s.out_title.strip() or os.path.splitext(first.name)[0]
        out_path = filedialog.asksaveasfilename(
            parent=self.app,
            initialdir=self.app.settings["download_dir"],
            initialfile=f"{base} (edit).{s.out_format}",
            defaultextension=f".{s.out_format}",
            filetypes=[(FORMAT_LABELS[s.out_format], f"*.{s.out_format}")],
        )
        if not out_path:
            return

        specs = [c.spec() for c in s.clips]
        try:
            cmd = at.build_export_command(
                specs, out_path, fmt=s.out_format, bitrate=s.out_bitrate, fade_in=fade_in, fade_out=fade_out,
                gain_db=s.gain_db, crossfade=crossfade, normalize=s.normalize, title=s.out_title.strip(),
                artist=s.out_artist.strip(), keep_cover=s.keep_cover and first.has_cover,
            )
        except at.AudioToolError as e:
            messagebox.showerror(t("dlg_error_title"), t("ed_err_export", error=e), parent=self.app)
            return

        total = at.output_duration(specs, crossfade)
        s.exporting = True
        s.cancel_event.clear()
        self._update_export_ui()

        def worker():
            try:
                at.run_export(cmd, total, lambda p: self._post("on_export_progress", p),
                              s.cancel_event)
                self._post("on_export_finished", out_path, None)
            except Exception as e:
                self._post("on_export_finished", None, e)

        threading.Thread(target=worker, daemon=True, name="EditorExport").start()

    def on_export_progress(self, fraction: float):
        self.export_bar.set(fraction)
        self.total_label.configure(text=t("ed_exporting", percent=fraction * 100), text_color="#90CAF9")

    def on_export_finished(self, out_path: Optional[str], error: Optional[Exception]):
        s = self.state
        s.exporting = False
        if out_path:
            s.last_export = out_path
        self._update_export_ui()
        if out_path:
            self.export_bar.set(1.0)
            self.total_label.configure(text=t("ed_export_done", path=os.path.basename(out_path)),
                                     text_color="#66BB6A")
        elif s.cancel_event.is_set():
            self.export_bar.set(0)
            self.total_label.configure(text=t("ed_export_cancelled"), text_color="#FFA726")
        else:
            self.export_bar.set(0)
            self.total_label.configure(text=t("ed_err_export", error=error), text_color="#EF5350")
            messagebox.showerror(t("dlg_error_title"), t("ed_err_export", error=error), parent=self.app)

    def _update_export_ui(self):
        s = self.state
        self.btn_export.configure(state="disabled" if s.exporting else "normal")
        self.btn_cancel_export.configure(state="normal" if s.exporting else "disabled")
        has_result = bool(s.last_export) and os.path.exists(s.last_export) and not s.exporting
        for button in (self.btn_open_export, self.btn_play_export):
            button.configure(state="normal" if has_result else "disabled")

    def set_status(self, text: str, color: str = "gray75"):
        if not self.state.exporting:
            if text:
                self.total_label.configure(text=text, text_color=color)
            else:
                self._update_total()
