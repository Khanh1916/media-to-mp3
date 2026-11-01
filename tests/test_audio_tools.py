import os
import shutil
import subprocess
import tempfile
import threading
import unittest

import audio_tools as at
from downloader import get_ffmpeg_path


class TimeTest(unittest.TestCase):
    def test_format_time(self):
        self.assertEqual(at.format_time(83.25), "1:23.2")
        self.assertEqual(at.format_time(3723), "1:02:03.0")
        self.assertEqual(at.format_time(213.4, precise=False), "3:33")
        self.assertEqual(at.format_time(-5), "0:00.0")

    def test_parse_time(self):
        self.assertEqual(at.parse_time("1:23.5"), 83.5)
        self.assertEqual(at.parse_time("83,5"), 83.5)
        self.assertEqual(at.parse_time("1:02:03"), 3723)
        self.assertEqual(at.parse_time(" 7 "), 7)
        for bad in ("", "abc", "1:2:3:4", "-1"):
            with self.assertRaises(ValueError):
                at.parse_time(bad)


class CrossfadeTest(unittest.TestCase):
    def test_crossfade_is_shorter_than_every_clip(self):
        clips = [at.ClipSpec("a", 0, 10), at.ClipSpec("b", 0, 3)]
        self.assertAlmostEqual(at.effective_crossfade(clips, 5), 1.45)
        self.assertEqual(at.effective_crossfade(clips[:1], 5), 0)
        self.assertAlmostEqual(at.output_duration(clips, 1), 12)
        self.assertAlmostEqual(at.output_duration(clips, 0), 13)


@unittest.skipUnless(get_ffmpeg_path(), "FFmpeg not available")
class ExportCommandTest(unittest.TestCase):
    clips = [at.ClipSpec("a.mp3", 5, 15), at.ClipSpec("b.m4a", 0, 20)]

    def test_concat_without_crossfade(self):
        cmd = at.build_export_command(self.clips, "out.mp3", bitrate="192")
        graph = cmd[cmd.index("-filter_complex") + 1]
        self.assertIn("concat=n=2:v=0:a=1", graph)
        self.assertNotIn("acrossfade", graph)
        self.assertEqual(cmd[cmd.index("-b:a") + 1], "192k")
        self.assertEqual(cmd[cmd.index("-id3v2_version") + 1], "3")
        self.assertEqual(cmd[-1], "out.mp3")
        self.assertEqual(cmd.count("-ss"), 2)

    def test_effects_and_crossfade(self):
        cmd = at.build_export_command(self.clips, "out.flac", fmt="flac", fade_in=2, fade_out=3, gain_db=-4,
                                      crossfade=2, normalize=True, title="T", artist="A", keep_cover=True)
        graph = cmd[cmd.index("-filter_complex") + 1]
        self.assertIn("acrossfade=d=2.000", graph)
        self.assertIn("afade=t=in:st=0:d=2.000", graph)
        self.assertIn("afade=t=out:st=25.000:d=3.000", graph)  # 10 + 20 - 2 = 28s, fade bắt đầu ở 25s
        self.assertIn("volume=-4.0dB", graph)
        self.assertIn("loudnorm", graph)
        self.assertTrue(graph.endswith("aresample=44100[out]"))
        self.assertIn("attached_pic", cmd)
        self.assertIn("title=T", cmd)
        self.assertIn("artist=A", cmd)

    def test_wav_never_keeps_cover(self):
        cmd = at.build_export_command(self.clips, "out.wav", fmt="wav", keep_cover=True)
        self.assertNotIn("attached_pic", cmd)
        self.assertIn("pcm_s16le", cmd)

    def test_rejects_bad_input(self):
        with self.assertRaises(at.AudioToolError):
            at.build_export_command([], "out.mp3")
        with self.assertRaises(at.AudioToolError):
            at.build_export_command(self.clips, "out.ogg", fmt="ogg")


@unittest.skipUnless(get_ffmpeg_path(), "FFmpeg not available")
class ExportIntegrationTest(unittest.TestCase):
    """Tạo 2 file sóng sine bằng ffmpeg rồi cắt, ghép, xuất thật."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.sources = []
        for name, freq, dur in (("a.mp3", 440, 8), ("b.wav", 660, 6)):
            path = os.path.join(cls.tmp, name)
            subprocess.run([get_ffmpeg_path(), "-v", "error", "-y", "-f", "lavfi", "-i",
                            f"sine=frequency={freq}:duration={dur}", "-metadata", f"title=Tone {freq}",
                            "-metadata", "artist=Tester", path], check=True)
            cls.sources.append(path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_probe(self):
        info = at.probe(self.sources[0])
        self.assertAlmostEqual(info.duration, 8, delta=0.1)
        self.assertEqual((info.title, info.artist, info.has_cover), ("Tone 440", "Tester", False))
        with self.assertRaises(at.AudioToolError):
            at.probe(os.path.join(self.tmp, "missing.mp3"))

    def test_peaks_are_normalized(self):
        peaks = at.load_peaks(self.sources[0], 8, buckets=100)
        self.assertGreaterEqual(len(peaks), 100)
        self.assertAlmostEqual(max(peaks), 1.0)

    def test_cut_and_join_every_format(self):
        clips = [at.ClipSpec(self.sources[0], 1, 4), at.ClipSpec(self.sources[1], 2, 5)]
        for fmt in at.EXPORT_CODECS:
            out = os.path.join(self.tmp, f"joined.{fmt}")
            progress = []
            at.run_export(at.build_export_command(clips, out, fmt=fmt, crossfade=1, fade_out=1, title="Ghép"),
                          at.output_duration(clips, 1), progress.append)
            info = at.probe(out)
            self.assertAlmostEqual(info.duration, 5, delta=0.15, msg=fmt)
            self.assertEqual(progress[-1], 1.0)
            if fmt != "wav":
                self.assertEqual(info.title, "Ghép")

    def test_refuses_to_overwrite_an_input(self):
        cmd = at.build_export_command([at.ClipSpec(self.sources[0], 0, 2)], self.sources[0])
        with self.assertRaises(at.AudioToolError):
            at.run_export(cmd, 2)
        self.assertAlmostEqual(at.probe(self.sources[0]).duration, 8, delta=0.1)

    def test_cancel_removes_partial_file(self):
        out = os.path.join(self.tmp, "cancelled.flac")
        event = threading.Event()
        event.set()
        cmd = at.build_export_command([at.ClipSpec(self.sources[0], 0, 8)], out, fmt="flac", normalize=True)
        with self.assertRaises(at.AudioToolError):
            at.run_export(cmd, 8, cancel_event=event)
        self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
