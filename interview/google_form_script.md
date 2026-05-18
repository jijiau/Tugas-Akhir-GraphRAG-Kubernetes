# Script Google Form — Lembar Penilaian Narasumber

**Panduan setup**: Buat Google Form baru, aktifkan "Require sign-in" jika perlu, aktifkan "Multiple sections". Judul form: **"Evaluasi Sistem GraphRAG Kubernetes — Wawancara Validasi"**

Deskripsi form:
> Terima kasih atas partisipasi Anda. Form ini diisi sambil melihat demonstrasi sistem — ikuti arahan pewawancara untuk setiap bagian.

---

## SECTION 0 — Profil

**Judul section**: Profil Narasumber

| No | Pertanyaan | Tipe Field |
|----|-----------|------------|
| 0.1 | Inisial nama Anda | Short answer (required) |
| 0.2 | Peran/jabatan saat ini | Short answer (required) |
| 0.3 | Tanggal wawancara | Date picker (required) |

---

## SECTION 1 — Skenario S1: Generate YAML StatefulSet

**Judul section**: Skenario 1: Generate YAML StatefulSet + PVC

**Deskripsi section**:
> Pewawancara akan mendemonstrasikan sistem menjawab permintaan: **"Buat YAML StatefulSet untuk database MySQL dengan PersistentVolumeClaim 10Gi"**. Perhatikan output YAML dan Retrieval Trace, lalu isi penilaian berikut.

| No | Pertanyaan | Tipe Field | Skala / Pilihan |
|----|-----------|------------|-----------------|
| 1.1 | **Relevansi** — Apakah jawaban sistem menjawab pertanyaan yang diajukan? | Linear scale | 1 = Sama sekali tidak menjawab → 5 = Sangat relevan dan lengkap |
| 1.2 | **Akurasi Teknis** — Apakah informasi Kubernetes dalam jawaban ini benar secara teknis? | Linear scale | 1 = Banyak kesalahan teknis → 5 = Akurat sepenuhnya |
| 1.3 | **Kelengkapan** — Apakah semua komponen penting untuk kebutuhan ini sudah tercakup? | Linear scale | 1 = Banyak yang kurang → 5 = Sangat lengkap |
| 1.4 | **Kesediaan Pakai** — Apakah output ini bisa langsung digunakan di pekerjaan tanpa modifikasi signifikan? | Linear scale | 1 = Perlu banyak perbaikan → 5 = Bisa langsung dipakai |
| 1.5 | Komentar atau catatan untuk skenario ini (opsional) | Paragraph | — |

---

## SECTION 2 — Skenario S2: Troubleshooting CrashLoopBackOff

**Judul section**: Skenario 2: Troubleshooting Pod OOMKilled

**Deskripsi section**:
> Pewawancara akan mendemonstrasikan sistem menjawab: **"Pod saya terus masuk ke status CrashLoopBackOff dan di Last State tertulis reason: OOMKilled. Apa penyebabnya dan bagaimana mengatasinya?"**. Perhatikan jawaban sistem, lalu isi penilaian berikut.

| No | Pertanyaan | Tipe Field | Skala / Pilihan |
|----|-----------|------------|-----------------|
| 2.1 | **Relevansi** — Apakah jawaban sistem menjawab pertanyaan yang diajukan? | Linear scale | 1 = Sama sekali tidak menjawab → 5 = Sangat relevan dan lengkap |
| 2.2 | **Akurasi Teknis** — Apakah penyebab dan solusi yang disebutkan benar secara teknis? | Linear scale | 1 = Banyak kesalahan teknis → 5 = Akurat sepenuhnya |
| 2.3 | **Kelengkapan** — Apakah langkah troubleshooting yang diberikan cukup komprehensif? | Linear scale | 1 = Banyak yang kurang → 5 = Sangat lengkap |
| 2.4 | **Kesediaan Pakai** — Apakah jawaban ini bisa langsung Anda ikuti untuk troubleshoot masalah serupa? | Linear scale | 1 = Perlu banyak perbaikan → 5 = Bisa langsung diikuti |
| 2.5 | Komentar atau catatan untuk skenario ini (opsional) | Paragraph | — |

---

## SECTION 3 — Skenario S3: Relasi Deployment–ReplicaSet–Pod

**Judul section**: Skenario 3: Relasi Antar-Komponen Kubernetes

**Deskripsi section**:
> Pewawancara akan mendemonstrasikan sistem menjawab: **"Bagaimana hubungan antara Deployment, ReplicaSet, dan Pod di Kubernetes?"**. Perhatikan jawaban dan fitur **Retrieval Trace** (grafik yang menunjukkan dari mana sistem mengambil informasi), lalu isi penilaian berikut.

| No | Pertanyaan | Tipe Field | Skala / Pilihan |
|----|-----------|------------|-----------------|
| 3.1 | **Relevansi** — Apakah jawaban sistem menjawab pertanyaan yang diajukan? | Linear scale | 1 = Sama sekali tidak menjawab → 5 = Sangat relevan dan lengkap |
| 3.2 | **Akurasi Teknis** — Apakah penjelasan hubungan antar-komponen ini benar secara teknis? | Linear scale | 1 = Banyak kesalahan teknis → 5 = Akurat sepenuhnya |
| 3.3 | **Kelengkapan** — Apakah penjelasan ini cukup untuk dipahami oleh rekan kerja yang baru mulai belajar Kubernetes? | Linear scale | 1 = Sangat tidak lengkap → 5 = Sangat lengkap dan jelas |
| 3.4 | **Kesediaan Pakai** — Apakah penjelasan ini bisa langsung Anda gunakan sebagai referensi? | Linear scale | 1 = Tidak berguna → 5 = Bisa langsung dipakai sebagai referensi |
| 3.5 | Komentar atau catatan untuk skenario ini (opsional) | Paragraph | — |

---

## SECTION 4 — Penilaian Fitur Retrieval Trace

**Judul section**: Penilaian Fitur Retrieval Trace

**Deskripsi section**:
> Retrieval Trace adalah fitur yang menampilkan "dari mana sistem mengambil informasi" — berupa grafik node Kubernetes dan daftar relasi yang ditelusuri. Anda sudah melihat fitur ini saat demonstrasi tadi.

| No | Pertanyaan | Tipe Field | Skala / Pilihan |
|----|-----------|------------|-----------------|
| 4.1 | Seberapa mudah informasi di Retrieval Trace untuk dibaca dan dipahami? | Linear scale | 1 = Sangat sulit dipahami → 5 = Sangat mudah dipahami |
| 4.2 | Apakah fitur Retrieval Trace meningkatkan kepercayaan Anda terhadap jawaban sistem? | Linear scale | 1 = Tidak berpengaruh sama sekali → 5 = Sangat meningkatkan kepercayaan |
| 4.3 | Seberapa sering Anda akan membuka Retrieval Trace jika menggunakan sistem ini sehari-hari? | Multiple choice | Tidak pernah / Hanya saat jawaban meragukan / Kadang-kadang / Selalu untuk setiap jawaban |
| 4.4 | Komentar tentang fitur Retrieval Trace (opsional) | Paragraph | — |

---

## SECTION 5 — Pertanyaan Terbuka

**Judul section**: Pertanyaan Reflektif

**Deskripsi section**:
> Tidak ada jawaban benar atau salah. Jawab berdasarkan pengalaman dan perspektif Anda sebagai praktisi.

| No | Pertanyaan | Tipe Field |
|----|-----------|------------|
| 5.1 | Menurut Anda, apa **kelebihan terbesar** dari sistem ini dibandingkan cara Anda biasanya mencari informasi Kubernetes? | Paragraph (required) |
| 5.2 | Apa **keterbatasan atau kelemahan** paling signifikan yang Anda rasakan dari sistem ini? | Paragraph (required) |
| 5.3 | Untuk YAML yang digenerate sistem (seperti di Skenario 1): apakah menurut Anda output-nya **production-ready**, atau perlu modifikasi apa sebelum dipakai? | Paragraph (required) |
| 5.4 | Jenis pertanyaan Kubernetes apa yang menurut Anda **masih kurang baik** ditangani oleh sistem ini? | Paragraph |
| 5.5 | Apakah Anda akan **menggunakan sistem ini** dalam pekerjaan sehari-hari? Mengapa atau mengapa tidak? | Paragraph (required) |

---

## CATATAN SETUP GOOGLE FORM

- **Section navigation**: Semua section berurutan, tidak perlu conditional logic
- **Required fields**: Tandai required di 0.1, 0.2, 0.3, semua Linear scale (1.1–4.2), dan 5.1, 5.2, 5.3, 5.5
- **Collect email**: Matikan (anonymous responses lebih nyaman untuk narasumber)
- **Progress bar**: Aktifkan agar narasumber tahu sudah sampai mana
- **Confirmation message**: "Terima kasih atas penilaian Anda! Masukan ini sangat berharga untuk penelitian ini."
- **Response limit**: 1 response per session sudah cukup (tidak perlu dibatasi)
