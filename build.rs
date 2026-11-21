fn main() {
    #[cfg(windows)]
    {
        let mut res = winres::WindowsResource::new();
        res.set_icon("assets/icon.ico");
        res.set("ProductName", "Media to MP3");
        res.set("FileDescription", "Media to MP3 Converter & Audio Editor");
        res.set("LegalCopyright", "Copyright (c) 2026 KhanhNN");
        let _ = res.compile();
    }
}
