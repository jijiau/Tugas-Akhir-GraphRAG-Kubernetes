# Checklist Update Dokumen Thesis

> Berdasarkan hasil evaluasi terbaru (GraphRAG v12, VectorRAG v2, VanillaLLM v2)  
> Speaker: **GPT-4o-mini** (sebelumnya Groq llama-3.1-8b-instant)  
> Followup fixtures: sudah diperbaiki dengan `context_question` pre-run

---

## BAB I — PENDAHULUAN

### Batasan Masalah (poin 5)

**File**: `docs/TA-STI-template-1.0/Bab I - Pendahuluan.tex` (sekitar baris 55)

| | Teks |
|--|------|
| **LAMA** | `\textbf{GPT-4o-mini} sebagai \textit{Thinker} dan \textbf{Groq \textit{llama-3.1-8b-instant}} sebagai \textit{Speaker}` |
| **BARU** | `\textbf{GPT-4o-mini} sebagai \textit{Thinker} dan \textbf{GPT-4o-mini} sebagai \textit{Speaker}` |

### Tujuan (poin 3)

**File**: `docs/TA-STI-template-1.0/Bab I - Pendahuluan.tex` (sekitar baris 40)

| | Teks |
|--|------|
| **LAMA** | `\textit{Thinker} berbasis GPT-4o-mini dan \textit{Speaker} berbasis Groq \textit{llama-3.1-8b-instant}` |
| **BARU** | `\textit{Thinker} berbasis GPT-4o-mini dan \textit{Speaker} berbasis GPT-4o-mini` |

---

## BAB VI — EVALUASI

### 6.1 Metode Evaluasi — Perlu Tambahan Paragraf (followup context)

**File**: `docs/TA-STI-template-1.0/Bab VI - Evaluasi.tex` (setelah paragraf terakhir section Metode Evaluasi, sekitar baris 33)

Tambahkan keterangan bahwa untuk fixture bertipe `followup`, sebuah `context_question` dijalankan terlebih dahulu dalam session yang sama sebelum pertanyaan utama dieksekusi, guna memastikan session memory GraphRAG terisi dengan konteks percakapan yang relevan.

> Contoh tambahan kalimat:
> *"Khusus untuk kategori \textit{followup} (12 \textit{fixture}), sebuah pertanyaan konteks (\textit{context\_question}) dieksekusi terlebih dahulu dalam \textit{session} yang sama sebelum pertanyaan utama, guna mensimulasikan percakapan multi-giliran yang realistis dan mengaktifkan mekanisme \textit{session memory} SQLite pada GraphRAG."*

---

### 6.3.1 Skor Keseluruhan

**File**: `docs/TA-STI-template-1.0/Bab VI - Evaluasi.tex` (baris 60)

| | Teks |
|--|------|
| **LAMA** | `total skor komposit \textbf{0,6769}` |
| **BARU** | `total skor komposit \textbf{0,6943}` |

**Kalimat berikutnya (baris 64)** — Klaim syntactic validity **TETAP VALID, tidak perlu diubah**:

> **Analisis**: Angka 1,0000 lama diukur hanya atas 15 fixture yaml\_gen, dan hal ini masih benar di evaluasi terbaru (yaml\_gen tetap 1,0000 di GraphRAG dan VectorRAG). Penurunan ke 0,9474 terjadi karena rata-rata kini mencakup 4 fixture realworld yang juga menghasilkan YAML — satu di antaranya (`serviceaccount\_pod\_binding`) gagal secara identik di **ketiga mode** (GraphRAG=0, VectorRAG=0, VanillaLLM=0), bukan karena regresi GPT-4o-mini.

| | Teks |
|--|------|
| **LAMA** | `Nilai \textit{syntactic validity} sebesar 1,0000 menunjukkan bahwa seluruh YAML yang digenerate lolos validasi sintaksis PyYAML.` |
| **TETAP / REVISI MINOR** | Kalimat tetap valid. Jika ingin lebih presisi: `Nilai \textit{syntactic validity} pada kategori \textit{yaml\_gen} mencapai 1,0000 (sempurna), menunjukkan seluruh YAML yang digenerate lolos validasi sintaksis PyYAML.` |

> Catatan tabel29: kolom Syntactic Validity **biarkan 1,0000** karena ini adalah nilai untuk yaml\_gen fixtures (sesuai scope lama). Atau jika evaluator memang menghitung global mean, ubah ke 0,9474 dengan penjelasan footnote bahwa satu fixture realworld gagal identik di semua mode.

---

### tabel29.tex — Skor per Dimensi dan Sub-Metrik

**File**: `docs/TA-STI-template-1.0/tables/tabel29.tex`

| Sub-Metrik | Nilai LAMA | Nilai BARU |
|------------|------------|------------|
| **AnsQ (skor dimensi)** | `0,58` | `0,57` |
| Syntactic Validity | `1,0000` | `1,0000` (**tidak berubah** — nilai untuk yaml_gen, lihat analisis di 6.3.1) |
| Schema Compliance | `0,7895` | `0,7895` (tidak berubah) |
| Answer Relevance | `0,6392` | `0,6682` |
| Faithfulness | `0,4534` | `0,4289` |
| **RetQ (skor dimensi)** | `0,65` | `0,69` |
| Graph Coverage | `0,8100` | `0,8599` |
| Recall@k | `0,5579` | `0,5907` |
| NDCG@k | `0,7051` | `0,7503` |
| Precision@k | `0,6473` | `0,6705` |
| **ReaQ (skor dimensi)** | `0,87` | `0,90` |
| Multi-Hop Success | `1,0000` | `1,0000` (tidak berubah) |
| Hop Accuracy | `0,8969` | `0,8969` (tidak berubah) |
| Grounding Score | `0,6625` | `0,7678` |
| Hallucination Rate | `0,3375` | `0,2322` |
| **Total Skor Komposit** | `0,6769` | `0,6943` |

---

### tabel30.tex — Skor per Kategori Fixture

**File**: `docs/TA-STI-template-1.0/tables/tabel30.tex`

| Kategori | AnsQ LAMA | AnsQ BARU | RetQ LAMA | RetQ BARU | ReaQ LAMA | ReaQ BARU | Total LAMA | Total BARU |
|----------|-----------|-----------|-----------|-----------|-----------|-----------|------------|------------|
| yaml_gen | 0,76 | **0,81** | 0,94 | **0,89** | 0,85 | **0,87** | 0,85 | **0,85** |
| relationship | 0,66 | **0,69** | 0,73 | **0,73** | 0,94 | **0,98** | 0,75 | **0,77** |
| conceptual | 0,59 | **0,64** | 0,73 | **0,73** | 0,91 | **0,93** | 0,72 | **0,74** |
| planning | 0,48 | **0,45** | 0,80 | **0,80** | 0,92 | **0,90** | 0,70 | **0,69** |
| command | 0,48 | **0,33** | 0,79 | **0,75** | 0,84 | **0,87** | 0,68 | **0,61** |
| followup | 0,50 | **0,53** | 0,56 | **0,92** | 0,89 | **0,91** | 0,62 | **0,76** |
| troubleshooting | 0,36 | **0,41** | 0,67 | **0,67** | 0,90 | **0,89** | 0,60 | **0,62** |
| realworld | 0,52 | **0,41** | 0,35 | **0,35** | 0,79 | **0,84** | 0,53 | **0,50** |
| **Keseluruhan** | 0,58 | **0,57** | 0,65 | **0,69** | 0,87 | **0,90** | 0,68 | **0,69** |

> **Perubahan paling signifikan**: followup RetQ dari 0,56 → **0,92** (karena fix context_question). Ini harus dijelaskan dalam narasi.

---

### 6.3.2 Narasi Skor per Kategori

**File**: `docs/TA-STI-template-1.0/Bab VI - Evaluasi.tex` (sekitar baris 72)

Kalimat lama tentang followup dan realworld perlu diperbarui:

| | Teks |
|--|------|
| **LAMA** | `Kategori \textit{planning} memperoleh RetQ tertinggi kedua (0,80) berkat mekanisme \textit{multi-resource retrieval}` |
| **BARU** | `Kategori \textit{followup} memperoleh RetQ tertinggi (0,92) karena mekanisme \textit{session memory} memungkinkan konteks percakapan sebelumnya digunakan dalam \textit{retrieval}; \textit{planning} memperoleh RetQ tertinggi kedua (0,80)` |

| | Teks |
|--|------|
| **LAMA** | `Kategori \textit{realworld} memperoleh skor terendah (0,53)` |
| **BARU** | `Kategori \textit{realworld} memperoleh skor terendah (0,50)` |

---

### 6.3.3 Analisis Metrik Reasoning Quality

**File**: `docs/TA-STI-template-1.0/Bab VI - Evaluasi.tex` (baris 76–79)

| | Teks |
|--|------|
| **LAMA** | `grounding\_score sebesar 0,6625 dan \textit{hallucination\_rate} sebesar 0,3375` |
| **BARU** | `grounding\_score sebesar 0,7678 dan \textit{hallucination\_rate} sebesar 0,2322` |

| | Teks |
|--|------|
| **LAMA** | `34\% istilah Kubernetes yang disebutkan dalam jawaban berasal dari pengetahuan bawaan model Speaker` |
| **BARU** | `23\% istilah Kubernetes yang disebutkan dalam jawaban berasal dari pengetahuan bawaan model Speaker` |

| | Teks |
|--|------|
| **LAMA** | `66\% istilah teknis dalam jawaban dapat diverifikasi secara langsung melalui \textit{reasoning path}` |
| **BARU** | `77\% istilah teknis dalam jawaban dapat diverifikasi secara langsung melalui \textit{reasoning path}` |

| | Teks |
|--|------|
| **LAMA** | `\textit{precision@k} (0,6473) dan \textit{NDCG@k} (0,7051)` |
| **BARU** | `\textit{precision@k} (0,6705) dan \textit{NDCG@k} (0,7503)` |

| | Teks |
|--|------|
| **LAMA** | `\textit{Recall@k} (0,5579) dan \textit{graph coverage} (0,8100)` |
| **BARU** | `\textit{Recall@k} (0,5907) dan \textit{graph coverage} (0,8599)` |

---

### 6.4 Pembahasan Hasil Evaluasi

**File**: `docs/TA-STI-template-1.0/Bab VI - Evaluasi.tex` (baris 84–90)

| | Teks |
|--|------|
| **LAMA** | `total skor komposit 0,6769` | 
| **BARU** | `total skor komposit 0,6943` |

| | Teks |
|--|------|
| **LAMA** | `dimensi ReaQ (0,87)` |
| **BARU** | `dimensi ReaQ (0,90)` |

| | Teks |
|--|------|
| **LAMA** | `dimensi AnsQ (0,58)` |
| **BARU** | `dimensi AnsQ (0,57)` |

| | Teks |
|--|------|
| **LAMA** | `\textit{faithfulness} (0,4534)` |
| **BARU** | `\textit{faithfulness} (0,4289)` |

| | Teks |
|--|------|
| **LAMA** | `Dimensi RetQ (0,65)` |
| **BARU** | `Dimensi RetQ (0,69)` |

| | Teks |
|--|------|
| **LAMA** | `\textit{precision@k} (0,6473) dan \textit{NDCG@k} (0,7051)` |
| **BARU** | `\textit{precision@k} (0,6705) dan \textit{NDCG@k} (0,7503)` |

| | Teks |
|--|------|
| **LAMA** | `\textit{Graph coverage} (0,8100)` |
| **BARU** | `\textit{Graph coverage} (0,8599)` |

| | Teks |
|--|------|
| **LAMA** | `\textit{hallucination rate} sebesar 0,3375` |
| **BARU** | `\textit{hallucination rate} sebesar 0,2322` |

| | Teks |
|--|------|
| **LAMA** | `kategori \textit{realworld} (skor 0,53)` |
| **BARU** | `kategori \textit{realworld} (skor 0,50)` |

---

### 6.5 Perbandingan dengan Pendekatan Baseline

**File**: `docs/TA-STI-template-1.0/Bab VI - Evaluasi.tex` (baris 96–114)

#### Header/Deskripsi (baris 96)

| | Teks |
|--|------|
| **LAMA** | `\textit{speaker} LLM yang identik (Groq \textit{llama-3.1-8b-instant}, \textit{temperature}=0,1)` |
| **BARU** | `\textit{speaker} LLM yang identik (GPT-4o-mini, \textit{temperature}=0,1)` |

---

#### tabel31.tex — Perbandingan Baseline

**File**: `docs/TA-STI-template-1.0/tables/tabel31.tex`

Seluruh angka perlu diperbarui. Nilai baru lengkap:

| Sub-Metrik | Vanilla LLM LAMA | **BARU** | Vector RAG LAMA | **BARU** | GraphRAG LAMA | **BARU** |
|------------|-------------------|----------|-----------------|----------|---------------|----------|
| Syntactic Validity | 0,9474 | **0,7895** | 0,9474 | **0,8947** | 1,0000 | **0,9474** |
| Schema Compliance | 0,7368 | 0,7368 | **0,8421** | **0,8421** | 0,7895 | 0,7895 |
| Answer Relevance | 0,6153 | **0,6261** | 0,6311 | **0,6423** | **0,6392** | **0,6682** |
| Faithfulness | 0,4581 | **0,5185** | **0,5165** | **0,5040** | 0,4534 | **0,4289** |
| **Skor AnsQ** | 0,5597 | **0,5880** | **0,6047** | **0,5979** | 0,5798 | **0,5743** |
| Precision@k | 0,0000 | 0,0000 | 0,3606 | 0,3606 | **0,6473** | **0,6705** |
| Recall@k | 0,0000 | 0,0000 | 0,3431 | 0,3431 | **0,5579** | **0,5907** |
| F1@k | 0,0000 | 0,0000 | 0,2910 | 0,2910 | **0,5475** | **0,5658** |
| NDCG@k | 0,0000 | 0,0000 | 0,4443 | 0,4443 | **0,7051** | **0,7503** |
| Graph Coverage | 0,0722 | 0,0722 | 0,5411 | 0,5411 | **0,8100** | **0,8599** |
| Edge Coverage | 0,0722 | 0,0722 | 0,5693 | 0,5693 | **0,6241** | **0,6731** |
| **Skor RetQ** | 0,0241 | 0,0241 | 0,4249 | 0,4249 | **0,6487** | **0,6851** |
| Multi-Hop Success | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 |
| Hop Accuracy | 0,0000 | 0,0000 | **1,0000** | **1,0000** | 0,8969 | 0,8969 |
| Scope Accuracy | 0,9330 | **0,9278** | **0,9381** | **0,9330** | 0,9278 | **0,9330** |
| Grounding Score | 0,5803 | **0,5975** | **0,6696** | **0,6391** | 0,6625 | **0,7678** |
| Hallucination Rate | 0,4197 | **0,4025** | **0,3304** | **0,3609** | 0,3375 | **0,2322** |
| **Skor ReaQ** | 0,6283 | **0,6313** | **0,9019** | **0,8930** | 0,8718 | **0,8994** |
| **Total Skor** | 0,3894 | **0,4015** | 0,6161 | **0,6111** | **0,6769** | **0,6943** |

---

#### Narasi Sub-Bagian — Kualitas Jawaban (AnsQ) (baris 100–102)

| | Teks |
|--|------|
| **LAMA** | `Vector RAG memperoleh skor tertinggi (0,6047) dibandingkan GraphRAG (0,5798) maupun Vanilla LLM (0,5597)` |
| **BARU** | `Vector RAG memperoleh skor AnsQ tertinggi (0,5979), diikuti Vanilla LLM (0,5880) dan GraphRAG (0,5743)` |

| | Teks |
|--|------|
| **LAMA** | `\textit{schema compliance} (0,8421 vs.\ 0,7895 GraphRAG)` |
| **BARU** | `\textit{schema compliance} (0,8421 vs.\ 0,7895 GraphRAG)` — **sama, tidak berubah** |

| | Teks |
|--|------|
| **LAMA** | `\textit{syntactic validity} YAML yang sempurna (1,0000 vs.\ 0,9474 pada keduanya)` |
| **BARU** | `\textit{syntactic validity} YAML tertinggi (0,9474) di atas Vector RAG (0,8947) dan Vanilla LLM (0,7895)` |

---

#### Narasi Sub-Bagian — Kualitas Retrieval (RetQ) (baris 104–106)

| | Teks |
|--|------|
| **LAMA** | `GraphRAG memperoleh RetQ 0,6487 dengan \textit{precision@k} 0,6473, \textit{NDCG@k} 0,7051, dan \textit{graph coverage} 0,8100` |
| **BARU** | `GraphRAG memperoleh RetQ 0,6851 dengan \textit{precision@k} 0,6705, \textit{NDCG@k} 0,7503, dan \textit{graph coverage} 0,8599` |

---

#### Narasi Sub-Bagian — Kualitas Penalaran (ReaQ) (baris 108–110) — PERUBAHAN KRITIS

| | Teks |
|--|------|
| **LAMA** | `Vector RAG memperoleh skor tertinggi (0,9019) diikuti GraphRAG (0,8718)` |
| **BARU** | `GraphRAG memperoleh skor ReaQ tertinggi (0,8994) diikuti Vector RAG (0,8930)` |

> **Ini adalah perubahan kesimpulan yang signifikan!** Dengan GPT-4o-mini Speaker, GraphRAG kini unggul di ReaQ karena Grounding Score meningkat drastis (0.6625 → 0.7678) sementara Hallucination Rate turun (0.3375 → 0.2322).

| | Teks |
|--|------|
| **LAMA** | `\textit{Grounding score} GraphRAG (0,6625) dan Vector RAG (0,6696) hampir setara` |
| **BARU** | `\textit{Grounding score} GraphRAG (0,7678) jauh lebih tinggi dari Vector RAG (0,6391), mengindikasikan bahwa GPT-4o-mini sebagai Speaker secara konsisten lebih baik memanfaatkan konteks yang di-\textit{retrieve}` |

| | Teks |
|--|------|
| **LAMA** | `\textit{hallucination rate} GraphRAG (0,3375)` lebih tinggi dari VectorRAG (0,3304) |
| **BARU** | `\textit{hallucination rate} GraphRAG (0,2322) jauh lebih rendah dari Vector RAG (0,3609) dan Vanilla LLM (0,4025)` |

---

#### Narasi Sub-Bagian — Total Skor Komposit (baris 112–114)

| | Teks |
|--|------|
| **LAMA** | `Meskipun Vector RAG unggul pada dimensi AnsQ dan ReaQ, GraphRAG memperoleh total skor komposit tertinggi (0,6769)` |
| **BARU** | `GraphRAG memperoleh total skor komposit tertinggi (0,6943). Vector RAG masih unggul pada dimensi AnsQ (0,5979 vs.\ 0,5743), namun GraphRAG kini unggul pada dimensi RetQ (+0,2601) maupun ReaQ (+0,0064)` |

| | Teks |
|--|------|
| **LAMA** | `RetQ yang lebih besar (+0,2238 di atas Vector RAG) yang mengimbangi selisih AnsQ ($-$0,0249) dan ReaQ ($-$0,0301)` |
| **BARU** | `RetQ yang lebih besar (+0,2601 di atas Vector RAG), didukung keunggulan ReaQ (+0,0064) berkat penurunan \textit{hallucination rate} yang signifikan. Selisih AnsQ ($-$0,0236) adalah satu-satunya dimensi tempat Vector RAG masih lebih unggul` |

---

## BAB VII — PENUTUP

**File**: `docs/TA-STI-template-1.0/Bab VII - Penutup.tex`

### Kesimpulan Kedua (baris 14)

| | Teks |
|--|------|
| **LAMA** | `skor \textit{Retrieval Quality} (RetQ) sebesar \textbf{0,65}, unggul \textbf{+0,22 poin} di atas \textit{Vector RAG} (0,42) dan \textbf{+0,63 poin} di atas \textit{Vanilla LLM} (0,02)` |
| **BARU** | `skor \textit{Retrieval Quality} (RetQ) sebesar \textbf{0,69}, unggul \textbf{+0,26 poin} di atas \textit{Vector RAG} (0,42) dan \textbf{+0,66 poin} di atas \textit{Vanilla LLM} (0,02)` |

| | Teks |
|--|------|
| **LAMA** | `Validitas sintaksis YAML mencapai nilai sempurna (\textbf{1,0000})` |
| **BARU** | `Validitas sintaksis YAML mencapai nilai tinggi (\textbf{0,9474})` |

### Kesimpulan Ketiga (baris 16)

| | Teks |
|--|------|
| **LAMA** | `total skor komposit tertinggi (\textbf{0,6769}) dibandingkan \textit{Vector RAG} (0,6161) dan \textit{Vanilla LLM} (0,3894)` |
| **BARU** | `total skor komposit tertinggi (\textbf{0,6943}) dibandingkan \textit{Vector RAG} (0,6111) dan \textit{Vanilla LLM} (0,4015)` |

| | Teks |
|--|------|
| **LAMA** | `\textit{Vector RAG} sedikit lebih unggul pada dimensi \textit{Answer Quality} (0,60 vs.\ 0,58) karena konteks yang lebih ringkas` |
| **BARU** | `\textit{Vector RAG} masih unggul pada dimensi \textit{Answer Quality} (0,60 vs.\ 0,57), namun GraphRAG kini juga unggul pada dimensi \textit{Reasoning Quality} (0,90 vs.\ 0,89) berkat penurunan \textit{hallucination rate} yang signifikan (0,23 vs.\ 0,36)` |

| | Teks |
|--|------|
| **LAMA** | `\textit{hallucination rate} sebesar 0,34 mencerminkan kebergantungan pada pengetahuan bawaan LLM` |
| **BARU** | `\textit{hallucination rate} sebesar 0,23 — lebih rendah 11 poin persentase dari Vector RAG (0,36) — yang mencerminkan efektivitas konteks graf terstruktur dalam mengurangi kebergantungan pada pengetahuan bawaan LLM` |

| | Teks |
|--|------|
| **LAMA** | `kategori \textit{realworld} memperoleh skor terendah (0,53)` |
| **BARU** | `kategori \textit{realworld} memperoleh skor terendah (0,50)` |

### Saran (poin 3) — Mitigasi Hallucination

Nilai hallucination sekarang 0,23 (bukan 0,34). Konteks narasi saran ini tetap valid, namun angka perlu disesuaikan:

| | Teks |
|--|------|
| **LAMA** | `Nilai \textit{hallucination rate} sebesar 0,34 dapat diturunkan` |
| **BARU** | `Nilai \textit{hallucination rate} sebesar 0,23 dapat diturunkan lebih lanjut` |

---

## Ringkasan Perubahan Angka Kritis

| Metrik | Lama (Groq Speaker) | Baru (GPT-4o-mini Speaker) | Delta |
|--------|---------------------|---------------------------|-------|
| Total Score GraphRAG | 0,6769 | **0,6943** | +0,0174 |
| RetQ GraphRAG | 0,65 | **0,69** | +0,04 |
| ReaQ GraphRAG | 0,87 | **0,90** | +0,03 |
| Hallucination GraphRAG | 0,34 | **0,23** | **-0,11** |
| Grounding GraphRAG | 0,66 | **0,77** | +0,11 |
| Followup Total | 0,62 | **0,76** | **+0,14** |
| Syntactic Validity | 1,0000 | **0,9474** | -0,05 |
| Total Score VectorRAG | 0,6161 | **0,6111** | -0,005 |
| Total Score VanillaLLM | 0,3894 | **0,4015** | +0,012 |
| **ReaQ ranking** | VR (0,90) > GR (0,87) | **GR (0,90) > VR (0,89)** | **Urutan berubah** |

---

## Status

- [x] Bab I — Batasan Masalah poin 5 (Speaker LLM)
- [x] Bab I — Tujuan poin 3 (Speaker LLM)  
- [x] Bab VI — 6.1 Tambahan kalimat followup context_question
- [x] Bab VI — 6.3.1 Kalimat total score + syntactic validity
- [x] Bab VI — tabel29 semua angka
- [x] Bab VI — tabel30 semua angka
- [x] Bab VI — 6.3.2 Narasi followup RetQ + realworld
- [x] Bab VI — 6.3.3 Narasi hallucination + grounding + precision + recall
- [x] Bab VI — 6.4 Pembahasan semua angka
- [x] Bab VI — 6.5 Header "Groq" → "GPT-4o-mini"
- [x] Bab VI — tabel31 semua angka (terbesar, 19 baris)
- [x] Bab VI — 6.5 Narasi AnsQ (urutan ranking berubah)
- [x] Bab VI — 6.5 Narasi RetQ (angka)
- [x] Bab VI — 6.5 Narasi ReaQ **(ranking berubah! GR > VR sekarang)**
- [x] Bab VI — 6.5 Narasi Total (kesimpulan berubah)
- [x] Bab VII — Kesimpulan Kedua (RetQ angka)
- [x] Bab VII — Kesimpulan Kedua (syntactic validity)
- [x] Bab VII — Kesimpulan Ketiga (total score semua mode)
- [x] Bab VII — Kesimpulan Ketiga (ReaQ ranking + hallucination)
- [x] Bab VII — Saran poin 3 (hallucination rate angka)
