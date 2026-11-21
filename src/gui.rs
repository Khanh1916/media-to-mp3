use crate::audio::{self, AudioInfo, ClipSpec};
use crate::clipboard::ClipboardMonitor;
use crate::config::{load_settings, save_settings, Settings};
use crate::downloader::{get_ffmpeg_path, MediaDownloader};
use crate::i18n::{self, t};
use crate::platform::{open_path_in_explorer, play_audio_file};
use crate::queue::{
    is_active_status, is_finished_status, DownloadQueue, QueueItem, CANCELLED, DONE, ERROR,
};
use crate::version::VERSION;
use arboard::Clipboard;
use eframe::egui::{self, Color32, Pos2, Rounding, Sense, Stroke, Vec2};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};

#[derive(PartialEq, Clone, Copy)]
pub enum ActiveTab {
    Download,
    Editor,
}

pub struct MediaToMp3App {
    // Navigation
    tab: ActiveTab,

    // Settings
    settings: Settings,
    output_dir: PathBuf,

    // Tab 1: Download Queue State
    url_input: String,
    selected_format: String,
    selected_bitrate: String,
    embed_thumbnail: bool,
    parse_metadata: bool,
    auto_clipboard: bool,
    queue: Arc<DownloadQueue>,
    clipboard_monitor: Option<ClipboardMonitor>,

    // Notification toast
    toast_msg: Option<(String, Instant, bool)>,

    // Tab 2: Audio Editor State
    editor_file: Option<PathBuf>,
    audio_info: Option<AudioInfo>,
    peaks: Vec<f32>,
    is_loading_audio: bool,
    clip_start: f64,
    clip_end: f64,
    start_str: String,
    end_str: String,
    fade_in: f64,
    fade_out: f64,
    crossfade: f64,
    gain_db: f64,
    normalize: bool,
    export_fmt: String,
    export_bitrate: String,
    export_title: String,
    export_artist: String,
    keep_cover: bool,
    export_progress: Option<f64>,
    cancel_export_flag: Arc<AtomicBool>,
}

impl MediaToMp3App {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        setup_custom_fonts(&cc.egui_ctx);
        setup_custom_theme(&cc.egui_ctx);

        let settings = load_settings(None::<&Path>);
        i18n::set_language(&settings.language);

        let out_dir = if settings.download_dir.is_empty() {
            crate::downloader::default_download_dir()
        } else {
            PathBuf::from(&settings.download_dir)
        };

        let downloader = MediaDownloader::new(Some(out_dir.clone()));
        let queue = Arc::new(DownloadQueue::new(downloader, None));

        let auto_clip = settings.clipboard_monitor;
        let mut app = Self {
            tab: ActiveTab::Download,
            settings: settings.clone(),
            output_dir: out_dir,
            url_input: String::new(),
            selected_format: settings.format,
            selected_bitrate: settings.bitrate,
            embed_thumbnail: settings.embed_thumbnail,
            parse_metadata: settings.parse_metadata,
            auto_clipboard: auto_clip,
            queue,
            clipboard_monitor: None,
            toast_msg: None,

            editor_file: None,
            audio_info: None,
            peaks: Vec::new(),
            is_loading_audio: false,
            clip_start: 0.0,
            clip_end: 0.0,
            start_str: "0:00.0".to_string(),
            end_str: "0:00.0".to_string(),
            fade_in: 0.0,
            fade_out: 0.0,
            crossfade: 0.0,
            gain_db: 0.0,
            normalize: false,
            export_fmt: "mp3".to_string(),
            export_bitrate: "320".to_string(),
            export_title: String::new(),
            export_artist: String::new(),
            keep_cover: true,
            export_progress: None,
            cancel_export_flag: Arc::new(AtomicBool::new(false)),
        };

        if auto_clip {
            app.start_clipboard_monitor();
        }

        app
    }

    fn show_toast(&mut self, msg: String, is_error: bool) {
        self.toast_msg = Some((msg, Instant::now(), is_error));
    }

    fn start_clipboard_monitor(&mut self) {
        let q = self.queue.clone();
        self.clipboard_monitor = Some(ClipboardMonitor::new(
            move |url, _platform| {
                let _ = q.add(&url);
            },
            Duration::from_millis(800),
        ));
    }

    fn stop_clipboard_monitor(&mut self) {
        self.clipboard_monitor = None;
    }

    fn save_current_settings(&mut self) {
        self.settings.download_dir = self.output_dir.to_string_lossy().to_string();
        self.settings.format = self.selected_format.clone();
        self.settings.bitrate = self.selected_bitrate.clone();
        self.settings.embed_thumbnail = self.embed_thumbnail;
        self.settings.parse_metadata = self.parse_metadata;
        self.settings.clipboard_monitor = self.auto_clipboard;
        self.settings.language = i18n::get_language();
        let _ = save_settings(&self.settings, None::<&Path>);
    }

    pub fn load_audio_for_editor(&mut self, path: PathBuf) {
        self.is_loading_audio = true;
        self.editor_file = Some(path.clone());

        match audio::probe(&path) {
            Ok(info) => {
                let dur = info.duration;
                self.clip_start = 0.0;
                self.clip_end = dur;
                self.start_str = "0:00.0".to_string();
                self.end_str = audio::format_time(dur, true);
                self.export_title = info.title.clone();
                self.export_artist = info.artist.clone();
                self.audio_info = Some(info);

                match audio::load_peaks(&path, dur, 160) {
                    Ok(pks) => self.peaks = pks,
                    Err(_) => self.peaks = vec![0.5; 160],
                }
                self.tab = ActiveTab::Editor;
                self.show_toast(
                    format!(
                        "Loaded: {}",
                        path.file_name().unwrap_or_default().to_string_lossy()
                    ),
                    false,
                );
            }
            Err(e) => {
                self.show_toast(format!("Failed to probe audio: {}", e), true);
            }
        }
        self.is_loading_audio = false;
    }
}

fn setup_custom_fonts(ctx: &egui::Context) {
    let mut fonts = egui::FontDefinitions::default();

    let candidates = [
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ];

    for path in &candidates {
        if let Ok(bytes) = std::fs::read(path) {
            fonts.font_data.insert(
                "system_unicode".to_owned(),
                egui::FontData::from_owned(bytes),
            );
            fonts
                .families
                .entry(egui::FontFamily::Proportional)
                .or_default()
                .insert(0, "system_unicode".to_owned());
            break;
        }
    }

    ctx.set_fonts(fonts);
}

fn setup_custom_theme(ctx: &egui::Context) {
    let mut visuals = egui::Visuals::dark();

    // Palette: Slate / Obsidian Dark
    visuals.override_text_color = Some(Color32::from_rgb(241, 245, 249));
    visuals.panel_fill = Color32::from_rgb(18, 21, 28);
    visuals.window_fill = Color32::from_rgb(15, 17, 23);
    visuals.faint_bg_color = Color32::from_rgb(24, 28, 38);
    visuals.extreme_bg_color = Color32::from_rgb(12, 14, 18);

    // Widgets styling
    visuals.widgets.noninteractive.bg_fill = Color32::from_rgb(26, 30, 42);
    visuals.widgets.noninteractive.bg_stroke = Stroke::new(1.0_f32, Color32::from_rgb(45, 52, 70));
    visuals.widgets.noninteractive.rounding = Rounding::same(6.0);

    visuals.widgets.inactive.bg_fill = Color32::from_rgb(28, 33, 46);
    visuals.widgets.inactive.bg_stroke = Stroke::new(1.0_f32, Color32::from_rgb(48, 56, 76));
    visuals.widgets.inactive.rounding = Rounding::same(6.0);

    visuals.widgets.hovered.bg_fill = Color32::from_rgb(38, 45, 62);
    visuals.widgets.hovered.bg_stroke = Stroke::new(1.0_f32, Color32::from_rgb(99, 102, 241));
    visuals.widgets.hovered.rounding = Rounding::same(6.0);

    visuals.widgets.active.bg_fill = Color32::from_rgb(99, 102, 241); // Accent Indigo
    visuals.widgets.active.bg_stroke = Stroke::new(1.0_f32, Color32::from_rgb(129, 140, 248));
    visuals.widgets.active.rounding = Rounding::same(6.0);

    ctx.set_visuals(visuals);
}

impl eframe::App for MediaToMp3App {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Request repaint if active downloads are running
        if self.queue.is_busy() || self.export_progress.is_some() {
            ctx.request_repaint_after(Duration::from_millis(150));
        }

        // Top Navigation Bar
        egui::TopBottomPanel::top("top_header").show(ctx, |ui| {
            ui.add_space(8.0);
            ui.horizontal(|ui| {
                ui.add_space(4.0);
                ui.heading("Media to MP3");
                ui.colored_label(Color32::from_rgb(148, 163, 184), format!("v{}", VERSION));

                ui.add_space(24.0);

                // Tab Switcher
                let dl_btn = ui.selectable_label(
                    self.tab == ActiveTab::Download,
                    format!("↓ {}", t("tab_download", &[])),
                );
                if dl_btn.clicked() {
                    self.tab = ActiveTab::Download;
                }

                let ed_btn = ui.selectable_label(
                    self.tab == ActiveTab::Editor,
                    format!("✂ {}", t("tab_editor", &[])),
                );
                if ed_btn.clicked() {
                    self.tab = ActiveTab::Editor;
                }

                // Right-aligned controls
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    ui.add_space(4.0);
                    // Language switch button
                    let cur_lang = i18n::get_language();
                    let lang_label = if cur_lang == "vi" {
                        "VI | Tiếng Việt"
                    } else {
                        "EN | English"
                    };
                    if ui.button(lang_label).clicked() {
                        if cur_lang == "vi" {
                            i18n::set_language("en");
                        } else {
                            i18n::set_language("vi");
                        }
                        self.save_current_settings();
                    }

                    // Open save directory button
                    if ui
                        .button(format!("📁 {}", t("btn_open_folder", &[])))
                        .clicked()
                    {
                        open_path_in_explorer(&self.output_dir);
                    }
                });
            });
            ui.add_space(8.0);
        });

        // Bottom Status Bar
        egui::TopBottomPanel::bottom("bottom_status").show(ctx, |ui| {
            ui.add_space(4.0);
            ui.horizontal(|ui| {
                ui.add_space(6.0);
                // FFmpeg indicator
                if get_ffmpeg_path().is_some() {
                    ui.colored_label(Color32::from_rgb(34, 197, 94), "● FFmpeg: Ready");
                } else {
                    ui.colored_label(Color32::from_rgb(239, 68, 68), "● FFmpeg: Missing");
                }

                ui.separator();

                // Clipboard monitor indicator
                if self.auto_clipboard {
                    ui.colored_label(Color32::from_rgb(34, 197, 94), "● Clipboard: Active");
                } else {
                    ui.colored_label(Color32::from_rgb(148, 163, 184), "○ Clipboard: Off");
                }

                // Toast notification
                if let Some((ref msg, time, is_err)) = self.toast_msg {
                    if time.elapsed() < Duration::from_secs(4) {
                        ui.separator();
                        let color = if is_err {
                            Color32::from_rgb(239, 68, 68)
                        } else {
                            Color32::from_rgb(34, 197, 94)
                        };
                        ui.colored_label(color, msg);
                    }
                }

                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    ui.add_space(6.0);
                    let folder_btn = ui.small_button(format!("📁 {}", self.output_dir.display()));
                    if folder_btn.clicked() {
                        if let Some(folder) = rfd::FileDialog::new()
                            .set_directory(&self.output_dir)
                            .pick_folder()
                        {
                            self.output_dir = folder;
                            self.save_current_settings();
                        }
                    }
                });
            });
            ui.add_space(4.0);
        });

        // Central Panel
        egui::CentralPanel::default().show(ctx, |ui| match self.tab {
            ActiveTab::Download => self.render_download_tab(ui),
            ActiveTab::Editor => self.render_editor_tab(ui),
        });
    }
}

impl MediaToMp3App {
    fn render_download_tab(&mut self, ui: &mut egui::Ui) {
        ui.add_space(4.0);

        // Card 1: Input URL & Format Configuration
        egui::Frame::group(ui.style())
            .fill(Color32::from_rgb(24, 28, 38))
            .rounding(Rounding::same(8.0))
            .inner_margin(12.0)
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.label(t("url_label", &[]));
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        if ui
                            .checkbox(&mut self.auto_clipboard, t("switch_clipboard", &[]))
                            .changed()
                        {
                            if self.auto_clipboard {
                                self.start_clipboard_monitor();
                            } else {
                                self.stop_clipboard_monitor();
                            }
                            self.save_current_settings();
                        }
                    });
                });

                ui.add_space(4.0);

                // URL Input Bar
                ui.horizontal(|ui| {
                    let text_edit = ui.add(
                        egui::TextEdit::singleline(&mut self.url_input)
                            .hint_text(t("url_placeholder", &[]))
                            .desired_width(ui.available_width() - 210.0),
                    );

                    // Paste button
                    if ui.button(t("btn_paste", &[])).clicked() {
                        if let Ok(mut cb) = Clipboard::new() {
                            if let Ok(text) = cb.get_text() {
                                self.url_input = text.trim().to_string();
                            }
                        }
                    }

                    // Add to Queue Button
                    let add_btn = ui.add(
                        egui::Button::new(format!("+ {}", t("btn_add_queue", &[])))
                            .fill(Color32::from_rgb(99, 102, 241)),
                    );

                    if add_btn.clicked()
                        || (text_edit.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter)))
                    {
                        let trimmed = self.url_input.trim().to_string();
                        if !trimmed.is_empty() {
                            let mut item = QueueItem::new(trimmed);
                            item.fmt = self.selected_format.clone();
                            item.bitrate = self.selected_bitrate.clone();
                            item.embed_thumbnail = self.embed_thumbnail;
                            item.parse_metadata = self.parse_metadata;
                            item.output_dir = self.output_dir.to_string_lossy().to_string();

                            let already_queued = {
                                let mut items = self.queue.items.lock().unwrap();
                                if !items
                                    .iter()
                                    .any(|i| i.url == item.url && !is_finished_status(&i.status))
                                {
                                    items.push(item);
                                    false
                                } else {
                                    true
                                }
                            };

                            if !already_queued {
                                self.queue.add(""); // Kick worker
                                self.url_input.clear();
                                self.show_toast(t("msg_added", &[("n", "1")]), false);
                            } else {
                                self.show_toast(t("msg_already_queued", &[]), true);
                            }
                        }
                    }
                });

                ui.add_space(10.0);
                ui.separator();
                ui.add_space(6.0);

                // Format & Bitrate Selection
                ui.horizontal(|ui| {
                    ui.label(t("format_label", &[]));
                    for &fmt in &["mp3", "m4a", "flac", "wav"] {
                        let label = match fmt {
                            "mp3" => "MP3",
                            "m4a" => "M4A (AAC)",
                            "flac" => "FLAC",
                            "wav" => "WAV",
                            _ => fmt,
                        };
                        if ui
                            .selectable_label(self.selected_format == fmt, label)
                            .clicked()
                        {
                            self.selected_format = fmt.to_string();
                            self.save_current_settings();
                        }
                    }

                    if self.selected_format == "mp3" {
                        ui.add_space(16.0);
                        ui.label(t("quality_label", &[]));
                        for &br in &["320", "192", "128"] {
                            let label = format!("{} kbps", br);
                            if ui
                                .selectable_label(self.selected_bitrate == br, label)
                                .clicked()
                            {
                                self.selected_bitrate = br.to_string();
                                self.save_current_settings();
                            }
                        }
                    }
                });

                ui.add_space(6.0);

                // Checkboxes
                ui.horizontal(|ui| {
                    if ui
                        .checkbox(&mut self.embed_thumbnail, t("chk_thumbnail", &[]))
                        .changed()
                    {
                        self.save_current_settings();
                    }
                    ui.add_space(12.0);
                    if ui
                        .checkbox(&mut self.parse_metadata, t("chk_parse", &[]))
                        .changed()
                    {
                        self.save_current_settings();
                    }
                });
            });

        ui.add_space(10.0);

        // Card 2: Queue Management Header
        let counts = self.queue.counts();
        ui.horizontal(|ui| {
            ui.heading(t("queue_title", &[]));
            ui.colored_label(
                Color32::from_rgb(148, 163, 184),
                t(
                    "queue_summary",
                    &[
                        ("total", &counts.total.to_string()),
                        ("active", &counts.active.to_string()),
                        ("pending", &counts.pending.to_string()),
                        ("done", &counts.done.to_string()),
                    ],
                ),
            );

            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                if ui.button(t("btn_clear_done", &[])).clicked() {
                    self.queue.clear_finished();
                }
                if counts.active > 0 && ui.button(t("btn_cancel_current", &[])).clicked() {
                    self.queue.cancel_current();
                }
            });
        });

        ui.add_space(6.0);

        // Queue Items Scrollable List
        egui::ScrollArea::vertical()
            .auto_shrink([false, false])
            .show(ui, |ui| {
                let items = self.queue.items.lock().unwrap().clone();
                if items.is_empty() {
                    ui.add_space(32.0);
                    ui.vertical_centered(|ui| {
                        ui.colored_label(Color32::from_rgb(100, 116, 139), t("queue_empty", &[]));
                    });
                    return;
                }

                for item in items {
                    render_queue_card(ui, &item, self);
                    ui.add_space(6.0);
                }
            });
    }

    fn render_editor_tab(&mut self, ui: &mut egui::Ui) {
        ui.add_space(4.0);

        // Top Toolbar of Editor: Pick File
        egui::Frame::group(ui.style())
            .fill(Color32::from_rgb(24, 28, 38))
            .rounding(Rounding::same(8.0))
            .inner_margin(12.0)
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    if ui
                        .button(format!("📁 {}", t("ed_add_files", &[])))
                        .clicked()
                    {
                        if let Some(file) = rfd::FileDialog::new()
                            .add_filter("Audio Files", &["mp3", "m4a", "wav", "flac", "ogg", "aac"])
                            .pick_file()
                        {
                            self.load_audio_for_editor(file);
                        }
                    }

                    if let Some(ref p) = self.editor_file {
                        ui.colored_label(
                            Color32::from_rgb(241, 245, 249),
                            p.file_name().unwrap_or_default().to_string_lossy(),
                        );
                        if let Some(ref info) = self.audio_info {
                            ui.colored_label(
                                Color32::from_rgb(148, 163, 184),
                                format!("⏱ {}", audio::format_time(info.duration, true)),
                            );
                        }
                    } else {
                        ui.colored_label(Color32::from_rgb(100, 116, 139), t("ed_empty", &[]));
                    }
                });
            });

        ui.add_space(10.0);

        if self.audio_info.is_none() {
            ui.add_space(40.0);
            ui.vertical_centered(|ui| {
                ui.label(t("ed_empty", &[]));
            });
            return;
        }

        let total_dur = self.audio_info.as_ref().map(|i| i.duration).unwrap_or(0.0);

        // Waveform Visualizer Card
        egui::Frame::group(ui.style())
            .fill(Color32::from_rgb(20, 24, 33))
            .rounding(Rounding::same(8.0))
            .inner_margin(10.0)
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.label("Waveform");
                    ui.colored_label(Color32::from_rgb(100, 116, 139), t("ed_wave_hint", &[]));
                });
                ui.add_space(4.0);

                let (response, painter) = ui.allocate_painter(
                    Vec2::new(ui.available_width(), 90.0),
                    Sense::click_and_drag(),
                );
                let rect = response.rect;

                // Canvas background
                painter.rect_filled(rect, 4.0, Color32::from_rgb(16, 19, 26));

                // Draw audio waveform bars
                if !self.peaks.is_empty() {
                    let w_step = rect.width() / self.peaks.len() as f32;
                    for (i, &peak) in self.peaks.iter().enumerate() {
                        let x = rect.left() + i as f32 * w_step;
                        let bar_h = (peak * (rect.height() - 8.0)).max(2.0);
                        let y_top = rect.center().y - bar_h / 2.0;
                        let y_bot = rect.center().y + bar_h / 2.0;

                        let time_pos = (i as f64 / self.peaks.len() as f64) * total_dur;
                        let is_selected = time_pos >= self.clip_start && time_pos <= self.clip_end;

                        let color = if is_selected {
                            Color32::from_rgb(99, 102, 241) // Accent Indigo
                        } else {
                            Color32::from_rgb(51, 65, 85) // Slate
                        };
                        painter.line_segment(
                            [Pos2::new(x, y_top), Pos2::new(x, y_bot)],
                            Stroke::new(w_step.max(1.0), color),
                        );
                    }
                }

                // Interactive dragging / clicking on waveform
                if response.clicked() || response.dragged() {
                    if let Some(pos) = response.interact_pointer_pos() {
                        let ratio = ((pos.x - rect.left()) / rect.width()).clamp(0.0, 1.0) as f64;
                        let click_time = ratio * total_dur;

                        // Check which marker is closer
                        if (click_time - self.clip_start).abs() < (click_time - self.clip_end).abs()
                        {
                            self.clip_start = click_time.min(self.clip_end - 0.1).max(0.0);
                            self.start_str = audio::format_time(self.clip_start, true);
                        } else {
                            self.clip_end = click_time.max(self.clip_start + 0.1).min(total_dur);
                            self.end_str = audio::format_time(self.clip_end, true);
                        }
                    }
                }

                // Draw Start Marker (Green) & End Marker (Red)
                let start_x =
                    rect.left() + (self.clip_start / total_dur.max(0.001)) as f32 * rect.width();
                let end_x =
                    rect.left() + (self.clip_end / total_dur.max(0.001)) as f32 * rect.width();

                painter.line_segment(
                    [
                        Pos2::new(start_x, rect.top()),
                        Pos2::new(start_x, rect.bottom()),
                    ],
                    Stroke::new(2.0_f32, Color32::from_rgb(34, 197, 94)),
                );
                painter.line_segment(
                    [
                        Pos2::new(end_x, rect.top()),
                        Pos2::new(end_x, rect.bottom()),
                    ],
                    Stroke::new(2.0_f32, Color32::from_rgb(239, 68, 68)),
                );
            });

        ui.add_space(10.0);

        // Trimming Inputs & Precision Controls
        egui::Frame::group(ui.style())
            .fill(Color32::from_rgb(24, 28, 38))
            .rounding(Rounding::same(8.0))
            .inner_margin(12.0)
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.label(t("ed_start", &[]));
                    if ui
                        .add(egui::TextEdit::singleline(&mut self.start_str).desired_width(70.0))
                        .changed()
                    {
                        if let Ok(val) = audio::parse_time(&self.start_str) {
                            self.clip_start = val.clamp(0.0, self.clip_end - 0.1);
                        }
                    }

                    ui.add_space(12.0);
                    ui.label(t("ed_end", &[]));
                    if ui
                        .add(egui::TextEdit::singleline(&mut self.end_str).desired_width(70.0))
                        .changed()
                    {
                        if let Ok(val) = audio::parse_time(&self.end_str) {
                            self.clip_end = val.clamp(self.clip_start + 0.1, total_dur);
                        }
                    }

                    ui.add_space(12.0);
                    let len = (self.clip_end - self.clip_start).max(0.0);
                    ui.colored_label(
                        Color32::from_rgb(148, 163, 184),
                        format!("Len: {}", audio::format_time(len, true)),
                    );

                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        if ui.button(t("ed_select_all", &[])).clicked() {
                            self.clip_start = 0.0;
                            self.clip_end = total_dur;
                            self.start_str = "0:00.0".to_string();
                            self.end_str = audio::format_time(total_dur, true);
                        }
                    });
                });

                ui.add_space(10.0);
                ui.separator();
                ui.add_space(6.0);

                // Effects
                ui.label(t("ed_effects_title", &[]));
                ui.horizontal(|ui| {
                    ui.label("Fade In (s):");
                    ui.add(
                        egui::DragValue::new(&mut self.fade_in)
                            .speed(0.1)
                            .range(0.0..=10.0),
                    );

                    ui.add_space(12.0);
                    ui.label("Fade Out (s):");
                    ui.add(
                        egui::DragValue::new(&mut self.fade_out)
                            .speed(0.1)
                            .range(0.0..=10.0),
                    );

                    ui.add_space(12.0);
                    ui.label("Gain (dB):");
                    ui.add(
                        egui::DragValue::new(&mut self.gain_db)
                            .speed(0.5)
                            .range(-20.0..=20.0),
                    );

                    ui.add_space(12.0);
                    ui.checkbox(&mut self.normalize, t("ed_normalize", &[]));
                });
            });

        ui.add_space(10.0);

        // Export Controls Card
        egui::Frame::group(ui.style())
            .fill(Color32::from_rgb(24, 28, 38))
            .rounding(Rounding::same(8.0))
            .inner_margin(12.0)
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.label(t("ed_title", &[]));
                    ui.text_edit_singleline(&mut self.export_title);

                    ui.add_space(12.0);
                    ui.label(t("ed_artist", &[]));
                    ui.text_edit_singleline(&mut self.export_artist);

                    ui.add_space(12.0);
                    ui.checkbox(&mut self.keep_cover, t("ed_keep_cover", &[]));
                });

                ui.add_space(10.0);

                ui.horizontal(|ui| {
                    ui.label(t("format_label", &[]));
                    for &fmt in &["mp3", "m4a", "flac", "wav"] {
                        if ui
                            .selectable_label(self.export_fmt == fmt, fmt.to_uppercase())
                            .clicked()
                        {
                            self.export_fmt = fmt.to_string();
                        }
                    }

                    if self.export_fmt == "mp3" {
                        ui.add_space(12.0);
                        ui.label(t("quality_label", &[]));
                        for &br in &["320", "192", "128"] {
                            if ui
                                .selectable_label(self.export_bitrate == br, format!("{}k", br))
                                .clicked()
                            {
                                self.export_bitrate = br.to_string();
                            }
                        }
                    }

                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        let export_btn = ui.add(
                            egui::Button::new(format!("💾 {}", t("ed_export", &[])))
                                .fill(Color32::from_rgb(34, 197, 94)),
                        );

                        if export_btn.clicked() {
                            self.start_audio_export();
                        }
                    });
                });

                if let Some(pct) = self.export_progress {
                    ui.add_space(8.0);
                    ui.add(egui::ProgressBar::new(pct as f32).show_percentage());
                }
            });
    }

    fn start_audio_export(&mut self) {
        let src_file = match self.editor_file {
            Some(ref p) => p.clone(),
            None => return,
        };

        let default_name = format!(
            "{}_edited.{}",
            self.export_title.replace(' ', "_"),
            self.export_fmt
        );
        let save_dialog = rfd::FileDialog::new()
            .set_file_name(&default_name)
            .add_filter(&self.export_fmt, &[&self.export_fmt])
            .save_file();

        let target_path = match save_dialog {
            Some(p) => p,
            None => return,
        };

        let clip = ClipSpec::new(
            src_file.to_string_lossy().to_string(),
            self.clip_start,
            self.clip_end,
        );
        let clips = vec![clip];

        let cmd = match audio::build_export_command(
            &clips,
            &target_path.to_string_lossy(),
            &self.export_fmt,
            &self.export_bitrate,
            self.fade_in,
            self.fade_out,
            self.gain_db,
            self.crossfade,
            self.normalize,
            &self.export_title,
            &self.export_artist,
            self.keep_cover,
        ) {
            Ok(c) => c,
            Err(e) => {
                self.show_toast(format!("Export build error: {}", e), true);
                return;
            }
        };

        let total_time = audio::output_duration(&clips, self.crossfade);
        self.export_progress = Some(0.0);
        self.cancel_export_flag.store(false, Ordering::SeqCst);

        let cancel_flag = self.cancel_export_flag.clone();
        std::thread::spawn(move || {
            let _ = audio::run_export(&cmd, total_time, None::<fn(f64)>, Some(cancel_flag));
        });
        self.show_toast(format!("Exporting to: {}", target_path.display()), false);
    }
}

fn render_queue_card(ui: &mut egui::Ui, item: &QueueItem, app: &mut MediaToMp3App) {
    egui::Frame::group(ui.style())
        .fill(Color32::from_rgb(26, 30, 42))
        .rounding(Rounding::same(6.0))
        .inner_margin(8.0)
        .show(ui, |ui| {
            ui.horizontal(|ui| {
                // Platform Badge
                let (badge_txt, badge_col) =
                    if item.url.contains("youtube.com") || item.url.contains("youtu.be") {
                        ("YouTube", Color32::from_rgb(239, 68, 68))
                    } else if item.url.contains("facebook.com") || item.url.contains("fb.watch") {
                        ("Facebook", Color32::from_rgb(59, 130, 246))
                    } else {
                        ("Media", Color32::from_rgb(148, 163, 184))
                    };

                ui.colored_label(badge_col, format!("[{}]", badge_txt));

                // Title
                let title_display = if !item.title.is_empty() {
                    item.title.clone()
                } else {
                    item.url.clone()
                };
                ui.strong(title_display);

                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    // Action Buttons based on status
                    if item.status == DONE {
                        if ui.button(format!("✂ {}", t("btn_edit", &[]))).clicked() {
                            app.load_audio_for_editor(PathBuf::from(&item.file_path));
                        }
                        if ui.button(format!("▶ {}", t("btn_play", &[]))).clicked() {
                            play_audio_file(&item.file_path);
                        }
                        if ui
                            .button(format!("📁 {}", t("btn_open_folder", &[])))
                            .clicked()
                        {
                            open_path_in_explorer(&item.file_path);
                        }
                    } else if item.status == ERROR || item.status == CANCELLED {
                        if ui.button(format!("↺ {}", t("btn_retry", &[]))).clicked() {
                            app.queue.retry(item.id);
                        }
                        if ui.button(format!("✕ {}", t("btn_remove", &[]))).clicked() {
                            app.queue.remove(item.id);
                        }
                    } else if is_active_status(&item.status)
                        && ui
                            .button(format!("■ {}", t("btn_cancel_current", &[])))
                            .clicked()
                    {
                        app.queue.cancel_current();
                    }
                });
            });

            // Status and Progress bar
            ui.add_space(4.0);
            if is_active_status(&item.status) {
                ui.horizontal(|ui| {
                    let progress = (item.percent / 100.0).clamp(0.0, 1.0) as f32;
                    ui.add(
                        egui::ProgressBar::new(progress)
                            .desired_width(ui.available_width() - 150.0)
                            .animate(true),
                    );
                    let speed_mb = item.speed as f64 / (1024.0 * 1024.0);
                    ui.colored_label(
                        Color32::from_rgb(148, 163, 184),
                        format!("{:.1}% · {:.1}MB/s", item.percent, speed_mb),
                    );
                });
            } else if item.status == DONE {
                ui.colored_label(
                    Color32::from_rgb(34, 197, 94),
                    format!("{} · {}", t("st_done", &[]), item.file_path),
                );
            } else if item.status == ERROR {
                ui.colored_label(
                    Color32::from_rgb(239, 68, 68),
                    format!(
                        "{} · {}",
                        t("st_error", &[("error", &item.error)]),
                        item.error
                    ),
                );
            } else if item.status == CANCELLED {
                ui.colored_label(Color32::from_rgb(245, 158, 11), t("st_cancelled", &[]));
            } else {
                ui.colored_label(Color32::from_rgb(148, 163, 184), t("st_pending", &[]));
            }
        });
}
