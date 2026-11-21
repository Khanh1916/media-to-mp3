use std::path::Path;
use std::process::Command;

pub fn open_path_in_explorer<P: AsRef<Path>>(path: P) {
    let p = path.as_ref();
    #[cfg(target_os = "windows")]
    {
        if p.is_file() {
            let _ = Command::new("explorer")
                .arg(format!("/select,{}", p.display()))
                .spawn();
        } else {
            let _ = Command::new("explorer")
                .arg(p)
                .spawn();
        }
    }
    #[cfg(target_os = "macos")]
    {
        if p.is_file() {
            let _ = Command::new("open").arg("-R").arg(p).spawn();
        } else {
            let _ = Command::new("open").arg(p).spawn();
        }
    }
    #[cfg(not(any(target_os = "windows", target_os = "macos")))]
    {
        let target = if p.is_file() {
            p.parent().unwrap_or(p)
        } else {
            p
        };
        let _ = Command::new("xdg-open").arg(target).spawn();
    }
}

pub fn play_audio_file<P: AsRef<Path>>(file_path: P) {
    let p = file_path.as_ref();
    #[cfg(target_os = "windows")]
    {
        let _ = Command::new("cmd")
            .args(["/c", "start", "", &p.to_string_lossy()])
            .spawn();
    }
    #[cfg(target_os = "macos")]
    {
        let _ = Command::new("open").arg(p).spawn();
    }
    #[cfg(not(any(target_os = "windows", target_os = "macos")))]
    {
        let _ = Command::new("xdg-open").arg(p).spawn();
    }
}
