# Phase 6 — Bab VII: Reframing Kesimpulan + Keterbatasan

**Status:** PENDING  
**Prasyarat:** Phase 1 (struktur T1/T2/T3), Phase 5 (angka v13 tersedia)  
**Referensi Aturan Bahasa:** [Plan Utama](../../.claude/plans/act-seperti-dosen-penguji-zippy-kahn.md) — bagian "Aturan Bahasa"

---

## ⚠ REVISI (Mei 2026) — struktur 3 paragraf kesimpulan berubah

Bab VII mengikuti pemetaan tujuan baru:
- **Paragraf 1 (T1):** "Kontribusi pertama — KG deterministik dibangun." Tidak berubah substansinya.
- **Paragraf 2 (T2):** "Kontribusi kedua — sistem GraphRAG (retrieval *intent-adaptive* + validasi YAML tiga lapis) dikembangkan." Validasi YAML disebut sebagai **bagian sistem**, bukan tujuan tersendiri.
- **Paragraf 3 (T3):** "Hasil perbandingan — faktor-faktor tempat GraphRAG terbukti unggul/setara/lemah terhadap Vector RAG dan Vanilla LLM." **Faktor pemenang = TBD (dari re-run final); jangan dipra-tulis.** Di sinilah hipotesis presisi *retrieval* + validitas YAML dijawab empiris.

**Semua angka di bawah (0,6943/0,6989 dst.) = USANG.** Isi angka dari re-run final (TBD). Tidak ada "skor Total" berbobot.

---

## ⚠ CONSTRAINT GLOBAL (WAJIB)

- **TA.tex TIDAK BOLEH DIUBAH**
- Persona: "Penelitian ini..." (Aturan C1)
- Bold hanya untuk label Pertama/Kedua/Ketiga (Aturan C7)
- Hedging tepat: tidak ada "membuktikan secara mutlak" (Aturan C5)
- Desimal: koma — `0,6989` bukan `0.6989` (Aturan A7)

---

## Konteks Phase 6

Bab VII saat ini memiliki:
- `\section{Kesimpulan}` — 3 paragraf (Pertama/Kedua/Ketiga)
- `\section{Saran}` — 4 item saran

**Yang perlu dilakukan:**
1. Update angka v12 → v13 di seluruh Bab VII
2. Reframe Ketiga agar lebih eksplisit membahas T3 (YAML Validation) sebagai kontribusi, bukan hanya GraphRAG performance
3. Tambah `\section{Keterbatasan}` antara Kesimpulan dan Saran
4. Pastikan 3 paragraf secara satu-ke-satu maping ke T1, T2, T3

---

## File yang Dimodifikasi

| File | Perubahan |
|------|-----------|
| `Bab VII - Penutup.tex` | Update angka; reframe Ketiga; tambah Keterbatasan |

---

## Update Angka v12 → v13

Angka yang muncul di Bab VII saat ini (v12) dan gantinya (v13):

| Posisi di Bab VII | v12 | v13 |
|------------------|-----|-----|
| Skor komposit GraphRAG | **0,6943** | **0,6989** |
| RetQ gain vs Vector RAG | "+0,26" | "+0,26" (boleh tetap, hitungannya 0,6801−0,4249=0,2552 ≈ +0,26) |
| 95% CI RetQ | [+0,19, +0,33] | [+0,19, +0,33] (tidak berubah) |
| syntactic validity YAML | **0,9474** | **0,9474** (tidak berubah) |
| Spearman ρ derajat | +0,44 | +0,44 (tidak berubah) |

> **Catatan v13:** Perubahan terbesar adalah AnsQ naik (+0,0162), sehingga Total naik ke 0,6989. RetQ sedikit turun (−0,0050, dalam batas noise). Kesimpulan RetQ tetap valid.

---

## Reframing Tiga Paragraf Kesimpulan

### Paragraf 1 — Klaim 1: KG Construction (T1)

**Status saat ini:** Sudah baik. Menyebut deterministik, 725 node, 18 edge types, 7 kategori, ablation A1-A2.

**Yang perlu ditambah/perbaiki:**
- Tidak ada perubahan substansial; hanya pastikan angka sudah v13 (tidak ada angka yang berubah untuk T1)
- Pastikan kalimat pembuka eksplisit menyebut "Kontribusi pertama" atau "Tujuan pertama penelitian ini"

### Paragraf 2 — Klaim 2: Intent-Adaptive Depth (T2)

**Status saat ini:** Sudah baik. Menyebut intent-adaptive depth, followup 0,943 → 0,769, A3 ablation.

**Yang perlu ditambah/perbaiki:**
- Tidak ada perubahan substansial
- Pastikan kalimat pembuka eksplisit menyebut "Kontribusi kedua" atau "Tujuan kedua penelitian ini"

### Paragraf 3 — T3: Hasil Perbandingan (REVISI)

**Arah baru:** T3 = perbandingan 3 sistem, bukan YAML Validation tersendiri. Validasi YAML masuk ke Paragraf 2 (T2).

**Draft struktur Paragraf 3:**
1. **Pembuka:** "Melalui perbandingan terhadap Vector RAG dan Vanilla LLM, penelitian ini mengidentifikasi faktor-faktor keunggulan sistem GraphRAG."
2. **Isi:** laporan per-faktor (RetQ, Path Coverage, Hop Accuracy, *syntactic validity*) dari hasil re-run. Sebutkan faktor mana unggul/setara/lemah **berdasarkan data empiris**, bukan asumsi.
3. **Kondisi batas:** di intent/derajat mana keunggulan terbesar (dari boundary condition analysis Bab VI).

⚠ **Angka & faktor pemenang = TBD** — isi setelah re-run final. JANGAN menulis angka dari v12/v13/v17 lama. Tidak ada "Total 0,6989" atau "RetQ +0,26" sampai ada data baru.

**Draft reframe Ketiga:**

```
\textbf{Ketiga}, mekanisme validasi struktural YAML tiga lapis berbasis 
\textit{knowledge graph} berhasil diimplementasikan. Lapisan ketiga—pemeriksaan 
\textit{required fields} langsung dari \textit{knowledge graph}—mencapai validitas 
sintaksis \textbf{0,9474} pada 97 \textit{fixture} uji, memverifikasi keberadaan 
ruas wajib tanpa memerlukan \textit{dry-run} pada kluster Kubernetes aktif. 
Implementasi ini merupakan alternatif yang dapat diverifikasi secara otomatis 
dibandingkan validasi berbasis kluster yang memerlukan infrastruktur nyata.

Secara keseluruhan, sistem GraphRAG yang mengintegrasikan ketiga kontribusi di atas 
mencapai total skor komposit \textbf{0,6989} (AnsQ 0,5904, RetQ 0,6801, ReaQ 0,8989), 
mengungguli \textit{Vector RAG} (0,6111) dan \textit{Vanilla LLM} (0,4015). 
Keunggulan pada dimensi \textit{Retrieval Quality} (RetQ $+0{,}26$, $p < 0{,}001$, 
95\% CI $[+0{,}19, +0{,}33]$) bersifat konsisten dan signifikan secara statistik. 
Analisis kondisi batas menunjukkan bahwa GraphRAG memberikan keunggulan terbesar 
pada tipe \textit{intent} relasional (\textit{follow-up} $+0{,}59$, \textit{planning} $+0{,}59$) 
dan pada \textit{resource} dengan derajat konektivitas menengah--tinggi 
(derajat 3--7, Spearman $\rho = +0{,}44$, $p < 0{,}001$).
```

---

## Tambah Section: Keterbatasan

Tambah section baru `\section{Keterbatasan}` **antara** Kesimpulan dan Saran. Isi mencakup:

### 1. Directed Graph dan Keterbatasan Relasi Operasional

Graf yang dibangun merupakan *directed graph* yang hanya merepresentasikan relasi struktural-skema dari referensi tipe dalam `swagger.json`. Akibatnya, relasi operasional seperti RBAC (*ServiceAccount* → *ClusterRole*) tidak dapat dijangkau melalui *traversal* dari *ServiceAccount*, karena edge hanya ada dalam arah terbalik (*RoleBinding* → *ServiceAccount*).

### 2. Keterbatasan Kategori *Realworld*

Kategori *realworld* memperoleh skor terendah (0,50) karena pertanyaan operasional nyata sering membutuhkan konteks *runtime* yang tidak tersedia dalam skema statis. Graf berbasis spesifikasi OpenAPI tidak mencakup status kluster aktual, log, atau perilaku *runtime*.

### 3. Eksperimen CGG (*Citation-Grounded Generation*)

Eksperimen CGG — yang membatasi istilah K8s dalam jawaban hanya pada `graph_context` yang diambil — menghasilkan penurunan *grounding score* sebesar 0,135 poin dan total skor turun 0,006 poin. Analisis menunjukkan bahwa CGG terlalu ketat: model secara valid mereferensikan konsep K8s yang terhubung secara semantik meskipun tidak secara eksplisit diambil dalam `graph_context`. Ini merupakan perilaku yang diharapkan dari integrasi pengetahuan *prior* LLM dengan *retrieved context*.

```latex
\section{Keterbatasan}

Penelitian ini mengidentifikasi tiga keterbatasan utama yang memengaruhi 
cakupan dan generalisabilitas hasil.

\textbf{Pertama}, \textit{knowledge graph} yang dibangun merupakan 
\textit{directed graph} yang hanya merepresentasikan relasi 
struktural-skema dari referensi tipe dalam \texttt{swagger.json}. 
Relasi operasional seperti ikatan RBAC antara \textit{ServiceAccount} 
dan \textit{ClusterRole} tidak dapat dijangkau melalui \textit{traversal} 
yang dimulai dari \textit{ServiceAccount}, karena \textit{edge} tersebut 
hanya ada dalam arah terbalik (\textit{RoleBinding} $\to$ \textit{ServiceAccount}).
Pengembangan lanjutan dapat menambahkan sumber relasi operasional sebagai 
lapisan kedua di atas graf skema yang sudah ada.

\textbf{Kedua}, kategori \textit{realworld} memperoleh skor terendah 
(0,50) karena pertanyaan operasional nyata sering membutuhkan konteks 
\textit{runtime} yang tidak tersedia dalam spesifikasi skema statis. 
Graf berbasis OpenAPI tidak mencakup status kluster aktual, log 
operasional, atau perilaku \textit{runtime} dinamis.

\textbf{Ketiga}, eksperimen \textit{Citation-Grounded Generation} (CGG)—
yang memeriksa apakah istilah Kubernetes dalam jawaban berasal dari 
\textit{graph\_context} yang diambil—menghasilkan penurunan 
\textit{grounding score} sebesar 0,135 poin. Analisis menunjukkan bahwa 
model secara valid mereferensikan konsep Kubernetes yang terhubung secara 
semantik meskipun tidak secara eksplisit tersedia dalam 
\textit{graph\_context}, merupakan perilaku yang diharapkan dari integrasi 
pengetahuan \textit{prior} LLM dengan \textit{retrieved context}.
```

---

## Audit Saran (4 Item)

Saran yang sudah ada perlu dicek konsistensinya dengan hasil akhir:

| Saran | Status | Catatan |
|-------|--------|---------|
| 1. Perluasan KG dengan relasi operasional | OK | Konsisten dengan Keterbatasan #1 |
| 2. Integrasi data dinamis (K8s Watch API) | OK | Konsisten dengan Keterbatasan #2 |
| 3. CGG selektif | OK | Konsisten dengan Keterbatasan #3 |
| 4. Pembaruan inkremental KG | OK | Tidak ada masalah |

Pastikan saran 1-4 tidak mengulang konten Keterbatasan secara verbatim — Keterbatasan menjelaskan *masalahnya*, Saran menjelaskan *arah penyelesaiannya*.

---

## Checklist Verifikasi Phase 6

- [ ] Paragraf Pertama: eksplisit sebut "Kontribusi pertama" / T1 (KG deterministik)
- [ ] Paragraf Kedua: eksplisit sebut "Kontribusi kedua" / T2 (sistem GraphRAG + validasi YAML)
- [ ] Paragraf Ketiga: "Melalui perbandingan..." / T3 — faktor keunggulan dari re-run; TIDAK ada pra-klaim
- [ ] Angka dari re-run final (TBD); TIDAK ada "Total 0,6989" atau angka v12/v13 lama
- [ ] Section `\section{Keterbatasan}` ditambah antara Kesimpulan dan Saran
- [ ] Keterbatasan membahas: directed graph, realworld, CGG
- [ ] Saran tidak menduplikasi Keterbatasan secara verbatim
- [ ] Bold hanya untuk Pertama/Kedua/Ketiga (Aturan C7)
- [ ] Semua desimal pakai koma
- [ ] Cross-reference ke Bab VI tetap valid

---

## Catatan untuk Phase Selanjutnya

- **Phase 8** (Abstrak): Update angka di Abstrak juga — masih menggunakan Groq LLaMA dan angka lama
- **Phase 9** (Final review): Cek apakah 3 Kesimpulan ↔ 3 Tujuan ↔ 3 Section Bab IV/V sudah sinkron penuh
