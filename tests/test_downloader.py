import unittest

from downloader import AUDIO_FORMATS, parse_artist_title


class ParseArtistTitleTest(unittest.TestCase):
    def check(self, title, expected, uploader=None):
        self.assertEqual(parse_artist_title(title, uploader), expected)

    def test_dash_separator_and_noise_brackets(self):
        self.check("Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
                   ("Rick Astley", "Never Gonna Give You Up"))

    def test_vietnamese_pipe_separated_title(self):
        self.check("SƠN TÙNG M-TP | CHÚNG TA CỦA TƯƠNG LAI | OFFICIAL MUSIC VIDEO",
                   ("SƠN TÙNG M-TP", "CHÚNG TA CỦA TƯƠNG LAI"))

    def test_keeps_featuring_and_drops_mv(self):
        self.check("Đen - Bài Này Chill Phết ft. MIN (M/V)", ("Đen", "Bài Này Chill Phết ft. MIN"))

    def test_keeps_meaningful_brackets(self):
        self.check("Artist – Song (Live at Wembley) [Remix]", ("Artist", "Song (Live at Wembley) [Remix]"))
        self.check("Artist - Song (Official Remix)", ("Artist", "Song (Official Remix)"))

    def test_hyphen_inside_name_is_not_a_separator(self):
        self.check("Jay-Z - Empire State of Mind (Lyrics)", ("Jay-Z", "Empire State of Mind"))

    def test_falls_back_to_cleaned_uploader(self):
        self.check("Shape of You [Official Lyric Video]", ("Ed Sheeran", "Shape of You"), uploader="Ed Sheeran")
        self.check("Song Name", ("Artist", "Song Name"), uploader="Artist - Topic")
        self.check("Song Name (Lời Bài Hát)", ("ArtistVN", "Song Name"), uploader="ArtistVN Official")
        self.check("Hello", ("", "Hello"))

    def test_never_returns_empty_track(self):
        artist, track = parse_artist_title("(Official Video)", "Someone")
        self.assertTrue(track)


class AudioFormatsTest(unittest.TestCase):
    def test_only_stereo_friendly_formats(self):
        self.assertEqual(set(AUDIO_FORMATS), {"mp3", "m4a", "wav", "flac"})
        self.assertEqual(AUDIO_FORMATS["mp3"]["bitrates"], ["320", "192", "128"])
        self.assertFalse(AUDIO_FORMATS["wav"]["thumbnail"])


if __name__ == "__main__":
    unittest.main()
