"""
Hàng đợi tải: nhận nhiều link và tải lần lượt từng bài trong một luồng nền.
Không phụ thuộc giao diện; mỗi khi một mục thay đổi sẽ gọi `on_change(item)` từ luồng nền.
"""
import itertools
import threading
from dataclasses import dataclass, field
from typing import Callable, List, Optional

PENDING = "pending"
DOWNLOADING = "downloading"
CONVERTING = "converting"
DONE = "done"
ERROR = "error"
CANCELLED = "cancelled"

ACTIVE_STATUSES = (DOWNLOADING, CONVERTING)
FINISHED_STATUSES = (DONE, ERROR, CANCELLED)

_ids = itertools.count(1)


@dataclass
class QueueItem:
    url: str
    fmt: str = "mp3"
    bitrate: str = "320"
    output_dir: str = ""
    embed_thumbnail: bool = True
    parse_metadata: bool = True
    id: int = field(default_factory=lambda: next(_ids))
    title: str = ""
    status: str = PENDING
    percent: float = 0.0
    speed: float = 0.0
    eta: int = 0
    file_path: str = ""
    error: str = ""


class DownloadQueue:
    def __init__(self, downloader, on_change: Optional[Callable[[Optional[QueueItem]], None]] = None):
        self.downloader = downloader
        self.on_change = on_change
        self.items: List[QueueItem] = []
        self._lock = threading.Lock()
        self._worker: Optional[threading.Thread] = None
        self._current: Optional[QueueItem] = None

    # ---- Thao tác từ giao diện ----
    def add(self, url: str, **options) -> Optional[QueueItem]:
        """Thêm link vào cuối hàng đợi; bỏ qua nếu link đó đang chờ hoặc đang tải."""
        url = url.strip()
        with self._lock:
            if any(i.url == url and i.status not in FINISHED_STATUSES for i in self.items):
                return None
            item = QueueItem(url=url, **options)
            self.items.append(item)
        self._notify(item)
        self._kick()
        return item

    def remove(self, item_id: int):
        with self._lock:
            self.items = [i for i in self.items if i.id != item_id or i.status in ACTIVE_STATUSES]
        self._notify(None)

    def retry(self, item_id: int):
        item = self.get(item_id)
        if item and item.status in (ERROR, CANCELLED):
            item.status, item.percent, item.error = PENDING, 0.0, ""
            self._notify(item)
            self._kick()

    def clear_finished(self):
        with self._lock:
            self.items = [i for i in self.items if i.status not in FINISHED_STATUSES]
        self._notify(None)

    def cancel_current(self):
        if self._current is not None:
            self.downloader.cancel()

    def get(self, item_id: int) -> Optional[QueueItem]:
        with self._lock:
            return next((i for i in self.items if i.id == item_id), None)

    @property
    def is_busy(self) -> bool:
        return self._current is not None

    def counts(self):
        with self._lock:
            statuses = [i.status for i in self.items]
        return {
            "total": len(statuses),
            "active": sum(s in ACTIVE_STATUSES for s in statuses),
            "pending": statuses.count(PENDING),
            "done": statuses.count(DONE),
            "error": statuses.count(ERROR),
        }

    # ---- Luồng nền ----
    def _notify(self, item: Optional[QueueItem]):
        if self.on_change:
            self.on_change(item)

    def _next_pending(self) -> Optional[QueueItem]:
        with self._lock:
            return next((i for i in self.items if i.status == PENDING), None)

    def _kick(self):
        with self._lock:
            if self._worker and self._worker.is_alive():
                return
            self._worker = threading.Thread(target=self._run, daemon=True, name="DownloadQueueWorker")
            self._worker.start()

    def _run(self):
        while True:
            item = self._next_pending()
            if item is None:
                break
            self._current = item
            item.status = DOWNLOADING
            self._notify(item)
            self._download(item)
            self._current = None
            self._notify(item)

        # Có thể có mục mới được thêm đúng lúc luồng vừa thoát vòng lặp
        with self._lock:
            self._worker = None
        if self._next_pending():
            self._kick()

    def _download(self, item: QueueItem):
        def on_progress(d):
            if d.get('title'):
                item.title = d['title']
            if d.get('status') == 'converting':
                item.status, item.percent = CONVERTING, 100.0
            else:
                item.status = DOWNLOADING
                item.percent = d.get('percent') or 0.0
                item.speed = d.get('speed') or 0
                item.eta = d.get('eta') or 0
            self._notify(item)

        def on_finished(path):
            item.status, item.file_path, item.percent = DONE, path, 100.0

        def on_error(msg):
            item.status = CANCELLED if self.downloader.is_cancelled else ERROR
            item.error = msg

        try:
            self.downloader.download_audio(
                url=item.url,
                fmt=item.fmt,
                bitrate=item.bitrate,
                output_dir=item.output_dir or None,
                embed_thumbnail=item.embed_thumbnail,
                parse_metadata=item.parse_metadata,
                progress_callback=on_progress,
                finished_callback=on_finished,
                error_callback=on_error,
            )
        except Exception as e:  # không để một bài lỗi làm dừng cả hàng đợi
            item.status, item.error = ERROR, str(e)
        if item.status in ACTIVE_STATUSES:
            item.status = ERROR
