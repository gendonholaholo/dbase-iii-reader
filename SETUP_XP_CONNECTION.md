# Tutorial: Menghubungkan Windows XP ke Mac untuk Claude Code

## Tujuan
Mengakses seluruh drive C:\ Windows XP dari Mac agar Claude Code bisa menganalisis aplikasi DOS dan data secara langsung.

---

## BAGIAN 1: Setup di Windows XP

### Opsi A: Via GUI

1. Buka **My Computer**
2. Klik kanan **C:\** → **Sharing and Security**
3. Jika muncul warning, klik **"If you understand the risk but still want to share..."**
4. Centang **"Share this folder on the network"**
5. Isi nama share: `DATA` (atau nama lain)
6. Centang **"Allow network users to change my files"** (opsional)
7. Klik **OK**

### Opsi B: Via Command Prompt (Lebih Cepat)

1. Buka **Start → Run** (atau tekan `Win + R`)
2. Ketik `cmd` lalu Enter
3. Jalankan perintah:

```cmd
net share DATA=C:\ /grant:everyone,full
```

### Cek IP Address XP

Di Command Prompt, jalankan:

```cmd
ipconfig
```

Catat **IP Address** (contoh: `192.168.1.100`)

---

## BAGIAN 2: Setup di Mac

### Langkah 1: Buat Mount Point

Buka Terminal di Mac, jalankan:

```bash
sudo mkdir -p /Volumes/xp_c
```

### Langkah 2: Mount Share dari XP

Ganti `IP_XP` dengan IP address yang dicatat tadi:

```bash
# Tanpa password (guest access)
sudo mount_smbfs //guest@IP_XP/DATA /Volumes/xp_c

# Dengan username/password
sudo mount_smbfs //username:password@IP_XP/DATA /Volumes/xp_c

# Contoh nyata:
sudo mount_smbfs //guest@192.168.1.100/DATA /Volumes/xp_c
```

### Langkah 3: Verifikasi

```bash
ls /Volumes/xp_c
```

Harus muncul isi drive C:\ dari XP.

---

## BAGIAN 3: Akses via Finder (Alternatif)

1. Buka **Finder**
2. Tekan **Cmd + K**
3. Ketik: `smb://IP_XP/DATA`
4. Klik **Connect**
5. Pilih **Guest** atau masukkan username/password
6. Share akan muncul di sidebar Finder

---

## BAGIAN 4: Gunakan Claude Code

Setelah mount berhasil, jalankan Claude Code:

```bash
cd /Volumes/xp_c
claude
```

Atau langsung analisis:

```bash
claude "Analisis struktur aplikasi DOS di /Volumes/xp_c"
```

---

## Troubleshooting

### XP tidak terlihat di jaringan
- Pastikan kedua mesin di subnet yang sama
- Cek firewall XP: Control Panel → Windows Firewall → matikan sementara
- Ping dari Mac: `ping IP_XP`

### Mount gagal
- Coba dengan IP langsung, bukan hostname
- Pastikan share sudah aktif: di XP jalankan `net share` untuk cek

### Permission denied
- Pastikan "Allow network users to change my files" dicentang
- Coba dengan username/password admin XP

### Unmount share
```bash
sudo umount /Volumes/xp_c
```

---

## Catatan Keamanan

- Share C:\ hanya di jaringan lokal yang aman
- Jangan expose ke internet
- Setelah selesai, bisa hapus share:
  ```cmd
  net share DATA /delete
  ```

---

## Quick Reference

| Langkah | Perintah |
|---------|----------|
| Share C:\ di XP | `net share DATA=C:\ /grant:everyone,full` |
| Cek IP di XP | `ipconfig` |
| Mount di Mac | `sudo mount_smbfs //guest@IP/DATA /Volumes/xp_c` |
| Unmount di Mac | `sudo umount /Volumes/xp_c` |
| Hapus share di XP | `net share DATA /delete` |
