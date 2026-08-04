# Phase 2 — Bab I Lengkap: Reframing + Sistematika Penulisan

**Status:** PENDING  
**Prasyarat:** Phase 1 selesai (Tujuan T1/T2/T3 sudah direvisi di Bab I)  
**Referensi Aturan Bahasa:** [Plan Utama](../../.claude/plans/act-seperti-dosen-penguji-zippy-kahn.md) — bagian "Aturan Bahasa"

---

## ⚠ REVISI (Mei 2026) — penyesuaian arah

Latar Belakang tetap memaparkan celah teknis & kontribusi, TAPI:
- Kontribusi teknis dikelompokkan ke **T1** (KG deterministik) & **T2** (GraphRAG *intent-adaptive depth* + validasi YAML). Validasi YAML = bagian T2, bukan kontribusi/tujuan terpisah.
- Peningkatan **presisi *retrieval* + validitas YAML** ditulis sebagai **hipotesis/ekspektasi** yang akan **dibandingkan** terhadap Vector RAG & Vanilla LLM (T3), **bukan** klaim hasil. Hindari kalimat "sistem ini unggul/lebih baik" di Latar Belakang.
- "3 Klaim" di bawah dibaca sebagai 2 kontribusi sistem (T1, T2) + 1 sasaran perbandingan (T3) yang dijawab empiris di Bab VI.

---

## ⚠ CONSTRAINT GLOBAL (WAJIB)

- **TA.tex TIDAK BOLEH DIUBAH**
- Persona: "Penelitian ini..." (Aturan C1)
- Istilah asing: sesuai starter list Aturan C2 (konfirmasi ke user kalau ambiguous)
- Sitasi: `\parencite{}` atau `\textcite{}` — format Chicago (Aturan A9, C9)
- First mention akronim: kepanjangan italic + (singkatan) (Aturan C3)

---

## Konteks Phase 2

Bab I saat ini sudah punya 5 section:
1. Latar Belakang
2. Rumusan Masalah
3. Tujuan
4. Batasan Masalah
5. Metodologi

Setelah Phase 1, T3 dan RM3 sudah diperbaiki ke YAML Validation. Phase 2 bertugas:
1. Tambah section ke-6 **"Sistematika Penulisan"** — WAJIB pedoman ITB, saat ini hilang
2. Reframing **Latar Belakang** agar 3 Klaim utama (Klaim 1/2/3) muncul eksplisit sebagai kontribusi terukur
3. Verifikasi konsistensi bahasa & sitasi di seluruh Bab I

---

## File yang Dimodifikasi

| File | Perubahan |
|------|-----------|
| `Bab I - Pendahuluan.tex` | Tambah section Sistematika Penulisan + reframing Latar Belakang |

**TIDAK DIUBAH:** TA.tex, tabel, gambar, bab lain.

---

## Detail Perubahan

### 1. Section Sistematika Penulisan (WAJIB DITAMBAH)

Tambah section baru **setelah Metodologi** (section ke-6). Formatnya:

```latex
% --- Sistematika Penulisan ---
\section{Sistematika Penulisan}

Dokumen Tugas Akhir ini disusun dalam tujuh bab dengan sistematika sebagai berikut.

\begin{enumerate}
    \item \textbf{Bab I Pendahuluan} \\
    Bab ini memaparkan latar belakang permasalahan, rumusan masalah, tujuan penelitian,
    batasan masalah, metodologi pengerjaan, dan sistematika penulisan.

    \item \textbf{Bab II Studi Literatur} \\
    Bab ini menguraikan dasar teori yang mendasari penelitian, meliputi arsitektur
    Kubernetes dan kompleksitasnya, \textit{Large Language Models} (LLM), pendekatan
    \textit{Retrieval-Augmented Generation} (RAG), \textit{knowledge graph}, serta
    kajian penelitian terkait.

    \item \textbf{Bab III Analisis Masalah} \\
    Bab ini menyajikan analisis mendalam terhadap permasalahan yang dihadapi, eksplorasi
    data spesifikasi OpenAPI Kubernetes, analisis kebutuhan sistem, dan justifikasi
    pemilihan pendekatan GraphRAG sebagai solusi.

    \item \textbf{Bab IV Perancangan} \\
    Bab ini merinci rancangan arsitektur dan komponen sistem GraphRAG, mencakup tiga
    kontribusi teknis utama: \textit{pipeline} ekstraksi \textit{knowledge graph} (T1),
    mekanisme GraphRAG dengan \textit{intent-adaptive depth traversal} (T2), dan
    perancangan validasi YAML tiga lapis berbasis \textit{knowledge graph} (T3).

    \item \textbf{Bab V Implementasi} \\
    Bab ini menguraikan detail implementasi teknis setiap komponen sistem, termasuk
    lingkungan implementasi, kode program, dan keputusan teknis yang diambil selama
    pengembangan.

    \item \textbf{Bab VI Evaluasi} \\
    Bab ini menyajikan metodologi evaluasi, hasil evaluasi kuantitatif terhadap 97
    \textit{fixture} uji, perbandingan dengan \textit{baseline}, \textit{ablation study},
    analisis sensitivitas kedalaman, uji signifikansi statistik, dan analisis kondisi batas.

    \item \textbf{Bab VII Penutup} \\
    Bab ini menyimpulkan hasil penelitian berdasarkan tiga kontribusi teknis yang telah
    diverifikasi secara empiris dan memaparkan saran pengembangan lanjutan.
\end{enumerate}
```

### 2. Reframing Latar Belakang

Paragraf terakhir Latar Belakang saat ini (baris ~19–21) sudah menyebutkan 3 kontribusi, tetapi perlu diperkuat agar:
- Muncul **Klaim 1** (schema-derived deterministic KG) secara eksplisit dengan justifikasi mengapa LLM-extracted KG inferior
- Muncul **Klaim 2** (intent-adaptive depth) dengan motivasi konkret
- Muncul **Klaim 3** (KG-grounded YAML validation) sebagai alternatif *dry-run*
- Sitasi pendukung untuk masing-masing klaim:
  - Klaim 1: `\parencite{pan2024unifying}`, `\parencite{wan2025empowering}`
  - Klaim 2: `\parencite{wan2025empowering}` (GraphRAG paper yang tidak adaptive)
  - Klaim 3: `\parencite{kubernetes_docs}` untuk OpenAPI spec

**Target reframing:**
Ganti paragraf pengantar 3 klaim (saat ini 1 paragraf besar di baris ~21) menjadi 2 paragraf:
- Paragraf 1: Konteks GraphRAG sebagai solusi, kemudian masalah yang belum diselesaikan (stochastic KG, fixed depth, no KG-grounded validation)
- Paragraf 2: 3 Klaim dengan **bold label** (sesuai Aturan C7), masing-masing dengan sitasi

### 3. Audit Bahasa Bab I

Setelah menambah/merevisi, periksa seluruh Bab I untuk:
- [ ] Tidak ada "dimana"/"di mana" sebagai relative pronoun (Aturan A5)
- [ ] "sedangkan" didahului koma; "sehingga" tanpa koma (Aturan A1-A2)
- [ ] Desimal pakai koma bukan titik (Aturan A7)
- [ ] First mention akronim: kepanjangan + (singkatan) (Aturan C3)
  - RAG, LLM, KG, GraphRAG sudah muncul di Bab I — cek apakah sudah diberi kepanjangan
- [ ] Range angka: en-dash `--` bukan hyphen (Aturan C6)
- [ ] Persona "Penelitian ini..." bukan "Penulis..." atau "Saya..." (Aturan C1)
- [ ] Istilah asing: sesuai starter list C2 (italic untuk: *retrieval*, *knowledge graph*, *intent*, dll.)

---

## Cek Sitasi Wajib di Bab I

Verifikasi bahwa citekey berikut ada di `daftar-pustaka.bib`:

| Citekey | Untuk |
|---------|-------|
| `gartner_cloud_2021` | Proyeksi 95% cloud-native |
| `cncf_2023_survey` | CNCF 2023 survey |
| `rahman_k8s_security_2023` | 80% insiden dari YAML kompleksitas |
| `liu2024deepanalysis` | LLM kode sintaksis benar tapi semantis salah |
| `wan2025empowering` | Vector RAG 63,4% exact match |
| `pan2024unifying` | KG untuk RAG |
| `niaksu2015` | CRISP-DM |
| `k8s_docs_concepts` | Kubernetes docs (IaC) |
| `kubernetes_docs` | Kubernetes docs (orkestrasi) |

---

## Checklist Verifikasi Phase 2

- [ ] Section "Sistematika Penulisan" ada sebagai `\section{Sistematika Penulisan}` di Bab I
- [ ] Sistematika mencantumkan 7 bab dengan deskripsi singkat yang akurat
- [ ] Bab IV deskripsi Sistematika menyebutkan T1, T2, T3
- [ ] Latar Belakang: 3 Klaim muncul eksplisit dengan bold label (**Pertama**, **Kedua**, **Ketiga**)
- [ ] Latar Belakang: Klaim 1 punya sitasi pan2024/wan2025; Klaim 2 punya justifikasi adaptive; Klaim 3 punya alternatif dry-run
- [ ] Latar Belakang: keunggulan presisi *retrieval*/validitas YAML ditulis sebagai HIPOTESIS (dibandingkan baseline di Bab VI), BUKAN klaim hasil
- [ ] Pemetaan: Klaim 1→T1, Klaim 2 & 3→T2 (validasi YAML bagian sistem); perbandingan = T3
- [ ] Tidak ada "dimana" sebagai relative pronoun
- [ ] First mention RAG: "*Retrieval-Augmented Generation* (RAG)"
- [ ] First mention LLM: "*Large Language Models* (LLM)"
- [ ] First mention KG: "*knowledge graph* (KG)"
- [ ] Sitasi semua sudah valid (citekey ada di .bib)

---

## Catatan untuk Phase Selanjutnya

- **Phase 3** (Bab II-III): Cek apakah teori 3 Klaim sudah ada di Bab II; sinkron RM dengan T3 baru
- **Phase 7** (Bahasa): Audit menyeluruh Bab I termasuk anti-pattern C11
