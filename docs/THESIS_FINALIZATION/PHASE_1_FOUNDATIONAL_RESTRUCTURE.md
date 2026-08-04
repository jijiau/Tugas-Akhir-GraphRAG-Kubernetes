# Phase 1 — Restruktur Foundasional (Sinkronisasi 3 Tujuan)

**Status:** PENDING  
**Fase ini dikerjakan di:** Chat eksekusi terpisah (lihat plan utama)  
**Referensi Aturan Bahasa:** [Plan Utama](../../.claude/plans/act-seperti-dosen-penguji-zippy-kahn.md) — bagian "Aturan Bahasa"

---

## ⚠ REVISI (Mei 2026) — GANTIKAN BAGIAN TUJUAN/RM DI BAWAH

Arah tujuan berubah lagi. Yang berlaku sekarang (override semua teks "Mengevaluasi"→"YAML validation" lama):

**Struktur Tujuan final:**
- **T1 — Membangun** *knowledge graph* deterministik dari OpenAPI Kubernetes.
- **T2 — Mengembangkan** sistem GraphRAG: *retrieval* *intent-adaptive depth* + **validasi YAML tiga lapis berbasis KG** (validasi YAML **melebur ke T2**, bukan tujuan tersendiri).
- **T3 — Membandingkan** kinerja sistem GraphRAG terhadap Vector RAG dan Vanilla LLM untuk mengidentifikasi faktor-faktor keunggulannya. (Rumah jawaban = Bab VI.)

**Catatan penting:**
- JANGAN mengunci "presisi *retrieval* + validitas YAML" sebagai faktor pemenang di Tujuan/Latar Belakang — itu **hipotesis** (turunan judul), dijawab empiris di Bab VI/VII.
- ⚠ Risiko Kaprodi: "Membandingkan" sebagai tujuan = pembacaan literal arahan. **Konfirmasi pembimbing dulu.** Fallback Opsi A: jadikan klausa sasaran pada T2 ("...dirancang untuk meningkatkan presisi *retrieval* dan validitas YAML").
- Struktur fisik Bab IV/V (4.3/4.4/4.5) yang sudah dibuat **TIDAK dibongkar**; hanya pemetaan naratif: T1→4.3/5.2, T2→4.4+4.5/5.3+5.4, **T3→Bab VI**.

Sisa dokumen Phase 1 di bawah (judul Bab IV, restruktur section) tetap berlaku, KECUALI teks Tujuan/RM lama yang digantikan blok ini.

---

## ⚠ CONSTRAINT GLOBAL (WAJIB)

- **TA.tex TIDAK BOLEH DIUBAH** — template resmi Kaprodi ITB (IGB Baskara Nugraha)
- Semua aturan bahasa mengikuti House Style Guide di plan utama (Aturan A–H)
- Persona penulis: "Penelitian ini..." (Aturan C1)
- Range angka: en-dash (`--` di LaTeX) → "1–5" (Aturan C6)

---

## Konteks Phase 1

Phase ini memperbaiki 3 pelanggaran kritis yang teridentifikasi dari audit pedoman ITB:

1. **Tujuan ke-3 (T3)** di Bab I masih "Mengevaluasi kinerja..." → melanggar arahan Kaprodi bahwa evaluasi bukan Tujuan mandiri, melainkan metode validasi
2. **Judul Bab IV** polos `\chapter{PERANCANGAN}` → melanggar arahan deskriptif
3. **Inkonsistensi 3 Tujuan ↔ 5 subbab Bab IV/V** → melanggar prinsip sinkronisasi Tujuan↔BabIV/V/VII

### Keputusan Struktural yang Diambil

Tiga Tujuan (T1, T2, T3) yang menjadi fondasi seluruh dokumen:

| Tujuan | Label | Isi |
|--------|-------|-----|
| T1 | KG Construction | Membangun *knowledge graph* deterministik berbasis spesifikasi OpenAPI Kubernetes |
| T2 | GraphRAG + YAML Validation | Mengembangkan sistem GraphRAG (*intent-adaptive depth* + validasi YAML tiga lapis berbasis KG) |
| T3 | Perbandingan Sistem | Membandingkan kinerja GraphRAG terhadap Vector RAG & Vanilla LLM (faktor keunggulan ditentukan empiris) |

---

## File yang Dimodifikasi

| File | Perubahan |
|------|-----------|
| `Bab I - Pendahuluan.tex` | Update T3 + RM3 sesuai YAML Validation |
| `Bab IV - Perancangan.tex` | Ganti judul chapter + restruktur 3 section T1/T2/T3 |
| `Bab V - Implementasi.tex` | Restruktur 3 section T1/T2/T3 + update konten Speaker |
| `Bab VII - Penutup.tex` | Tidak diubah (sudah 3 paragraf; Phase 6 reframing detail) |

**TIDAK DIUBAH:** `TA.tex`, tabel `.tex`, gambar

---

## Detail Perubahan per File

### 1. Bab I — Update Tujuan & Rumusan Masalah (REVISI)

Catatan: T3 sempat direvisi jadi "validasi YAML"; kini direvisi LAGI. Validasi YAML pindah ke T2; T3 = perbandingan.

**Tujuan ke-2 (T2)** — sekarang mencakup validasi YAML:  
"Mengembangkan sistem GraphRAG yang menelusuri jalur relasional (*intent-adaptive depth traversal*) untuk menghasilkan jawaban sesuai logika domain Kubernetes, dilengkapi mekanisme validasi struktural YAML tiga lapis berbasis *knowledge graph* yang memverifikasi *required fields* langsung dari representasi graf."

**Tujuan ke-3 (T3)** — perbandingan (BARU):  
"Membandingkan kinerja sistem GraphRAG terhadap pendekatan Vector RAG dan Vanilla LLM untuk mengidentifikasi faktor-faktor keunggulannya."  
⚠ Jangan menulis faktor pemenang di sini (hipotesis, dijawab Bab VI/VII). Risiko Kaprodi + fallback Opsi A: lihat banner atas.

**Rumusan Masalah ke-2 (RM2):** serap validasi YAML (mekanisme GraphRAG + validasi struktural).  
**Rumusan Masalah ke-3 (RM3):**  
"Bagaimana perbandingan kinerja sistem GraphRAG terhadap Vector RAG dan Vanilla LLM di seluruh faktor evaluasi?"

### 2. Bab IV — Chapter Title + Restruktur Section

**Chapter title:**  
- LAMA: `\chapter{PERANCANGAN}`  
- BARU: `\chapter{PERANCANGAN SISTEM \textit{GRAPHRAG} BERBASIS \textit{KNOWLEDGE GRAPH} KUBERNETES}`

**Struktur baru Bab IV:**

```
4.1  Rancangan Solusi Secara Garis Besar          [tidak berubah]
4.2  Pemetaan Metodologi terhadap Kebutuhan Sistem  [tidak berubah]
4.3  Perancangan Pipeline Ekstraksi dan Knowledge Graph  [T1 — BARU]
     4.3.1  Pipeline Ingestion Data                [dari 4.3.1]
4.4  Perancangan Mekanisme GraphRAG                 [T2 — BARU]
     4.4.1  Perancangan LangGraph Agent Pipeline    [dari 4.3.2]
     4.4.2  Perancangan Mekanisme Retrieval Bertingkat [dari 4.3.3]
     4.4.3  Perancangan Antarmuka Web Streamlit     [dari 4.3.5]
4.5  Perancangan Validasi YAML Tiga Lapis           [T3 — BARU]
     (konten dari 4.3.4)
```

### 3. Bab V — Restruktur Section + Update Konten

**Konten yang perlu diperbarui selain struktur:**
- Line ~41: Hapus referensi "Groq llama-3.1-8b-instant" → ganti ke "GPT-4o-mini" (sudah di-switch sejak Mei 2026)
- Line ~42: Hapus batas konteks "12.000 karakter via Groq tier gratis" → sesuaikan dengan batas GPT-4o-mini

**Struktur baru Bab V:**

```
5.1  Lingkungan Implementasi                        [tidak berubah]
5.2  Implementasi Pipeline Ekstraksi dan Knowledge Graph [T1 — BARU]
     5.2.1  [konten dari 5.2 lama]
5.3  Implementasi Mekanisme GraphRAG               [T2 — BARU]
     5.3.1  Implementasi Pipeline LangGraph          [dari 5.3]
     5.3.2  Implementasi Mekanisme Retrieval Bertingkat [dari 5.4]
     5.3.3  Implementasi Antarmuka Pengguna          [dari 5.6]
5.4  Implementasi Validasi YAML Tiga Lapis          [T3 — BARU]
     (konten dari 5.5)
```

---

## Checklist Verifikasi Phase 1

- [ ] Bab I: T3 = "Membandingkan" (perbandingan 3 sistem); validasi YAML ada di T2
- [ ] Bab I: RM3 = pertanyaan komparatif; konsisten dengan T3
- [ ] Bab I: 3 Tujuan ↔ 3 Rumusan Masalah (satu-ke-satu)
- [ ] Bab I: tidak ada faktor pemenang yang dipra-tulis (hipotesis, bukan klaim)
- [ ] Bab IV: Chapter title deskriptif (bukan hanya "PERANCANGAN")
- [ ] Bab IV: Ada 3 `\section{}` untuk T1, T2, T3 (selain 4.1 dan 4.2)
- [ ] Bab IV: Subseksi 4.3.1–4.3.5 lama sudah jadi `\subsection{}` di bawah T1/T2/T3 baru
- [ ] Bab V: Ada 3 `\section{}` untuk T1, T2, T3 (selain 5.1)
- [ ] Bab V: Referensi "Groq llama-3.1-8b-instant" sudah diganti GPT-4o-mini
- [ ] Tidak ada konten yang hilang (hanya dipindah/dibungkus)
- [ ] Semua `\label{}` lama masih ada
- [ ] Sinkronisasi: T1→Bab IV/V, T2→Bab IV/V (incl. validasi YAML), T3→Bab VI

---

## Catatan untuk Phase Selanjutnya

- **Phase 2** (Bab I lengkap): Tambah subbab "Sistematika Penulisan", reframing Latar Belakang dengan 3 Klaim
- **Phase 4** (Bab IV/V detail): Isi konten substantif per T1/T2/T3, diagram baru, justifikasi design decision
- **Phase 6** (Bab VII): Reframing 3 paragraf kesimpulan secara detail per T1/T2/T3, tambah keterbatasan dan angka v13
