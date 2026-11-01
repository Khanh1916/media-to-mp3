import threading
import time
import unittest

from download_queue import CANCELLED, DONE, ERROR, PENDING, DownloadQueue


class FakeDownloader:
    """Giả lập MediaDownloader: link chứa 'fail' thì lỗi, chứa 'slow' thì chờ tới khi bị hủy."""

    def __init__(self):
        self.is_cancelled = False
        self.calls = []
        self.started = threading.Event()

    def cancel(self):
        self.is_cancelled = True

    def download_audio(self, url, progress_callback, finished_callback, error_callback, **options):
        self.is_cancelled = False
        self.calls.append((url, options))
        progress_callback({"status": "downloading", "percent": 50.0, "speed": 1024, "eta": 3, "title": f"T {url}"})
        if "slow" in url:
            self.started.set()
            while not self.is_cancelled:
                time.sleep(0.01)
            error_callback("cancelled")
            return None
        if "fail" in url:
            error_callback("boom")
            return None
        progress_callback({"status": "converting", "percent": 100.0})
        finished_callback(f"/music/{url}.mp3")
        return f"/music/{url}.mp3"


class DownloadQueueTest(unittest.TestCase):
    def setUp(self):
        self.downloader = FakeDownloader()
        self.changes = []
        self.queue = DownloadQueue(self.downloader, on_change=self.changes.append)

    def wait_idle(self, timeout=5):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self.queue.is_busy and not any(i.status == PENDING for i in self.queue.items):
                time.sleep(0.05)
                if not self.queue.is_busy:
                    return
            time.sleep(0.01)
        self.fail("queue did not finish")

    def test_downloads_in_order_with_item_options(self):
        a = self.queue.add("a", fmt="flac", bitrate="320", output_dir="/x")
        b = self.queue.add("b", fmt="mp3", bitrate="128")
        self.wait_idle()
        self.assertEqual([c[0] for c in self.downloader.calls], ["a", "b"])
        self.assertEqual(self.downloader.calls[0][1]["fmt"], "flac")
        self.assertEqual(self.downloader.calls[0][1]["output_dir"], "/x")
        self.assertEqual((a.status, a.file_path, a.title), (DONE, "/music/a.mp3", "T a"))
        self.assertEqual(b.status, DONE)
        self.assertTrue(self.changes)

    def test_skips_duplicate_unfinished_links(self):
        self.assertIsNotNone(self.queue.add("slow"))
        self.assertIsNone(self.queue.add("slow"))
        self.downloader.started.wait(2)
        self.queue.cancel_current()
        self.wait_idle()
        self.downloader.started.clear()
        self.assertIsNotNone(self.queue.add("slow"))  # đã hủy xong thì được thêm lại
        self.downloader.started.wait(2)
        self.queue.cancel_current()
        self.wait_idle()

    def test_error_then_retry_and_clear(self):
        item = self.queue.add("fail")
        ok = self.queue.add("ok")
        self.wait_idle()
        self.assertEqual((item.status, item.error), (ERROR, "boom"))
        self.assertEqual(ok.status, DONE)
        self.assertEqual(self.queue.counts()["error"], 1)

        item.url = "fixed"
        self.queue.retry(item.id)
        self.wait_idle()
        self.assertEqual(item.status, DONE)

        self.queue.clear_finished()
        self.assertEqual(self.queue.items, [])

    def test_cancel_current_keeps_processing_the_rest(self):
        slow = self.queue.add("slow")
        nxt = self.queue.add("next")
        self.assertTrue(self.downloader.started.wait(2))
        self.queue.cancel_current()
        self.wait_idle()
        self.assertEqual(slow.status, CANCELLED)
        self.assertEqual(nxt.status, DONE)

    def test_remove_pending_item_only(self):
        slow = self.queue.add("slow")
        pending = self.queue.add("later")
        self.assertTrue(self.downloader.started.wait(2))
        self.queue.remove(slow.id)  # đang tải thì không xóa được
        self.queue.remove(pending.id)
        self.assertEqual([i.id for i in self.queue.items], [slow.id])
        self.queue.cancel_current()
        self.wait_idle()


if __name__ == "__main__":
    unittest.main()
