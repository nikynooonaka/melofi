# Melofi 🎵

Music downloader ringan buat Android — pake **yt-dlp**, output **Opus 64kbps**, metadata lengkap, anti-blokir.

## ✨ Fitur

| Fitur | Ada? |
|---|---|
| Output Opus 64kbps (ringan banget) | ✅ |
| Cover artwork & metadata lengkap | ✅ |
| Anti-blokir (rotate UA + extractor) | ✅ |
| Cepet, tanpa proxy | ✅ |
| UI Material You modern | ✅ |
| Search langsung dari YouTube | ✅ |

## 🚀 Cara Build APK

### 1. Cara termudah — GitHub Actions (tanpa ngapa-ngapain)

1. **Fork repo ini** ke GitHub kamu
2. Buka tab **Actions** → klik **Build APK Melofi** → **Run workflow**
3. Tunggu ~15-30 menit, APK siap di-download dari artifact!

### 2. Build pake Buildozer (kalo mau local)

```bash
# Install buildozer
pip install buildozer

# Build APK
buildozer android debug
```

APK bakal muncul di folder `bin/` 🎉

## 📱 Cara Install

1. Download APK dari GitHub Actions (artifact)
2. Buka di HP Android
3. Allow "Install dari sumber tidak dikenal"
4. Done! Mulai download lagu~

## ⚙️ Tech Stack

- **Python** + **KivyMD** (UI)
- **yt-dlp** (engine download)
- **mutagen** (metadata & cover art)
- **Buildozer** (build APK)

## 🧡 Credits

Dibuat spesial buat kak Niky 🫶
