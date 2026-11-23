# Sales Insight — tes AI Builder Dua Kelinci

Aplikasi web kecil dari `sales.csv` (Sep–Okt 2026):

1. **Penjualan per region dan per brand**: bulan ini dibanding bulan lalu, dalam bentuk grafik dan tabel.
2. **5 outlet terlemah**, lengkap dengan alasan kenapa masuk daftar.
3. **Ringkasan satu paragraf** untuk sales manager yang bisa dikirim ke **Telegram** (tombol di dashboard atau lewat CLI untuk cron).

## Cara menjalankan

Butuh Python 3.10 atau lebih baru.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py               # buka http://localhost:8501
```

Dashboard langsung jalan tanpa konfigurasi apa pun. Untuk Claude dan Telegram, salin `.env.example` menjadi `.env` lalu isi:

| Variabel | Untuk apa | Kalau kosong |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude menulis paragraf ringkasan | Paragraf ditulis dengan template |
| `TELEGRAM_BOT_TOKEN` | Token bot dari @BotFather | Tombol kirim memberi pesan cara mengisinya |
| `TELEGRAM_CHAT_ID` | Chat/grup tujuan | sama |

Cari `TELEGRAM_CHAT_ID`: isi token dulu, kirim pesan apa saja ke bot, lalu jalankan `python get_chat_id.py`.

Kirim ringkasan tanpa membuka dashboard (cocok untuk cron harian):

```bash
python send_summary.py --dry-run     # cetak saja
python send_summary.py               # tulis + kirim ke Telegram
python send_summary.py --no-claude   # pakai template, tanpa panggilan API
```

Tes:

```bash
pytest
```

### Deploy (Docker / Coolify)

```bash
docker build -t sales-insight .
docker run -p 8501:8501 --env-file .env sales-insight
```

Di Coolify: Build Pack **Dockerfile**, port **8501**, isi variabel dari `.env.example` di tab Environment Variables. Kalau dashboard bisa dibuka publik, **isi `APP_PASSWORD`**. Pengunjung tanpa password tetap bisa melihat grafik, tabel, dan ringkasan template, tapi Claude dan tombol kirim Telegram terkunci.

## Data yang dirapikan

Datanya tidak bersih. Semua perbaikan dihitung dan ditampilkan di dashboard (bagian *Kualitas data*), tidak dilakukan diam-diam.

| Temuan | Jumlah | Penanganan |
|---|---|---|
| Baris duplikat persis (invoice, SKU, dan semua kolom sama) | 3 | Dibuang. Tanpa ini penjualan terhitung dobel. |
| Penulisan region tidak seragam (`JABODETABEK`, `JAWA BARAT`, `Jabar`, `JAWA TIMUR`) | 10 baris | Disatukan ke 6 region. Region baru yang tidak dikenal dibiarkan apa adanya dan dilaporkan. |
| Nama outlet dengan spasi di belakang | 4 baris | Di-*trim*. |
| Satu nama outlet dipakai beberapa `outlet_id` (mis. "Toko Sinar Abadi" di 3 cabang) | 8 nama | Semua hitungan memakai `outlet_id`. Label tampilan = nama · cabang. |
| Salesman kosong | 5 baris | Ditandai `(tidak diisi)`, penjualannya tetap dihitung. |
| Retur (qty −2, invoice `RTR…`) | 1 baris | Tetap dihitung sebagai pengurang penjualan bersih, karena memang barang kembali. |
| Cek aritmetika: gross = qty × harga, net = gross − diskon | 0 selisih | Lolos. |

Semua angka memakai `net_sales_idr` (setelah diskon).

## Definisi "outlet terlemah"

Kalau peringkatnya pakai rupiah mentah, hasilnya cuma daftar warung terkecil. Rata-rata Grosir menjual sekitar 10× Warung. Padahal yang dibutuhkan manager adalah outlet yang **kinerjanya di bawah standar untuk jenisnya**.

Karena itu setiap outlet dibandingkan dengan **outlet setipe** (Grosir / Minimarket / Toko Kelontong / Warung):

```
skor = penjualan bersih outlet bulan ini / median penjualan bulan ini untuk tipe outletnya
```

- Lima skor terendah = 5 outlet terlemah. Kalau skornya sama, yang penurunannya dari bulan lalu paling besar didahulukan.
- Outlet yang order bulan lalu tapi **tidak order sama sekali** bulan ini dapat skor 0, jadi otomatis paling atas. Ini sinyal paling penting buat sales.
- "Bulan ini" = bulan terakhir di data (Oktober 2026), dibanding bulan sebelumnya.
- Filter region, brand, dan tipe outlet di sidebar ikut mengubah daftar ini.

Hasil untuk Oktober 2026: kelima outlet terlemah semuanya hanya 5–12% dari median tipenya. Tabel juga menampilkan perubahan dari September, karena sebagian sebenarnya naik dari basis yang sangat kecil. Artinya masalahnya di volume, bukan tren.

## Ringkasan dan Claude

- **Semua angka dihitung di kode** (`salesinsight/summary.py → build_facts`) lalu diberikan ke penulis sebagai JSON.
- Penulisnya **Claude** (`claude-opus-5-5`, effort `low`, fallback server-side aktif) dengan instruksi untuk memakai angka persis seperti yang diberikan dan tidak menghitung sendiri. Ini mencegah angka halusinasi di pesan yang dibaca manager.
- Kalau kredensial tidak ada, jaringan putus, atau permintaannya ditolak, aplikasi otomatis memakai **template** yang menghasilkan paragraf setara. Pengiriman ke Telegram tidak pernah gagal gara-gara LLM.
- Paragraf bisa diedit dulu di dashboard sebelum dikirim.

Contoh paragraf template untuk data ini:

> Ringkasan penjualan Oktober 2026: total Rp878,4 jt (+3,6% dari September 2026). Jabodetabek masih region terbesar (Rp256,8 jt) dan Kacang Dua Kelinci brand terlaris (Rp376,2 jt). Jawa Timur tumbuh paling cepat (+92%), sedangkan Jawa Barat turun paling dalam (−14%); penurunan rupiah terbesar ada di cabang Bandung (−Rp31,2 jt). Lima outlet terlemah dibanding outlet setipenya: Toko Anugerah · Banjarmasin (Rp360 rb), Toko Sinar Abadi · Jakarta Barat (Rp372 rb), Toko Mulia · Solo (Rp504 rb), Warung Maju Lancar · Malang (Rp744 rb), Toko Mandiri · Palembang (Rp870 rb); mohon salesman terkait mengunjungi dan mengecek stok serta kendala order minggu ini.

## Struktur

```
app.py                    dashboard Streamlit
send_summary.py           CLI: ringkasan → Telegram (untuk cron)
get_chat_id.py            bantu cari TELEGRAM_CHAT_ID
Dockerfile                image untuk Docker / Coolify
salesinsight/data.py      baca + rapikan CSV, laporan kualitas data
salesinsight/metrics.py   agregasi region/brand, peringkat outlet terlemah
salesinsight/summary.py   fakta → paragraf (Claude atau template)
salesinsight/telegram.py  kirim lewat Bot API (library standar saja)
salesinsight/fmt.py       format Rupiah dan persen gaya Indonesia
tests/                    15 tes (pembersihan data, peringkat, fallback, format)
data/sales.csv            data tes
```

## Catatan untuk dipakai sungguhan

- **Satu temuan yang perlu dicek ke lapangan:** Jawa Timur naik 92% karena Malang (Rp41 jt → Rp103 jt). Hampir semua kenaikannya dari Grosir Lancar Jaya, dan naiknya merata di semua brand. Polanya mirip program atau promo baru, bukan salah input. Tapi tetap perlu dikonfirmasi sebelum dijadikan target.
- Untuk export QAD harian, `send_summary.py` bisa dijalankan lewat cron atau launchd setelah file export masuk.
- Mengirim ke Microsoft Teams cukup dengan mengganti `telegram.py` dengan *incoming webhook*. Bagian lain tidak perlu diubah.
