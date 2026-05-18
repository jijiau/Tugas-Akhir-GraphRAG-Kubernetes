# Panduan Pewawancara — Interview Kedua: Validasi Sistem GraphRAG Kubernetes

**Untuk**: Pewawancara (Jihan)  
**Durasi**: 30–45 menit  
**Narasumber**: N1 / N2 / N3 (sama seperti interview pertama)

---

## CHECKLIST PERSIAPAN (sebelum sesi)

- [ ] Laptop sudah nyala, koneksi internet stabil
- [ ] Jalankan sistem: `streamlit run main.py` dari terminal
- [ ] Verifikasi sistem berjalan normal: buka `http://localhost:8501`, kirim 1 pertanyaan test
- [ ] Buka file `skenario_demo.md` di tab/window terpisah sebagai referensi
- [ ] Kirim link Google Form ke narasumber sebelum sesi (atau buka di tab browser narasumber)
- [ ] Siapkan notepad fisik untuk catatan observasi non-verbal
- [ ] Tes rekaman audio/video jika ada

---

## SEGMEN 0 — PEMBUKAAN (3–5 menit)

**Script:**

> "Terima kasih sudah luangkan waktu lagi. Hari ini kita akan evaluasi hasil dari sistem yang sudah saya bangun — bukan lagi menilai pertanyaannya seperti dulu, tapi menilai **kualitas jawaban sistem-nya**.
>
> Saya akan menunjukkan tiga contoh pertanyaan yang sudah saya jalankan ke sistem, dan nanti ada sesi di mana kamu bisa coba sendiri. Tidak ada jawaban benar/salah — yang saya butuhkan adalah perspektif kamu sebagai praktisi: apakah jawaban ini berguna dan akurat di dunia nyata?
>
> Boleh saya rekam sesi ini untuk keperluan penelitian?"

**Minta konfirmasi rekaman**, lalu lanjut.

---

## SEGMEN 1 — DEMO OUTPUT + PENILAIAN (18–20 menit)

> Untuk setiap skenario: buka chatbot, ketik pertanyaannya live (atau tampilkan output dari file demo), tunggu respons muncul, lalu tunjukkan Retrieval Trace di bagian bawah.

### Skenario S1 — Generate YAML StatefulSet (~6 menit)

**Script pengantar:**
> "Skenario pertama: permintaan generate YAML. Ini jenis pertanyaan yang paling sering muncul di kerjaan. Saya ketik pertanyaannya sekarang."

**Ketik ke chatbot:**
```
Buat YAML StatefulSet untuk database MySQL dengan PersistentVolumeClaim 10Gi
```

**Setelah output muncul, sorot:**
- Klik tombol copy YAML di kanan atas code block
- Scroll ke bawah, buka tab **Retrieval Trace** → tunjukkan daftar node yang dilalui
- Tunjukkan tab **Graph** (visualisasi)

**Minta narasumber isi Google Form — Section 1 (Skenario S1)**

**Probing jika diam:**
- *"Menurut kamu YAML ini bisa langsung di-`kubectl apply` atau butuh modifikasi dulu?"*
- *"Ada bagian yang menurutmu kurang atau salah secara teknis?"*

---

### Skenario S2 — Troubleshooting CrashLoopBackOff (~7 menit)

**Script pengantar:**
> "Skenario kedua: troubleshooting. Ini yang tadi kamu sebut paling sering kamu gunakan LLM untuk ini."

**Ketik ke chatbot:**
```
Pod saya terus masuk ke status CrashLoopBackOff dan ketika saya cek dengan kubectl describe pod, di bagian Last State tertulis reason: OOMKilled. Apa yang menyebabkan ini dan bagaimana cara mengatasinya?
```

**Setelah output muncul, sorot:**
- Apakah sistem menyebut `resources.limits.memory` secara eksplisit?
- Buka Retrieval Trace → lihat berapa node yang ditraversal
- Tunjukkan bahwa sistem mengaitkan OOMKilled ke Container → ResourceRequirements → limits

**Minta narasumber isi Google Form — Section 2 (Skenario S2)**

**Probing jika diam:**
- *"Apakah langkah-langkah troubleshooting yang diberikan ini sudah dalam urutan yang benar menurutmu?"*
- *"Adakah konteks tambahan yang biasanya kamu berikan ke LLM supaya jawaban lebih spesifik?"*

---

### Skenario S3 — Relasi Deployment–ReplicaSet–Pod (~6 menit)

**Script pengantar:**
> "Skenario ketiga: pertanyaan relasi. Ini menguji apakah sistem bisa menjelaskan hubungan antar-komponen Kubernetes yang saling terhubung."

**Ketik ke chatbot:**
```
Bagaimana hubungan antara Deployment, ReplicaSet, dan Pod di Kubernetes?
```

**Setelah output muncul, sorot:**
- Buka Retrieval Trace → tunjukkan chain: Deployment → ReplicaSet → Pod
- Tunjukkan tab **Graph** — ada visualisasi node dan edge-nya
- Tunjukkan berapa "hop" yang dilalui sistem (tertera di bagian atas Retrieval Trace)

**Minta narasumber isi Google Form — Section 3 (Skenario S3)**

**Probing jika diam:**
- *"Apakah penjelasan hubungan ini sudah cukup untuk kamu jadikan referensi ketika debugging masalah Deployment?"*

---

## SEGMEN 2 — EKSPLORASI MANDIRI (7–10 menit)

**Script:**
> "Sekarang giliranmu. Silakan ketik pertanyaan apapun tentang Kubernetes yang biasa kamu tanyakan di kerjaan — bisa troubleshooting, minta buatkan YAML, tanya relasi komponen, apapun."

Jika narasumber blank, tawarkan pilihan dari list di bawah:
- *"Mau coba tanya tentang masalah yang pernah kamu hadapi di cluster?"*
- *"Atau mau minta sistem buatkan YAML untuk sesuatu yang biasa kamu konfigurasi?"*

**Setelah mengetik pertanyaan dan melihat output:**
> "Sekarang coba buka **Retrieval Trace** di bawah jawaban. Ini menunjukkan dari node mana sistem mengambil informasi untuk menjawab pertanyaan kamu."

**Minta narasumber isi Google Form — Section 4 (Retrieval Trace)**

**Catatan observasi untuk kamu:** Perhatikan apakah narasumber spontan membuka Retrieval Trace sendiri, atau butuh dipandu.

---

## SEGMEN 3 — DISKUSI TERBUKA + PENUTUP (8–10 menit)

**Script:**
> "Hampir selesai. Ada beberapa pertanyaan reflektif — ini yang paling penting buat penelitian saya. Mohon dijawab sejujurnya."

**Minta narasumber selesaikan Google Form — Section 5 (Pertanyaan Terbuka)**

Beri waktu ~5 menit untuk mengisi. Boleh sambil diisi secara lisan.

**Setelah form selesai:**
> "Ada hal lain yang ingin kamu tambahkan atau komentari soal sistem ini yang belum tercakup di form?"

**Kalimat penutup:**
> "Terima kasih banyak, masukannya sangat berharga untuk penelitian saya. Kalau nanti saya butuh klarifikasi dari hasilnya, boleh saya hubungi lagi?"

---

## CATATAN OBSERVASI (isi selama sesi)

| Waktu | Narasumber | Observasi |
|-------|-----------|-----------|
| Segmen 1 S1 | | |
| Segmen 1 S2 | | |
| Segmen 1 S3 | | |
| Segmen 2 | | |
| Segmen 3 | | |

**Hal yang perlu dicatat:**
- Reaksi spontan saat melihat output (ekspresi setuju/ragu/heran)
- Apakah narasumber membaca Retrieval Trace tanpa diminta?
- Kata-kata yang digunakan untuk mendeskripsikan kelemahan sistem
- Pertanyaan yang diketik saat eksplorasi mandiri
