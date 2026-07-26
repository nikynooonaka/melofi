[app]

# Nama aplikasi yang muncul di layar HP
title = Melofi

package.name = melofi
package.domain = com.melofi

# Source code
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,md

# Versi
version = 1.0.0
version.code = 1

# Requirements (dependencies Python)
requirements = python3,kivy==2.3.0,kivymd==2.0.0,yt-dlp,requests,mutagen,Pillow

# Orientation
orientation = portrait

# Android SDK (biarkan buildozer download sendiri)
android.api = 33
android.minapi = 21
android.ndk = 25c
android.sdk = 34

# Izin Android
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE

# Biar APK-nya gak terlalu gede
android.archs = arm64-v8a
android.wakelock = True

# Bundle ffmpeg biar bisa konversi audio & embed metadata
android.add_src = .
android.gradle_dependencies = 'androidx.core:core:1.9.0'

# Metadata
android.google_play_key = 
android.google_play_salt = 

# Bundle icon (nanti bisa diganti)
# icon = icon.png
# presplash = splash.png

# Build settings
android.allow_backup = False
android.fullscreen = 0
android.enable_androidx = True

ios.codesign.provision_file = 
ios.codesign.identity = 
ios.codesign.entitlements = 

# Python untuk ARM
android.python_version = 3

# Biar APK ukurannya lebih kecil
android.copy_libs = True
android.bluetooth = False
android.speech = False
android.gps = False
android.headsets = True
android.assist = True

# ======== BUILD COMMAND ========
# buildozer android debug
