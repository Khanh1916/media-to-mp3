import glob
import json
import os
import re
import shutil
import string
import tempfile
import unittest

import config
import i18n
from downloader import AUDIO_FORMATS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "sub", "settings.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_missing_file_gives_defaults(self):
        self.assertEqual(config.load_settings(self.path), config.DEFAULTS)

    def test_round_trip(self):
        settings = dict(config.DEFAULTS, format="flac", language="en", embed_thumbnail=False)
        config.save_settings(settings, self.path)
        self.assertEqual(config.load_settings(self.path), settings)
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_wrong_types_and_unknown_keys_are_ignored(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"format": 3, "embed_thumbnail": "yes", "language": "en", "other": 1}, f)
        settings = config.load_settings(self.path)
        self.assertEqual(settings["format"], "mp3")
        self.assertTrue(settings["embed_thumbnail"])
        self.assertEqual(settings["language"], "en")
        self.assertNotIn("other", settings)

    def test_corrupt_file_gives_defaults(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{not json")
        self.assertEqual(config.load_settings(self.path), config.DEFAULTS)


class I18nTest(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("vi")

    @staticmethod
    def fields(text):
        return {name for _, name, _, _ in string.Formatter().parse(text) if name}

    def test_languages_have_same_keys_and_placeholders(self):
        vi, en = i18n.STRINGS["vi"], i18n.STRINGS["en"]
        self.assertEqual(set(vi), set(en))
        for key in vi:
            self.assertEqual(self.fields(vi[key]), self.fields(en[key]), key)

    def test_every_key_used_in_code_exists(self):
        used = set()
        for path in glob.glob(os.path.join(ROOT, "*.py")):
            if os.path.basename(path) == "i18n.py":
                continue
            with open(path, encoding="utf-8") as f:
                used |= set(re.findall(r"""\bt\(\s*["']([a-z0-9_]+)["']""", f.read()))
        used |= {f"fmt_hint_{fmt}" for fmt in AUDIO_FORMATS}
        self.assertTrue(used)
        self.assertEqual(sorted(used - set(i18n.STRINGS["vi"])), [])

    def test_emoji_stripped_only_when_enabled(self):
        original = i18n.STRIP_EMOJI
        try:
            i18n.STRIP_EMOJI = True
            self.assertEqual(i18n.t("btn_add_queue"), "Thêm vào hàng đợi")
            self.assertEqual(i18n.t("st_error", error="x"), "x")
            self.assertEqual(i18n.plain("🔴 YouTube Video"), "YouTube Video")
            self.assertEqual(i18n.plain("Tải ⬇ nhạc"), "Tải nhạc")
            i18n.STRIP_EMOJI = False
            self.assertEqual(i18n.t("btn_add_queue"), "➕ Thêm vào hàng đợi")
        finally:
            i18n.STRIP_EMOJI = original

    def test_switch_language_and_fallbacks(self):
        i18n.set_language("en")
        self.assertEqual(i18n.t("st_done"), "✅ Done")
        self.assertEqual(i18n.t("msg_added", n=2), "Added 2 link(s) to the queue.")
        i18n.set_language("xx")  # không hỗ trợ -> giữ nguyên
        self.assertEqual(i18n.get_language(), "en")
        self.assertEqual(i18n.t("no_such_key"), "no_such_key")


if __name__ == "__main__":
    unittest.main()
