use crate::downloader::MediaDownloader;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};

pub const PENDING: &str = "pending";
pub const DOWNLOADING: &str = "downloading";
pub const CONVERTING: &str = "converting";
pub const DONE: &str = "done";
pub const ERROR: &str = "error";
pub const CANCELLED: &str = "cancelled";

pub fn is_active_status(status: &str) -> bool {
    status == DOWNLOADING || status == CONVERTING
}

pub fn is_finished_status(status: &str) -> bool {
    status == DONE || status == ERROR || status == CANCELLED
}

static ID_COUNTER: AtomicUsize = AtomicUsize::new(1);

#[derive(Debug, Clone)]
pub struct QueueItem {
    pub id: usize,
    pub url: String,
    pub fmt: String,
    pub bitrate: String,
    pub output_dir: String,
    pub embed_thumbnail: bool,
    pub parse_metadata: bool,
    pub title: String,
    pub status: String,
    pub percent: f64,
    pub speed: u64,
    pub eta: u64,
    pub file_path: String,
    pub error: String,
}

impl QueueItem {
    pub fn new(url: String) -> Self {
        Self {
            id: ID_COUNTER.fetch_add(1, Ordering::SeqCst),
            url,
            fmt: "mp3".to_string(),
            bitrate: "320".to_string(),
            output_dir: String::new(),
            embed_thumbnail: true,
            parse_metadata: true,
            title: String::new(),
            status: PENDING.to_string(),
            percent: 0.0,
            speed: 0,
            eta: 0,
            file_path: String::new(),
            error: String::new(),
        }
    }
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct QueueCounts {
    pub total: usize,
    pub active: usize,
    pub pending: usize,
    pub done: usize,
    pub error: usize,
}

pub type ChangeCallback = Arc<dyn Fn(Option<&QueueItem>) + Send + Sync>;

pub struct DownloadQueue {
    pub downloader: MediaDownloader,
    pub on_change: Option<ChangeCallback>,
    pub items: Arc<Mutex<Vec<QueueItem>>>,
    current_item: Arc<Mutex<Option<QueueItem>>>,
    worker_handle: Arc<Mutex<Option<JoinHandle<()>>>>,
}

impl DownloadQueue {
    pub fn new(downloader: MediaDownloader, on_change: Option<ChangeCallback>) -> Self {
        Self {
            downloader,
            on_change,
            items: Arc::new(Mutex::new(Vec::new())),
            current_item: Arc::new(Mutex::new(None)),
            worker_handle: Arc::new(Mutex::new(None)),
        }
    }

    pub fn add(&self, url: &str) -> Option<QueueItem> {
        let trimmed = url.trim().to_string();
        if trimmed.is_empty() {
            return None;
        }

        let mut items = self.items.lock().unwrap();
        if items
            .iter()
            .any(|i| i.url == trimmed && !is_finished_status(&i.status))
        {
            return None;
        }

        let item = QueueItem::new(trimmed);
        items.push(item.clone());
        drop(items);

        self.notify(Some(&item));
        self.kick();
        Some(item)
    }

    pub fn remove(&self, item_id: usize) {
        let mut items = self.items.lock().unwrap();
        items.retain(|i| i.id != item_id || is_active_status(&i.status));
        drop(items);
        self.notify(None);
    }

    pub fn retry(&self, item_id: usize) {
        let mut items = self.items.lock().unwrap();
        let mut found = None;
        if let Some(item) = items.iter_mut().find(|i| i.id == item_id) {
            if item.status == ERROR || item.status == CANCELLED {
                item.status = PENDING.to_string();
                item.percent = 0.0;
                item.error.clear();
                found = Some(item.clone());
            }
        }
        drop(items);

        if let Some(it) = found {
            self.notify(Some(&it));
            self.kick();
        }
    }

    pub fn clear_finished(&self) {
        let mut items = self.items.lock().unwrap();
        items.retain(|i| !is_finished_status(&i.status));
        drop(items);
        self.notify(None);
    }

    pub fn cancel_current(&self) {
        self.downloader.cancel();
    }

    pub fn is_busy(&self) -> bool {
        self.current_item.lock().unwrap().is_some()
    }

    pub fn get(&self, item_id: usize) -> Option<QueueItem> {
        let items = self.items.lock().unwrap();
        items.iter().find(|i| i.id == item_id).cloned()
    }

    pub fn counts(&self) -> QueueCounts {
        let items = self.items.lock().unwrap();
        let mut counts = QueueCounts {
            total: items.len(),
            ..Default::default()
        };
        for i in items.iter() {
            if is_active_status(&i.status) {
                counts.active += 1;
            } else if i.status == PENDING {
                counts.pending += 1;
            } else if i.status == DONE {
                counts.done += 1;
            } else if i.status == ERROR {
                counts.error += 1;
            }
        }
        counts
    }

    fn notify(&self, item: Option<&QueueItem>) {
        if let Some(ref cb) = self.on_change {
            cb(item);
        }
    }

    fn kick(&self) {
        let mut handle = self.worker_handle.lock().unwrap();
        if handle.is_some() {
            return;
        }

        let items_arc = self.items.clone();
        let current_arc = self.current_item.clone();
        let downloader = self.downloader.clone();
        let on_change = self.on_change.clone();
        let worker_handle_arc = self.worker_handle.clone();

        let join = thread::spawn(move || {
            loop {
                let pending = {
                    let items = items_arc.lock().unwrap();
                    items.iter().find(|i| i.status == PENDING).cloned()
                };

                let mut current = match pending {
                    Some(p) => p,
                    None => break,
                };

                // Mark downloading
                {
                    let mut items = items_arc.lock().unwrap();
                    if let Some(item) = items.iter_mut().find(|i| i.id == current.id) {
                        item.status = DOWNLOADING.to_string();
                        current = item.clone();
                    }
                    *current_arc.lock().unwrap() = Some(current.clone());
                }
                if let Some(ref cb) = on_change {
                    cb(Some(&current));
                }

                // Download using downloader
                let url = current.url.clone();
                let fmt = current.fmt.clone();
                let bitrate = current.bitrate.clone();
                let out_dir = if current.output_dir.is_empty() {
                    None
                } else {
                    Some(std::path::PathBuf::from(&current.output_dir))
                };
                let embed_thumb = current.embed_thumbnail;
                let parse_meta = current.parse_metadata;

                let items_p = items_arc.clone();
                let on_change_p = on_change.clone();
                let cur_id = current.id;

                let progress_cb = move |status: &str, percent: f64, speed: u64, eta: u64| {
                    let mut it_copy = None;
                    {
                        let mut items = items_p.lock().unwrap();
                        if let Some(item) = items.iter_mut().find(|i| i.id == cur_id) {
                            if status == "converting" {
                                item.status = CONVERTING.to_string();
                                item.percent = 100.0;
                            } else {
                                item.status = DOWNLOADING.to_string();
                                item.percent = percent;
                                item.speed = speed;
                                item.eta = eta;
                            }
                            it_copy = Some(item.clone());
                        }
                    }
                    if let (Some(ref cb), Some(ref it)) = (&on_change_p, &it_copy) {
                        cb(Some(it));
                    }
                };

                let items_f = items_arc.clone();
                let on_change_f = on_change.clone();
                let finished_cb = move |path: String| {
                    let mut it_copy = None;
                    {
                        let mut items = items_f.lock().unwrap();
                        if let Some(item) = items.iter_mut().find(|i| i.id == cur_id) {
                            item.status = DONE.to_string();
                            item.file_path = path;
                            item.percent = 100.0;
                            it_copy = Some(item.clone());
                        }
                    }
                    if let (Some(ref cb), Some(ref it)) = (&on_change_f, &it_copy) {
                        cb(Some(it));
                    }
                };

                let items_e = items_arc.clone();
                let on_change_e = on_change.clone();
                let error_cb = move |err: String| {
                    let mut it_copy = None;
                    {
                        let mut items = items_e.lock().unwrap();
                        if let Some(item) = items.iter_mut().find(|i| i.id == cur_id) {
                            if err == "cancelled" {
                                item.status = CANCELLED.to_string();
                            } else {
                                item.status = ERROR.to_string();
                                item.error = err;
                            }
                            it_copy = Some(item.clone());
                        }
                    }
                    if let (Some(ref cb), Some(ref it)) = (&on_change_e, &it_copy) {
                        cb(Some(it));
                    }
                };

                downloader.download_audio(
                    &url,
                    &fmt,
                    &bitrate,
                    out_dir.as_deref(),
                    embed_thumb,
                    parse_meta,
                    progress_cb,
                    finished_cb,
                    error_cb,
                );

                *current_arc.lock().unwrap() = None;
            }

            *worker_handle_arc.lock().unwrap() = None;
        });

        *handle = Some(join);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_queue_add_and_duplicate() {
        let dl = MediaDownloader::new(None);
        let q = DownloadQueue::new(dl, None);

        let item1 = q.add("https://youtube.com/watch?v=111");
        assert!(item1.is_some());
        let dup = q.add("https://youtube.com/watch?v=111");
        assert!(dup.is_none());
    }

    #[test]
    fn test_queue_counts() {
        let dl = MediaDownloader::new(None);
        let q = DownloadQueue::new(dl, None);
        assert_eq!(q.counts().total, 0);

        let _ = q.add("https://youtube.com/watch?v=111");
        assert_eq!(q.counts().total, 1);
    }
}
