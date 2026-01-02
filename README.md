# dBase III Reader

Aplikasi untuk mengkonversi file database lama (`.DAT`, `.DTA`) ke Excel.

---

## Instalasi (Hanya Sekali)

### Windows

1. **Buka PowerShell** (tekan `Win + X`, pilih "Windows PowerShell")

2. **Copy-paste perintah ini**, lalu tekan Enter:
   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Tutup PowerShell**, buka lagi

4. **Download aplikasi ini** dari GitHub (klik tombol hijau "Code" → "Download ZIP"), lalu extract

---

## Cara Pakai

### 1. Buka PowerShell

Tekan `Win + X` → pilih "Windows PowerShell"

### 2. Masuk ke folder aplikasi

```
cd C:\Users\NAMA_USER\Downloads\dbase-iii-reader-main
```
*(Ganti `NAMA_USER` dengan nama user Windows kamu)*

### 3. Jalankan aplikasi

```
uv run app.py
```

Tunggu sampai muncul tulisan seperti ini:
```
Running on local URL: http://127.0.0.1:7860
```

### 4. Buka browser

Buka **Chrome/Edge/Firefox**, ketik di address bar:
```
localhost:7860
```

### 5. Gunakan aplikasi

1. Klik area **"Upload File"**
2. Pilih file `.DAT` atau `.DTA`
3. Klik **"Preview"** untuk lihat isi
4. Klik **"Export ke Excel"** untuk download

---

## Menutup Aplikasi

Di PowerShell, tekan `Ctrl + C`

---

## Format File yang Didukung

| File | Deskripsi |
|------|-----------|
| `.DTA` | Data transaksi (dBase III) |
| `.DAT` | Data stok/barcode |

---

## Troubleshooting

**Muncul error saat install uv?**
→ Pastikan PowerShell dibuka sebagai Administrator

**Browser tidak bisa buka localhost:7860?**
→ Pastikan aplikasi sudah jalan (ada tulisan "Running on local URL")

**File tidak bisa dibaca?**
→ Pastikan file tidak corrupt dan formatnya `.DAT` atau `.DTA`
