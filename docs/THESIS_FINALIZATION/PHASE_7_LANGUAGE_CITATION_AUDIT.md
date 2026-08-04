# Phase 7 — Audit Bahasa & Sitasi Cross-Cutting

**Status:** PENDING  
**Prasyarat:** Phase 1–6 selesai (semua konten sudah final)  
**Referensi Aturan Bahasa:** [Plan Utama](../../.claude/plans/act-seperti-dosen-penguji-zippy-kahn.md) — bagian "Aturan Bahasa"

---

## ⚠ REVISI (Mei 2026) — tambahan cakupan audit

Audit bahasa standar tetap berlaku. Tambahan khusus setelah revisi metrik & tujuan:

**Tambahan grep/audit yang wajib dilakukan:**

1. **Tidak ada `eq:total_score`** — grep `eq:total_score` di seluruh `.tex`; hapus semua `\ref{eq:total_score}` dan `\eqref{eq:total_score}`.
2. **Istilah metrik baru harus italic:** `\textit{Path Coverage}`, `\textit{Hop Accuracy}`, `\textit{Grounding Score}` (di seluruh bab termasuk Bab II/VI/VII). RGA = akronim, tidak italic.
3. **Cross-ref persamaan metrik domain (kini di Bab II):** `eq:hop-accuracy`, `eq:path-coverage`, `eq:grounding`, `eq:faithfulness`, `eq:precision-recall`, `eq:ndcg` — pastikan `\label{}` ada di Bab II dan `\ref{}` dari bab lain valid.
4. **Tidak ada "Kontribusi ketiga = validasi YAML"** — grep dan ganti jadi "bagian sistem (T2)".
5. **Tidak ada pra-klaim keunggulan** di Bab I–V — grep "lebih baik dari", "mengungguli", "superior" di luar Bab VI/VII (hapus atau ubah jadi hipotesis/sasaran).
6. **Tidak ada bobot/skor Total** di bab manapun — grep `0{,}40`, `0{,}35`, `RETQ\_WEIGHT`, `ANSQ\_WEIGHT`, `total\_score` (di luar komentar LaTeX/kode).
7. **"Membandingkan" sebagai T3** harus konsisten: cek Bab I (Tujuan/RM), Bab VI (pembuka), Bab VII (Paragraf 3).

---

## ⚠ CONSTRAINT GLOBAL (WAJIB)

- **TA.tex TIDAK BOLEH DIUBAH**
- Semua perbaikan mengikuti 16 Hard Rules Aturan A dan terminologi Aturan B
- Perbaikan style mengikuti Aturan C (C1–C11)

---

## Konteks Phase 7

Phase ini adalah audit bahasa menyeluruh — menyisir semua file `.tex` bab inti dengan grep otomatis (pola pelanggaran) dan manual review (anti-pattern). Ini adalah phase paling tedious tapi krusial sebelum review final.

---

## File yang Diaudit

```
Bab I - Pendahuluan.tex
Bab II - Studi.tex
Bab III - Analisis.tex
Bab IV - Perancangan.tex
Bab V - Implementasi.tex
Bab VI - Evaluasi.tex
Bab VII - Penutup.tex
```

---

## A. Audit Grep — Hard Rules (Aturan A)

Untuk setiap pelanggaran di bawah, grep ke seluruh file bab, lalu perbaiki setiap kemunculan.

### A1–A2: "sehingga"/"sedangkan" di Posisi Salah

```
Pola grep: \. Sehingga|\. Sedangkan|^Sehingga|^Sedangkan
```

| Salah | Benar |
|-------|-------|
| ". Sehingga Y." | Ganti "Sehingga" → "karena", "sehingga", atau reframe kalimat |
| "X sedangkan Y" (tanpa koma sebelum sedangkan) | "X, sedangkan Y" |
| "X, sehingga Y" (dengan koma sebelum sehingga) | "X sehingga Y" (hapus koma) |

### A3: "di" Kata Depan vs Awalan Serangkai

```
Pola grep: \bdi [a-z]  (cek apakah itu kata depan atau awalan verba)
```

| Salah | Benar |
|-------|-------|
| "di analisis", "di gunakan", "di implementasikan" | "dianalisis", "digunakan", "diimplementasikan" |
| "diatas", "dibawah", "disamping" (kata depan) | "di atas", "di bawah", "di samping" |

### A4: Istilah Tidak Baku

```
Pola grep (case-insensitive): \banalisa\b|\baktifitas\b|\bsosial media\b|\bbisnis proses\b|\bexisting\b
```

| Salah | Benar |
|-------|-------|
| analisa | analisis |
| aktifitas | aktivitas |
| existing | "yang ada", "saat ini", atau *existing* (italic jika dipertahankan Inggris) |

### A5: "di mana"/"dimana" sebagai Relative Pronoun

```
Pola grep: \bdimana\b|\bdi mana\b
```

| Salah | Benar |
|-------|-------|
| "ruangan di mana rapat diadakan" | "ruangan tempat rapat diadakan" |
| "sistem di mana data disimpan" | "sistem yang menyimpan data" |

### A6: Placement "masing-masing"

```
Pola grep: \bmasing-masing [a-zA-Z]
```

| Salah | Benar |
|-------|-------|
| "masing-masing algoritma" | "tiap-tiap algoritma" atau "algoritma masing-masing" |
| "masing-masing komponen" | "setiap komponen" atau "komponen masing-masing" |

### A7: Desimal Pakai Titik (Inggris)

```
Pola grep: [0-9]+\.[0-9]  (dalam konteks teks, bukan kode atau URL)
```

Khusus perhatikan: `0.6989`, `0.69`, `0.42`, `0.001`, `95%` tanpa desimal tidak masalah.

| Salah | Benar |
|-------|-------|
| "skor 0.69" | "skor 0,69" |
| "$p < 0.001$" | "$p < 0{,}001$" (dalam math mode: `0{,}001`) |

### A8: Kalimat Tanpa Subjek (Setelah Keterangan Depan)

```
Pola grep: Dalam penelitian ini [a-z]  (tanpa "penelitian ini" sebagai subjek berikutnya)
Contoh buruk: "Dalam penelitian ini menggunakan..."
```

| Salah | Benar |
|-------|-------|
| "Dalam penelitian ini menggunakan..." | "Penelitian ini menggunakan..." atau "Dalam penelitian ini, penelitian ini menggunakan..." |

### A13: Kalimat Mulai dengan Angka

```
Pola grep: ^[0-9]|\. [0-9]  (di awal kalimat)
```

| Salah | Benar |
|-------|-------|
| "97 fixture digunakan dalam..." | "Sebanyak 97 *fixture* digunakan dalam..." |
| "725 node terdapat dalam..." | "Graf memiliki 725 node..." |

---

## B. Audit Terminologi (Aturan B)

### B1: Edge Types

```
Pola grep: HAS_PROPERTY|EXTENDS|REFERENCES|CONTAINS|LOADS  (tanpa \textit{})
```
Semua edge type harus `\textit{HAS\_PROPERTY}`, `\textit{EXTENDS}`, dst.

### B2: Node Pipeline

```
Pola grep: \bThinker\b|\bSpeaker\b|\bRetriever\b|\bSaver\b|\bMemory\b  (kapital, tanpa italic)
```
Harus `\textit{thinker}`, `\textit{speaker}`, `\textit{retriever}`, `\textit{saver}`, `\textit{memory}`.

**Exception:** Di awal kalimat atau judul tabel, boleh kapital tapi tetap italic.

### B3: Intent Types

```
Pola grep: generate_yaml|trace_relationship|planning|explain|followup  (tanpa \textit{})
```
Harus `\textit{generate\_yaml}`, `\textit{trace\_relationship}`, dst.

### B4: Resource K8s

```
Pola grep: \bPod\b|\bDeployment\b|\bStatefulSet\b|\bConfigMap\b  (tanpa \textit{})
```
Harus `\textit{Pod}`, `\textit{Deployment}`, `\textit{StatefulSet}`, `\textit{ConfigMap}`, dst.

**Exception:** Nama file YAML atau kode (`\texttt{}`), judul tabel, nama class.

### B5: Metrik Dimensi

```
Pola grep: \bAnsQ\b|\bRetQ\b|\bReaQ\b  (tanpa italic — ini benar, tapi cek konsistensi)
```
AnsQ, RetQ, ReaQ tidak pakai italic (kapital biasa).

### B6: Versi Kubernetes

```
Pola grep: versi 1\.30|Kubernetes 1\.30  (tanpa "v" prefix)
```
Harus "v1.30" (dengan huruf "v").

---

## C. Audit Style Decisions (Manual Review per Bab)

### C1: Persona "Penelitian ini..."

Baca setiap paragraf Bab I–VII. Tandai dan ganti:
- "Penulis mengusulkan..." → "Penelitian ini mengusulkan..."
- "Kami menggunakan..." → "Penelitian ini menggunakan..."
- "Saya menemukan..." → "Penelitian ini menemukan..."

**Exception:** Kata Pengantar dan Pernyataan Orisinalitas → tetap "Saya"

### C2: Istilah Asing Tanpa `\textit{}`

Grep dan perbaiki istilah yang seharusnya italic tapi tidak:
```
Pola: \bretrival\b|\bembedding\b|\bpipeline\b|\btraversal\b|\bhallucination\b|\breasoning\b
(tanpa backslash textit sebelumnya)
```

Starter list dari Aturan C2 — pastikan semua sudah italic:
- *retrieval*, *embedding*, *pipeline*, *traversal*, *reasoning*, *reasoning path*
- *knowledge graph*, *node*, *edge*, *intent*, *multi-hop*, *fallback*
- *ablation study*, *ground truth*, *baseline*, *runtime*, *production-grade*
- *trace*, *path*

### C6: Range Angka — Hyphen vs En-dash

```
Pola grep: [0-9]-[0-9]  (dalam konteks range, bukan minus)
```

| Salah | Benar |
|-------|-------|
| "kedalaman 1-5" | "kedalaman 1--5" (LaTeX en-dash) |
| "derajat 3-7" | "derajat 3--7" |

**Exception:** Angka negatif (`$-0{,}50$`), kode, URL.

### C9: Sitasi Format

```
Pola: ([A-Z][a-z]+ \d{4}) [a-z]  (parentetik di posisi subjek)
```

| Salah | Benar |
|-------|-------|
| "(Wan 2025) mengusulkan..." | "Wan (2025) mengusulkan..." (`\textcite{wan2025}`) |
| "(Pan dkk. 2024) menunjukkan..." | "Pan dkk. (2024) menunjukkan..." |

---

## C11: Anti-Pattern Check (Manual per Bab)

Untuk setiap bab, baca dan tandai:

| Anti-pattern | Contoh | Perbaikan |
|--------------|--------|-----------|
| Kalimat pasif berantai > 3 | "Data dikumpulkan, dianalisis, divalidasi, disimpan." | Pecah kalimat atau satu aktif |
| Nominalisasi berlebihan | "pengimplementasian dilakukan" | "diimplementasikan" atau "implementasi dilakukan" |
| Frasa filler | "pada dasarnya", "secara umum", "perlu diingat bahwa", "perlu diketahui bahwa" | Hapus |
| Redundansi | "hasil daripada penelitian", "berdasarkan dari", "untuk dapat dilakukan" | "hasil penelitian", "berdasarkan", "agar dapat" |
| Pembuka paragraf monoton | 5 paragraf berturut mulai "Penelitian ini..." | Variasi: "Berdasarkan...", "Hasil menunjukkan...", "Selanjutnya..." |
| Bullet disguise | "Sistem menggunakan A dan B dan C dan D dan E." | `\begin{enumerate}` |
| Cross-reference dangling | `\ref{fig:xxx}` tanpa `\label{fig:xxx}` | Tambah label atau hapus ref |

---

## D. Audit Cross-Reference Dangles

Setelah semua perubahan Phase 1–6, lakukan grep untuk memastikan semua `\ref{}` punya pasangan `\label{}`:

```
Daftar label yang harus ada (cek \label{} di file-file bab):
- chap:pendahuluan, chap:studi-literatur, chap:analisis-masalah
- chap:perancangan, chap:implementasi, chap:evaluasi, chap:penutup
- sec:perancangan-kg, sec:perancangan-graphrag, sec:perancangan-yaml  (baru dari Phase 1)
- sec:expert_validation
- sec:ablation-study, subsec:depth-sensitivity, sec:statistical-test
- subsec:boundary-condition, subsubsec:bc-by-type, subsubsec:bc-quantitative
- fig:crispdm_diagram, fig:architecture_diagram, fig:sequence_diagram, fig:langgraph_pipeline
- fig:depth-sensitivity, fig:depth-submetrics
- fig:boundary-retq-gain-by-type, fig:boundary-hops-vs-gain, fig:boundary-degree-vs-gain
- tbl:dimension_scores, tbl:category_scores, tbl:ablation_results
- tbl:statistical_test, tbl:ablation_significance
- tbl:retq-gain-by-type, tbl:spearman-factors
- eq:total_score, eq:retq-gain
```

---

## E. Audit Bibliography

```bash
# Cek citekey yang dipakai di dokumen
grep -r "\\\\parencite{\|\\\\textcite{\|\\\\cite{" Bab*.tex | grep -oP '(?<=\{)[^}]+' | sort | uniq

# Bandingkan dengan entry di daftar-pustaka.bib
grep "^@" daftar-pustaka.bib | grep -oP '(?<=\{)[^,]+' | sort
```

Pastikan tidak ada:
- Citekey di teks yang tidak ada entry-nya di .bib
- Entry di .bib yang tidak dipakai di dokumen

---

## Checklist Verifikasi Phase 7

### Grep-Based Fixes
- [ ] Zero "dimana"/"di mana" sebagai relative pronoun
- [ ] Zero kalimat mulai dengan "Sehingga"/"Sedangkan" (standalone)
- [ ] Zero "di " + verba serangkai (di analisis, di gunakan)
- [ ] Zero istilah tidak baku (analisa, aktifitas)
- [ ] Zero angka desimal pakai titik dalam teks (0.69 → 0,69)
- [ ] Zero kalimat awal dengan angka
- [ ] Zero edge type tanpa `\textit{}`
- [ ] Zero intent type tanpa `\textit{}`
- [ ] Zero resource K8s tanpa `\textit{}`
- [ ] Zero range angka dengan hyphen tunggal

### Manual Review
- [ ] Persona "Penelitian ini..." konsisten (exception: Kata Pengantar, Pernyataan)
- [ ] Istilah asing dari starter list C2 sudah italic — termasuk *Path Coverage*, *Hop Accuracy*, *Grounding Score*
- [ ] Tidak ada paragraf yang dimulai dengan angka
- [ ] Tidak ada paragraf filler (pada dasarnya, secara umum)
- [ ] Tidak ada sitasi parentetik di posisi subjek
- [ ] Variasi pembuka paragraf (tidak 5 berturut-turut "Penelitian ini...")
- [ ] Cross-reference tidak dangling
- [ ] Zero `\ref{eq:total_score}` atau `\eqref{eq:total_score}` di seluruh dokumen
- [ ] Zero "Kontribusi ketiga = validasi YAML" di Bab I–V
- [ ] Zero pra-klaim keunggulan di luar Bab VI/VII
- [ ] Zero bobot/skor Total di luar Bab VI (dan di Bab VI pun sudah tidak ada)

### Bibliography
- [ ] Semua citekey yang dipakai ada di .bib
- [ ] Tidak ada entry .bib orphan yang tidak dipakai

---

## Catatan untuk Phase Selanjutnya

- **Phase 8** (Frontmatter): Terapkan audit bahasa yang sama ke Abstrak, Kata Pengantar, dan frontmatter lainnya
- **Phase 9** (Final): Compile dan cek output PDF untuk typo yang tidak tertangkap grep
