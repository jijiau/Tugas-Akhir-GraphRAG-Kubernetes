# Phase 4 — Bab IV & V: Konten Detail + Diagram

**Status:** PENDING  
**Prasyarat:** Phase 1 selesai (struktur T1/T2/T3 sudah ada di Bab IV/V)  
**Referensi Aturan Bahasa:** [Plan Utama](../../.claude/plans/act-seperti-dosen-penguji-zippy-kahn.md) — bagian "Aturan Bahasa"

---

## ⚠ REVISI (Mei 2026) — penyesuaian arah

- **Validasi YAML = bagian T2** (sistem GraphRAG), bukan "kontribusi ketiga"/T3. Di intro section 4.5 & 5.4, frame validasi YAML sebagai komponen sistem (lanjutan T2). Struktur fisik section 4.3/4.4/4.5 & 5.2/5.3/5.4 **TIDAK dibongkar**.
- **T3 (perbandingan) TIDAK punya section desain di Bab IV/V** — rumahnya Bab VI.
- **Deskripsi evaluator (Bab V):** ikuti metrik final — **tanpa Total berbobot** (buang konstanta `RETQ_WEIGHT/ANSQ_WEIGHT/REAQ_WEIGHT` & kolom `total_score`); RetQ = F1+NDCG+Path Coverage; ReaQ = Hop Accuracy+Grounding (*hallucination*/multihop/scope dibuang); ada `compute_rga`. Definisi metrik lengkap di Bab II (rujuk, jangan duplikasi).
- **Jangan pra-klaim keunggulan** di Bab IV/V (hipotesis; dijawab empiris di Bab VI).

---

## ⚠ CONSTRAINT GLOBAL (WAJIB)

- **TA.tex TIDAK BOLEH DIUBAH**
- Persona: "Penelitian ini..." (Aturan C1)
- Istilah asing: sesuai starter list Aturan C2
- Kode/algoritma > 10 baris: pindah ke `listings/` atau `algorithms/` (Aturan G)
- Gambar: `\caption{}` + `\label{fig:...}` wajib (Aturan D1)
- Tabel: `\caption{}` + `\label{tbl:...}` wajib (Aturan D2)

---

## Konteks Phase 4

Setelah Phase 1, Bab IV dan V sudah punya struktur 3 section (T1, T2, T3). Phase 4 bertugas mengisi konten substantif dan memastikan kualitas diagram. Ini adalah phase terberat karena mencakup:
1. Konten justifikasi design decision per T1/T2/T3
2. Fix konten yang sudah outdated (Groq → GPT-4o-mini, 12K char limit, dll.)
3. Diagram audit dan perbaikan

---

## File yang Dimodifikasi

| File | Perubahan |
|------|-----------|
| `Bab IV - Perancangan.tex` | Isi konten substantif per T1/T2/T3 |
| `Bab V - Implementasi.tex` | Isi konten + fix outdated references |
| `images/*.png` | Audit kualitas; replace yang blur/tidak profesional |
| `listings/*.tex` | Tambah listing kode jika diperlukan |
| `algorithms/*.tex` | Tambah pseudocode jika diperlukan |

---

## BAB IV — Perancangan (Setelah Phase 1 Restructure)

### Struktur Target Bab IV (Post-Phase 1)

```
4.1  Rancangan Solusi Secara Garis Besar
4.2  Pemetaan Metodologi terhadap Kebutuhan Sistem
4.3  Perancangan Pipeline Ekstraksi dan Knowledge Graph  [T1]
     4.3.1  Pipeline Ingestion Data
4.4  Perancangan Mekanisme GraphRAG                      [T2]
     4.4.1  Perancangan LangGraph Agent Pipeline
     4.4.2  Perancangan Mekanisme Retrieval Bertingkat
     4.4.3  Perancangan Antarmuka Web Streamlit
4.5  Perancangan Validasi YAML Tiga Lapis               [T3]
```

### Konten yang Perlu Ditambah/Diperkuat per Section

#### Section 4.3 (T1 — KG Construction)
**Yang sudah ada:** Penjelasan 5 pass ingestion (Tabel 16)

**Yang perlu ditambah:**
- Intro paragraph 2-3 kalimat: "Kontribusi pertama penelitian ini adalah..." dengan link ke Klaim 1
- Justifikasi mengapa schema-derived (bukan LLM-extracted): reproducibility, verifiability
- Contoh edge yang dihasilkan per kategori (bisa dalam tabel atau paragraf)
- Cross-reference ke Bab III (analisis distribusi skema OpenAPI)

#### Section 4.4 (T2 — GraphRAG Pipeline)
**Yang sudah ada:** LangGraph pipeline (Tabel 17), retrieval bertingkat (Tabel 18), antarmuka

**Yang perlu ditambah:**
- Intro paragraph: "Kontribusi kedua adalah..." dengan link ke Klaim 2
- Justifikasi kedalaman adaptif per intent type (Tabel 18) — back-reference ke analisis Bab III
- Justifikasi dual-model (Thinker + Speaker) dengan temperature berbeda
- Penjelasan *reasoning path* format: `Parent -[REL]-> Child`

#### Section 4.5 (bagian T2 — YAML Validation)
**Yang sudah ada:** 3 lapis validasi (Tabel 19)

**Yang perlu ditambah:**
- Intro paragraph: "Sebagai bagian dari sistem GraphRAG (T2), mekanisme validasi YAML..." (BUKAN "kontribusi ketiga"/T3)
- Justifikasi mengapa KG-grounded (bukan dry-run): tidak perlu live cluster
- Contoh REQUIRED_FIELDS_QUERY di Neo4j (bisa sebagai listing jika < 10 baris)

---

## BAB V — Implementasi (Setelah Phase 1 Restructure)

### Konten Outdated yang WAJIB Diperbaiki

⚠ **KRITIS:** Bab V saat ini mengandung referensi teknologi lama yang tidak sesuai sistem akhir:

| Baris | Konten Salah | Konten Benar |
|-------|-------------|--------------|
| ~40 | "Node *speaker* menggunakan Groq *llama-3.1-8b-instant* dengan `temperature`=0,1" | "Node *speaker* menggunakan GPT-4o-mini dengan `temperature`=0,1" |
| ~42 | "Batas ini ditentukan berdasarkan kapasitas konteks *tier* gratis Groq" | Hapus kalimat ini; konteks GPT-4o-mini jauh lebih besar (128K token) |
| ~18 | "kelas *ZepMemoryStore* di `src/memory/zep_store.py`" | Periksa apakah class name masih sama; Zep diganti SQLite tapi class mungkin masih bernama ZepMemoryStore |

### Konten yang Perlu Ditambah/Diperkuat per Section

#### Section 5.2 (T1 — Implementasi KG)
**Yang sudah ada:** SwaggerGraphBuilder, 5 pass, statistik KG (725 node, 18 edge types)

**Yang perlu diperkuat:**
- Jelaskan proses seleksi 14 node generik yang dikecualikan (ObjectMeta, ManagedFieldsEntry, dll.)
- Embedding: text-embedding-3-small, 1536 dim, cosine similarity, Native Vector Index Neo4j
- Contoh Cypher query untuk vector search (inline atau listing jika > 10 baris → listings/)

#### Section 5.3 (T2 — Implementasi GraphRAG Pipeline)

##### 5.3.1 LangGraph Pipeline
**Yang sudah ada:** AgentState 9 fields, 5 nodes, temperature config

**Yang perlu diperbaiki:**
- Hapus semua referensi Groq (ganti GPT-4o-mini)
- Jelaskan mengapa temperature=0.0 untuk Thinker (deterministik JSON output)
- Jelaskan mengapa temperature=0.1 untuk Speaker (variasi naratif minimal)

##### 5.3.2 Retrieval Bertingkat
**Yang sudah ada:** EXACT_MATCH_QUERY, HYBRID_VECTOR_GRAPH_QUERY, SCHEMA_DEPS_QUERY

**Yang perlu diperkuat:**
- Explain DEPTH_BY_INTENT dictionary (kedalaman adaptif per intent)
- Multi-entity retrieval untuk planning/trace_relationship/generate_yaml
- Format reasoning path: `"Parent -[REL]-> Child"` strings

##### 5.3.3 Antarmuka Pengguna
**Yang sudah ada:** UUID session, SQLite, Graphviz visualization, 4 tab

**Cek:** Apakah konten sudah akurat dengan implementasi actual? Tidak ada perubahan besar yang perlu dilakukan.

#### Section 5.4 (bagian T2 — Implementasi Validasi YAML)
**Yang sudah ada:** YAMLValidator, 3 lapis kondisional, YAMLValidationResult

**Yang perlu diperkuat:**
- Jelaskan REQUIRED_FIELDS_QUERY yang di-eksekusi ke Neo4j
- Contoh output YAMLValidationResult (4 fields: valid, syntax_errors, schema_errors, missing_fields)
- Kondisi trigger: hanya untuk intent_type == "generate_yaml"

---

## Diagram Audit

### Gambar yang Ada Saat Ini di `images/`

| File | Digunakan Di | Kualitas |
|------|-------------|---------|
| `Architecture.png` | Bab IV (fig:architecture_diagram) | Cek blur |
| `Solusi-Methodology.png` | Bab IV (fig:crispdm_diagram) | Cek blur |
| `Seq-High.png` | Bab IV (fig:sequence_diagram) | Cek blur |
| `Agent-Interaction.png` | Bab IV (fig:langgraph_pipeline) | Cek blur |
| `api-to-graph.png` | Cek di mana digunakan | Cek blur |
| `arc-graph.png` | Cek di mana digunakan | Cek blur |

### Standar Kualitas Diagram

- Minimum 300 DPI untuk cetak / 300% zoom tanpa blur pada layar
- Format PNG atau JPG (bukan PDF screenshot)
- Warna konsisten antar-diagram (pilih satu color scheme)
- Font terbaca pada zoom normal

### Diagram yang Mungkin Perlu Dibuat/Diperbarui

Berdasarkan audit konten Bab IV/V:

1. **Flowchart cascading retrieval** — saat ini di-comment di Bab V (`% \begin{figure}` at ~line 58-63). Pertimbangkan untuk uncomment dan buat gambarnya, atau hapus comment jika tidak ada gambarnya.
2. **KG schema ER-style** — visualisasi 7 kategori relasi dan 18 edge types
3. **Sequence diagram per intent type** — jika diperlukan untuk memperjelas perbedaan alur per intent

---

## Checklist Verifikasi Phase 4

### Bab IV
- [ ] Intro paragraph section KG (T1): eksplisit sebut Klaim 1
- [ ] Intro paragraph section GraphRAG (T2): eksplisit sebut Klaim 2
- [ ] Intro paragraph section validasi YAML: framing sebagai bagian T2 (BUKAN "kontribusi ketiga"/T3)
- [ ] Tidak ada pra-klaim keunggulan atas baseline di Bab IV/V (hipotesis)
- [ ] Tabel 16, 17, 18, 19 masih ter-reference dengan benar
- [ ] Cross-reference ke Bab III menggunakan label yang valid
- [ ] Semua `\label{fig:...}` dan `\label{tbl:...}` ada dan digunakan

### Bab V
- [ ] ZERO referensi "Groq" atau "llama-3.1-8b-instant"
- [ ] ZERO referensi "12.000 karakter" batas konteks Groq
- [ ] Speaker: GPT-4o-mini, temperature=0.1
- [ ] Thinker: GPT-4o-mini, temperature=0.0
- [ ] DEPTH_BY_INTENT dijelaskan
- [ ] Format reasoning path dijelaskan
- [ ] Section 5.4 (T3) menjelaskan REQUIRED_FIELDS_QUERY ke Neo4j
- [ ] Cross-reference tabel (tbl:ingestion_pipeline, tbl:langgraph_nodes, tbl:intent_depth_iv, tbl:yaml_validation_iv) masih valid

### Diagram
- [ ] Semua gambar yang di-\includegraphics ada filenya di `images/`
- [ ] Tidak ada `\ref{fig:cascading-retrieval}` tanpa gambar yang sesuai (saat ini di-comment)
- [ ] Gambar utama tidak blur saat 100% zoom

---

## Catatan untuk Phase Selanjutnya

- **Phase 5** (Bab VI): Update angka v12→v13 di hasil evaluasi; ablation/depth/stats/boundary sudah ada strukturnya
- **Phase 7** (Bahasa): Bab IV/V adalah bab terpanjang — alokasi lebih banyak waktu untuk audit bahasa
