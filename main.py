"""
Melofi · Music Downloader
~ ringan, anti-blokir, metadata lengkap ~
"""

import os, sys, re, json, random, threading, time
from datetime import datetime
from pathlib import Path

import requests
from kivy.clock import Clock
from kivy.utils import platform

# ── KivyMD ──
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import OneAvatarIconListItem, ImageLeftWidget
from kivymd.uix.card import MDCard
from kivymd.uix.progress import MDProgressBar
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar
from kivy.metrics import dp

# ── yt-dlp ──
try:
    import yt_dlp
    YTDL_AVAILABLE = True
except ImportError:
    YTDL_AVAILABLE = False
    print("[!] yt-dlp gak keinstall, fallback ke mock")

# ── Metadata ──
try:
    from mutagen.oggopus import OggOpus
    from mutagen.flac import Picture as FlacPicture
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("[!] mutagen gak keinstall, metadata skip")

# ═══════════════════════════════════════════
#   ANTI BLOKIR
# ═══════════════════════════════════════════

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; SM-S938B) AppleWebKit/537.36 Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; rv:134.0) Gecko/20100101 Firefox/134.0",
]

def random_ua():
    return random.choice(USER_AGENTS)

# ═══════════════════════════════════════════
#   YT-DLP WRAPPER
# ═══════════════════════════════════════════

YTDL_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': 'in_playlist',
    'ignoreerrors': True,
    'retries': 10,
    'fragment_retries': 10,
    'sleep_interval': 0.5,
    'user_agent': random_ua(),
    'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
    'http_headers': {'Accept-Language': 'id,en;q=0.9'},
}

def search_music(query, max_results=12):
    """Cari lagu lewat yt-dlp"""
    if not YTDL_AVAILABLE:
        return mock_search(query, max_results)

    opts = {**YTDL_OPTS, 'user_agent': random_ua()}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            data = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            results = []
            for entry in (data.get('entries') or []):
                if not entry:
                    continue
                duration = entry.get('duration') or 0
                results.append({
                    'id': entry.get('id', ''),
                    'title': entry.get('title', 'Unknown'),
                    'artist': entry.get('channel', entry.get('uploader', 'Unknown')),
                    'duration': duration,
                    'duration_str': f"{duration//60}:{duration%60:02d}" if duration else "?",
                    'thumb': entry.get('thumbnail', ''),
                    'url': f"https://youtu.be/{entry['id']}" if entry.get('id') else '',
                    'source': 'youtube',
                })
            return results
    except Exception as e:
        print(f"[ERR] search gagal: {e}")
        return mock_search(query, max_results)


def mock_search(query, n=6):
    """Cth hasil kalo offline / error"""
    samples = [
        ("Loneliness", "Putri Ariani", 210),
        ("Ditto", "NewJeans", 194),
        ("Kill Bill", "SZA", 185),
        ("Snooze", "SZA", 202),
        ("Flowers", "Miley Cyrus", 200),
        ("Hype Boy", "NewJeans", 175),
    ]
    results = []
    for i, (t, a, d) in enumerate(samples[:n]):
        m, s = divmod(d, 60)
        results.append({
            'id': f"mock_{i}",
            'title': t,
            'artist': a,
            'duration': d,
            'duration_str': f"{m}:{s:02d}",
            'thumb': '',
            'url': '',
            'source': 'mock',
        })
    return results


def get_audio_streams(url):
    """Ambil info audio streams dari URL"""
    if not YTDL_AVAILABLE:
        return None

    opts = {
        **YTDL_OPTS,
        'user_agent': random_ua(),
        'format': 'bestaudio[ext=opus]/bestaudio[ext=m4a]/bestaudio',
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'artist': info.get('channel', info.get('uploader', 'Unknown')),
                'album': info.get('album', ''),
                'year': info.get('release_year') or info.get('upload_date', '')[:4] if info.get('upload_date') else '',
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'webpage_url': url,
                'extractor': info.get('extractor', ''),
            }
    except Exception as e:
        print(f"[ERR] get_audio_streams: {e}")
        return None


# ═══════════════════════════════════════════
#   METADATA WRITER (mutagen)
# ═══════════════════════════════════════════

def embed_metadata(filepath, metadata, cover_data=None):
    """Tulis metadata ke file audio (opus/m4a)"""
    if not MUTAGEN_AVAILABLE:
        print("[*] mutagen skip - gak keinstall")
        return False

    ext = Path(filepath).suffix.lower()
    try:
        if ext == '.opus':
            audio = OggOpus(filepath)
            audio['title'] = metadata.get('title', '')
            audio['artist'] = metadata.get('artist', '')
            audio['album'] = metadata.get('album', '')
            audio['date'] = str(metadata.get('year', ''))
            audio['genre'] = 'Music'
            if cover_data:
                pic = FlacPicture()
                pic.type = 3  # front cover
                pic.mime = 'image/jpeg' if isinstance(cover_data, bytes) else 'image/png'
                pic.desc = 'Cover'
                pic.data = cover_data if isinstance(cover_data, bytes) else cover_data.encode()
                pic.width = pic.height = 640
                audio['metadata_block_picture'] = pic.write()
            audio.save()

        elif ext == '.m4a':
            audio = MP4(filepath)
            audio['\xa9nam'] = metadata.get('title', '')
            audio['\xa9ART'] = metadata.get('artist', '')
            audio['\xa9alb'] = metadata.get('album', '')
            audio['\xa9day'] = str(metadata.get('year', ''))
            audio['\xa9gen'] = 'Music'
            if cover_data:
                from mutagen.mp4 import MP4Cover
                cov = MP4Cover(cover_data if isinstance(cover_data, bytes) else cover_data.encode(),
                               MP4Cover.FORMAT_JPEG)
                audio['covr'] = [cov]
            audio.save()

        else:
            print(f"[*] format {ext} belum didukung metadata")
            return False

        print(f"[✓] metadata tertulis ke {Path(filepath).name}")
        return True
    except Exception as e:
        print(f"[ERR] embed_metadata: {e}")
        return False


def download_cover(url):
    """Download cover art dari URL"""
    try:
        hd_url = url.replace('w120-h120', 'w640-h640').replace('w90-h90', 'w640-h640')
        r = requests.get(hd_url, timeout=8, headers={'User-Agent': random_ua()})
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
    except Exception as e:
        print(f"[!] cover download error: {e}")
    return None


# ═══════════════════════════════════════════
#   DOWNLOAD MANAGER
# ═══════════════════════════════════════════

class DownloadManager:
    def __init__(self, download_dir):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.queue = []        # antrian
        self.active = {}       # active downloads: id -> progress_info
        self.history = []      #已完成
        self._lock = threading.Lock()

    def get_opts(self):
        return {
            'format': 'bestaudio[ext=opus]/bestaudio[ext=m4a]/bestaudio',
            'outtmpl': str(self.download_dir / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'retries': 10,
            'fragment_retries': 10,
            'user_agent': random_ua(),
            'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
            'progress_hooks': [self._progress_hook],
        }

    def _progress_hook(self, d):
        status = d.get('status', '')
        info_id = d.get('info_dict', {}).get('id', '')
        if not info_id:
            return

        with self._lock:
            if status == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                pct = (downloaded / total * 100) if total > 0 else 0
                self.active[info_id] = {
                    'pct': pct,
                    'downloaded': downloaded,
                    'total': total,
                    'speed': d.get('speed', 0),
                    'status': 'downloading',
                }
            elif status == 'finished':
                self.active[info_id] = {**self.active.get(info_id, {}), 'status': 'processing'}
            elif status == 'error':
                self.active[info_id] = {**self.active.get(info_id, {}), 'status': 'error'}

    def start_download(self, song_data, progress_callback, done_callback):
        """Mulai download di thread bg"""
        thread = threading.Thread(
            target=self._do_download,
            args=(song_data, progress_callback, done_callback),
            daemon=True,
        )
        thread.start()

    def _do_download(self, song, prog_cb, done_cb):
        if not YTDL_AVAILABLE:
            Clock.schedule_once(lambda dt: done_cb(song, False, "yt-dlp gak tersedia"))
            return

        # kalo mock, skip
        if song.get('source') == 'mock' or not song.get('url'):
            Clock.schedule_once(lambda dt: done_cb(song, False, "URL tidak valid"))
            return

        opts = self.get_opts()
        info_id = song.get('id', '')

        try:
            # ── Download ──
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(song['url'], download=True)
                filename = ydl.prepare_filename(info)

            # cari file beneran (ext bisa beda)
            downloaded_path = None
            for f in self.download_dir.iterdir():
                if info_id in f.name or (info.get('title', '') in f.name):
                    downloaded_path = f
                    break
            if not downloaded_path:
                # fallback: file terbaru
                files = sorted(self.download_dir.iterdir(), key=os.path.getmtime, reverse=True)
                downloaded_path = files[0] if files else None

            if not downloaded_path or not downloaded_path.exists():
                Clock.schedule_once(lambda dt: done_cb(song, False, "File gak ditemukan"))
                return

            # ── Metadata ──
            meta = {
                'title': info.get('title', song.get('title', '')),
                'artist': info.get('channel', info.get('uploader', song.get('artist', ''))),
                'album': info.get('album', ''),
                'year': str(info.get('release_year') or info.get('upload_date', '')[:4] if info.get('upload_date') else ''),
            }

            cover_data = None
            thumb = info.get('thumbnail') or song.get('thumb', '')
            if thumb:
                cover_data = download_cover(thumb)

            embed_metadata(str(downloaded_path), meta, cover_data)

            # rename ke .opus kalo mentok
            final_path = downloaded_path
            if downloaded_path.suffix.lower() not in ('.opus', '.m4a', '.mp3'):
                new = downloaded_path.with_suffix('.opus')
                downloaded_path.rename(new)
                final_path = new

            # ── Organisir folder: (Artis) - (Nama Album) ──
            artist_name = (meta.get('artist') or 'Unknown').strip()
            album_name = (meta.get('album') or 'Unknown').strip()
            # fallback kalo album kosong pake "Single"
            if not album_name or album_name == '' or album_name == 'Unknown':
                album_name = 'Single'

            # sanitasi karakter aneh buat folder
            def sanitize(name):
                import re
                nama = re.sub(r'[<>:"/\\|?*]', '', name)
                nama = nama.strip()
                return nama[:120]  # potong kalo kepanjangan

            artist_safe = sanitize(artist_name)
            album_safe = sanitize(album_name)
            folder_name = f"{artist_safe} - {album_safe}"
            album_dir = self.download_dir / folder_name
            album_dir.mkdir(parents=True, exist_ok=True)

            # pindahin file ke folder album
            target_path = album_dir / final_path.name
            # kalo udah ada file sama, tambahin nomor
            if target_path.exists():
                stem = final_path.stem
                count = 1
                while target_path.exists():
                    target_path = album_dir / f"{stem}_{count}{final_path.suffix}"
                    count += 1
            final_path.rename(target_path)
            final_path = target_path

            with self._lock:
                self.history.append({
                    'title': meta['title'],
                    'artist': meta['artist'],
                    'album': album_name,
                    'path': str(final_path),
                    'size': final_path.stat().st_size if final_path.exists() else 0,
                })
                if info_id in self.active:
                    del self.active[info_id]

            Clock.schedule_once(lambda dt: done_cb(song, True, meta['title']))

        except Exception as e:
            print(f"[ERR] download: {e}")
            with self._lock:
                if info_id in self.active:
                    del self.active[info_id]
            Clock.schedule_once(lambda dt: done_cb(song, False, str(e)))


# ═══════════════════════════════════════════
#   KIVYMD SCREENS
# ═══════════════════════════════════════════

class HomeScreen(MDScreen):
    def on_enter(self):
        self.refresh_home()

    def refresh_home(self):
        pass  # akan dipanggil pas search / load

    def do_search(self):
        query = self.ids.search_field.text.strip()
        if not query:
            return
        app = MDApp.get_running_app()
        app.current_query = query
        self.manager.current = 'search'


class SearchScreen(MDScreen):
    def on_enter(self):
        app = MDApp.get_running_app()
        query = getattr(app, 'current_query', '')
        if query:
            self.ids.search_title.text = f"'{query}'"
            self.ids.status_label.text = "🔍 Mencari..."
            self.ids.result_list.clear_widgets()
            # run di thread
            threading.Thread(target=self._do_search, args=(query,), daemon=True).start()

    def _do_search(self, query):
        results = search_music(query)
        Clock.schedule_once(lambda dt: self._show_results(results))

    def _show_results(self, results):
        self.ids.status_label.text = f"🎯 {len(results)} hasil ditemukan"
        self.ids.result_list.clear_widgets()

        if not results:
            self.ids.result_list.add_widget(MDLabel(
                text="Gak ada hasil. Coba kata kunci lain~",
                theme_text_color="Secondary",
                halign="center",
                size_hint_y=None,
                height=dp(60),
            ))
            return

        for song in results:
            card = SongCard(song=song)
            card.bind(on_download=lambda s=song: self._start_download(s))
            self.ids.result_list.add_widget(card)

    def _start_download(self, song):
        app = MDApp.get_running_app()
        app.download_mgr.start_download(
            song,
            progress_callback=lambda p: None,
            done_callback=lambda s, ok, msg: self._on_done(s, ok, msg),
        )
        MDSnackbar(text=f"⏳ Download: {song['title']}", duration=2).open()

    def _on_done(self, song, ok, msg):
        if ok:
            MDSnackbar(text=f"✅ {msg} selesai!", duration=3).open()
        else:
            MDSnackbar(text=f"❌ {msg}", duration=3).open()


class DownloadsScreen(MDScreen):
    def on_enter(self):
        self.refresh()

    def refresh(self):
        """Refresh the list when entering screen"""
        app = MDApp.get_running_app()
        dl = app.download_mgr
        self.ids.dl_list.clear_widgets()

        # Active
        active = list(dl.active.values())
        if active:
            for info_id, info in dl.active.items():
                item = DownloadItem(info=info)
                self.ids.dl_list.add_widget(item)

        # History
        for h in dl.history[-10:]:  # last 10
            done_item = DownloadItem(done_data=h)
            self.ids.dl_list.add_widget(done_item)

        if not active and not dl.history:
            self.ids.dl_list.add_widget(MDLabel(
                text="Belum ada download.\nCari lagu dulu yuk! 🎵",
                theme_text_color="Secondary",
                halign="center",
                size_hint_y=None,
                height=dp(100),
            ))

    def on_resume(self):
        self.refresh()


class SettingsScreen(MDScreen):
    pass


# ═══════════════════════════════════════════
#   REUSABLE WIDGETS
# ═══════════════════════════════════════════

class SongCard(MDCard):
    """Card hasil pencarian lagu"""
    def __init__(self, song, **kwargs):
        super().__init__(**kwargs)
        self.song = song
        self.size_hint_y = None
        self.height = dp(72)
        self.padding = dp(8)
        self.spacing = dp(12)
        self.radius = dp(14)
        self.orientation = "horizontal"
        self.md_bg_color = [0.11, 0.11, 0.13, 1]

        from kivymd.uix.label import MDIcon
        from kivy.uix.image import AsyncImage

        # Thumbnail / Icon
        if song.get('thumb'):
            img = AsyncImage(
                source=song['thumb'],
                size_hint=(None, 1),
                width=dp(48),
                mipmap=True,
            )
            self.add_widget(img)
        else:
            icon = MDIcon(
                icon="music-circle",
                size_hint=(None, 1),
                width=dp(48),
                font_size=dp(36),
            )
            self.add_widget(icon)

        # Info
        text_box = BoxLayout(orientation="vertical", spacing=2, size_hint_x=1)
        text_box.add_widget(MDLabel(
            text=song.get('title', ''),
            font_size=dp(14),
            bold=True,
            size_hint_y=None,
            height=dp(20),
        ))
        text_box.add_widget(MDLabel(
            text=f"{song.get('artist', '')} · {song.get('duration_str', '?')}",
            font_size=dp(12),
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(18),
        ))
        self.add_widget(text_box)

        # Download btn
        from kivymd.uix.button import MDIconButton
        btn = MDIconButton(
            icon="download",
            theme_icon_color="Custom",
            icon_size=dp(22),
            size_hint=(None, 1),
            width=dp(40),
        )
        btn.bind(on_release=lambda x: self.dispatch("on_download"))
        self.add_widget(btn)

    def on_download(self):
        pass


from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty


class SongCard(MDCard):
    def __init__(self, song=None, **kwargs):
        super().__init__(**kwargs)
        self.song = song or {}
        self.size_hint_y = None
        self.height = dp(72)
        self.padding = dp(8)
        self.spacing = dp(12)
        self.radius = dp(14)
        self.orientation = "horizontal"
        self.md_bg_color = [0.11, 0.11, 0.13, 1]
        self._build()

    def _build(self):
        from kivymd.uix.label import MDIcon
        from kivy.uix.image import AsyncImage
        from kivymd.uix.button import MDIconButton
        from kivy.uix.boxlayout import BoxLayout

        # Thumb
        thumb = self.song.get('thumb', '')
        if thumb:
            img = AsyncImage(source=thumb, size_hint=(None, 1), width=dp(48), mipmap=True)
            self.add_widget(img)
        else:
            icon = MDIcon(icon="music-circle", size_hint=(None, 1), width=dp(48), font_size=dp(36))
            self.add_widget(icon)

        # Text
        txt = BoxLayout(orientation="vertical", spacing=2, size_hint_x=1)
        txt.add_widget(MDLabel(text=self.song.get('title', ''), font_size=dp(14), bold=True, size_hint_y=None, height=dp(20)))
        txt.add_widget(MDLabel(text=f"{self.song.get('artist', '')} · {self.song.get('duration_str', '?')}",
                               font_size=dp(12), theme_text_color="Secondary", size_hint_y=None, height=dp(18)))
        self.add_widget(txt)

        # Btn
        btn = MDIconButton(icon="download", theme_icon_color="Custom", icon_size=dp(22),
                           size_hint=(None, 1), width=dp(40))
        btn.bind(on_release=lambda x: setattr(self, 'on_download', lambda: None))
        self.add_widget(btn)

    def on_download(self):
        pass


from kivy.event import EventDispatcher

class SongCardEvent(EventDispatcher):
    def __init__(self, **kwargs):
        self.register_event_type('on_download')
        super().__init__(**kwargs)


class DownloadItem(MDCard):
    """Item di halaman download"""
    def __init__(self, info=None, done_data=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(64)
        self.padding = dp(8)
        self.spacing = dp(10)
        self.radius = dp(12)
        self.orientation = "horizontal"
        self.md_bg_color = [0.11, 0.11, 0.13, 1]
        self._build(info, done_data)

    def _build(self, info, done):
        from kivy.uix.boxlayout import BoxLayout
        from kivymd.uix.label import MDIcon

        txt = BoxLayout(orientation="vertical", spacing=2, size_hint_x=1)

        if done:
            txt.add_widget(MDLabel(text=done.get('title', ''), font_size=dp(14), bold=True,
                                   size_hint_y=None, height=dp(20)))
            size_mb = done.get('size', 0) / (1024*1024)
            txt.add_widget(MDLabel(text=f"✅ {size_mb:.1f} MB · Opus 64k", font_size=dp(12),
                                   theme_text_color="Secondary", size_hint_y=None, height=dp(18)))
            icon = MDIcon(icon="check-circle-outline", theme_icon_color="Custom", icon_size=dp(28))
            self.add_widget(txt)
            self.add_widget(icon)
        elif info:
            pct = info.get('pct', 0)
            txt.add_widget(MDLabel(text=info.get('title', 'Downloading...'), font_size=dp(14), bold=True,
                                   size_hint_y=None, height=dp(20)))
            status = info.get('status', 'downloading')
            if status == 'processing':
                txt.add_widget(MDLabel(text="⏳ Processing metadata...", font_size=dp(12),
                                       theme_text_color="Secondary", size_hint_y=None, height=dp(18)))
            else:
                txt.add_widget(MDLabel(text=f"⏳ {pct:.0f}% · Opus 64k", font_size=dp(12),
                                       theme_text_color="Secondary", size_hint_y=None, height=dp(18)))
            self.add_widget(txt)
            # progress ring simpel
            icon = MDIcon(icon="progress-download", theme_icon_color="Custom", icon_size=dp(28))
            self.add_widget(icon)


# ═══════════════════════════════════════════
#   APP
# ═══════════════════════════════════════════

class MelofiApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_query = ""
        self.download_mgr = DownloadManager(
            self._get_download_dir()
        )

    def _get_download_dir(self):
        if platform == 'android':
            # Android: pake dir external
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            except:
                pass
            try:
                from android.storage import primary_external_storage_path
                base = primary_external_storage_path()
                return os.path.join(base, 'Music', 'Melofi')
            except:
                pass
        # fallback
        return os.path.join(os.path.expanduser('~'), 'Music', 'Melofi')

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.material_style = "M3"

        from kivymd.uix.navigationbar import MDBottomNavigation, MDBottomNavigationItem

        # Root layout
        from kivy.uix.screenmanager import ScreenManager
        sm = ScreenManager()

        home = HomeScreen(name='home')
        search = SearchScreen(name='search')
        downloads = DownloadsScreen(name='downloads')
        settings = SettingsScreen(name='settings')

        sm.add_widget(home)
        sm.add_widget(search)
        sm.add_widget(downloads)
        sm.add_widget(settings)

        return sm

    def on_start(self):
        pass


# ═══════════════════════════════════════════
#   MAIN
# ═══════════════════════════════════════════

if __name__ == '__main__':
    MelofiApp().run()
