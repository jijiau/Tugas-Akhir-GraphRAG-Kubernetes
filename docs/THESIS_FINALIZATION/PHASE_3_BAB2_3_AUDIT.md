# Phase 3 — Bab II & III: Audit dan Sinkronisasi

**Status:** PENDING  
**Prasyarat:** Phase 1 selesai (struktur T1/T2/T3 sudah ada)  
**Referensi Aturan Bahasa:** [Plan Utama](../../.claude/plans/act-seperti-dosen-penguji-zippy-kahn.md) — bagian "Aturan Bahasa"

---

## ⚠ REVISI (Mei 2026) — FOKUS PHASE BERUBAH: KONSOLIDASI METRIK

Fokus baru Phase 3 = **mengumpulkan SELURUH definisi metrik di Bab II** (jangan loncat ke Bab III) + sinkron dengan `evaluate.py` final.

Tindakan utama:
1. **Pindahkan `subsec:metrik-domain-spesifik`** (Hop Accuracy, Path Coverage, RGA) dari Bab III → **Bab II**, digabung dengan metrik IR standar (Precision/Recall/F1/NDCG/Grounding) jadi satu section evaluasi utuh. Frame metrik domain sebagai "dikembangkan dalam penelitian ini" + sitasi (RGA → `han_graphrag_2024`).
2. **Buang pembobotan & skor Total**: hapus bahasa "skor komposit/agregasi berbobot" (cek Bab II ~baris 292). Tidak ada bobot 0,40/0,35/0,25; tidak ada `eq:total_score`.
3. **ReaQ = Hop Accuracy + Grounding** saja; *hallucination rate* dibuang dari himpunan metrik.
4. **RetQ = F1 + NDCG + Path Coverage** (precision/recall diagnostik saja).
5. Pastikan definisi di Bab II **persis sama** dengan `evaluate.py` final; perbaiki cross-ref Bab II→Bab III (Bab III hanya merujuk, tidak mendefinisikan metrik).
6. Bab III boleh pertahankan tabel pemetaan bisnis→dimensi, tapi definisi metriknya rujuk ke Bab II.

Bagian "Keputusan Framing T3" di bawah **SUDAH USANG** (T3 kini = perbandingan, validasi YAML melebur ke T2). Abaikan; gunakan blok ini.

---

## ⚠ CONSTRAINT GLOBAL (WAJIB)

- **TA.tex TIDAK BOLEH DIUBAH**
- Persona: "Penelitian ini..." (Aturan C1)
- Istilah asing: sesuai starter list Aturan C2
- Sitasi: `\parencite{}` atau `\textcite{}` — format Chicago (Aturan A9, C9)

---

## Konteks Phase 3

Bab II (Studi Literatur) dan Bab III (Analisis Masalah) perlu disinkronkan dengan reframing 3 Klaim yang sudah dilakukan di Bab I (Phase 2). Fase ini bersifat **audit dan refinement**, bukan penulisan dari awal — konten sudah ada, perlu dicek konsistensinya.

### Keputusan Framing T3 (ditetapkan saat Phase 3 planning) — ⚠ USANG (lihat banner revisi)

> Catatan revisi: T3 BUKAN lagi validasi YAML. Validasi YAML melebur ke T2; T3 = perbandingan 3 sistem (Bab VI). Isi di bawah dipertahankan sebagai arsip; ikuti banner revisi.

**T3 dipertahankan** sebagai kontribusi tersendiri dengan framing yang diperketat:

- ❌ JANGAN: "alternatif pengganti dry-run secara sempurna" — Kubernetes docs menyatakan OpenAPI schema validation tidak lengkap (tidak mencakup admission webhooks, runtime CEL rules)
- ✅ HARUS: "memanfaatkan representasi KG yang dibangun pada T1 untuk verifikasi struktural keluaran YAML — berfungsi ganda sebagai basis retrieval (T2) sekaligus validator skema berbasis graf **dalam konteks evaluasi penelitian ini**"
- Keterbatasan diakui eksplisit di Bab III/IV sebagai batasan inheren sistem

**Basis teori yang harus hadir di Bab II untuk mendukung T3:**
- `\parencite{rahman2023misconfigurations}` — Rahman et al. (2023), ACM TOSEM Q1: ~80% miskonfigurasi Kubernetes bersifat struktural, dapat dideteksi static analysis
- Literatur cukup membuktikan *prinsip pendekatan* valid; implementasi dan angka empiris (syntactic validity 0,9474 pada 97 fixture) adalah kontribusi original penelitian

**Sitasi baru yang perlu ditambah ke .bib:**
```bibtex
@article{abusalih2021domain,
  author  = {Abu-Salih, Bilal},
  title   = {Domain-specific knowledge graphs: {A} survey},
  journal = {Journal of Network and Computer Applications},
  year    = {2021},
  volume  = {185},
  pages   = {103076},
  doi     = {10.1016/j.jnca.2021.103076}
}

@article{rahman2023misconfigurations,
  author  = {Rahman, Akond and Partho, Asif and Morrison, Patrick and Williams, Laurie},
  title   = {Security Misconfigurations in Open Source {Kubernetes} Manifests: An Empirical Study},
  journal = {ACM Transactions on Software Engineering and Methodology},
  year    = {2023},
  volume  = {32},
  number  = {5},
  doi     = {10.1145/3579639}
}
```

---

## File yang Dimodifikasi

| File | Perubahan |
|------|-----------|
| `Bab II - Studi.tex` | Tambah/perkuat teori 3 Klaim; audit terminologi; cek sitasi |
| `Bab III - Analisis.tex` | Sinkron dengan RM baru; audit EDA data; cek justifikasi solusi |

**TIDAK DIUBAH:** TA.tex, tabel, gambar (kecuali caption jika perlu).

---

## BAB II — Studi Literatur

### Struktur Bab II Saat Ini (Berdasarkan Pembacaan)

```
II.1  Arsitektur Cloud Modern dan Tantangan Kompleksitas
II.2  Kubernetes: Platform Orkestrasi Kontainer
      II.2.1  Gambaran Umum Arsitektur
      II.2.2  Resource Model dan Hierarki
      II.2.3  Manifes YAML dan Infrastructure as Code
II.3  Large Language Models (LLM)
[... perlu dibaca selebihnya]
```

### Hal yang Perlu Diaudit dan Diperbaiki di Bab II

#### A. Teori Pendukung 3 Klaim (Cek Apakah Sudah Ada)

| Klaim | Teori yang Harus Ada di Bab II | Status |
|-------|-------------------------------|--------|
| Klaim 1: Schema-derived KG | Deterministic KG construction dari skema formal (bukan LLM-extracted) | Cek |
| Klaim 1: Neo4j + OpenAPI | Knowledge graph dari OpenAPI/Swagger spec | Cek |
| Klaim 2: Intent-adaptive | Intent classification & query-type-specific retrieval | Cek |
| Klaim 2: Depth traversal | Multi-hop graph traversal dan depth sensitivity | Cek |
| Klaim 3: KG-grounded validation | Schema-based YAML validation tanpa dry-run | Cek |
| Klaim 3: PyYAML + kubernetes-validate | Syntax validation tools | Cek |

**Jika belum ada:** Tambah subsection baru dengan teori yang relevan, lengkap dengan sitasi.

#### B. Audit Terminologi (Aturan B)

Grep dan perbaiki terminologi yang tidak konsisten dengan Aturan B:

| Periksa | Benar | Salah |
|---------|-------|-------|
| Edge type | `\textit{HAS\_PROPERTY}` | HAS\_PROPERTY tanpa italic |
| Node pipeline | `\textit{thinker}`, `\textit{speaker}` | Thinker, Speaker dengan kapital |
| Intent type | `\textit{generate\_yaml}` | generate\_yaml tanpa italic |
| Dataset | "*fixture*" | "test case" |
| Resource K8s | `\textit{Pod}`, `\textit{Deployment}` | Pod tanpa italic atau lowercase |
| Versi K8s | "v1.30" | "1.30", "versi 1.30" |

#### C. Audit Sitasi

Cek bahwa semua klaim di Bab II punya sitasi yang valid. Sitasi yang sudah digunakan di Bab II (dari pembacaan parsial):
- `\parencite{soldani_pains_2018}` — arsitektur microservices
- `\parencite{kubernetes_docs}` — Kubernetes orchestration
- `\parencite{k8s_docs_concepts}` — IaC YAML

Perlu ditambahkan jika belum ada:
- `\parencite{pan2024unifying}` — Knowledge graph + LLM survey
- `\parencite{wan2025empowering}` — GraphRAG vs Vector RAG
- `\parencite{liu2024deepanalysis}` — LLM code generation evaluation

#### D. Organisasi Bab II

Urutan yang direkomendasikan (domain → tool → theory → related work):
1. Konteks domain: Cloud-native, Kubernetes, YAML complexity
2. LLM dan halusinasi
3. RAG: Vector RAG → keterbatasan → GraphRAG
4. Knowledge Graph: konstruksi, traversal, Neo4j
5. Related Work: penelitian terkait GraphRAG untuk domain teknis

Jika urutan saat ini berbeda secara signifikan, pertimbangkan restruktur ringan.

---

## BAB III — Analisis Masalah

### Hal yang Perlu Diaudit di Bab III

#### A. Sinkronisasi dengan Rumusan Masalah Baru

Setelah Phase 1, RM3 sudah berubah dari "evaluasi kinerja" ke "validasi YAML berbasis KG". Pastikan:
- Bab III membahas keterbatasan validasi YAML yang ada (tanpa KG) sebagai motivasi Klaim 3
- Justifikasi pemilihan solusi (mengapa GraphRAG, bukan hanya Vector RAG) mengarah ke 3 Klaim

#### B. EDA Data: 725 Node, 735→730→725 Seleksi

Pastikan Bab III menjelaskan proses EDA dengan angka yang **konsisten** di seluruh dokumen:
- Total definisi di swagger.json: cek angka pastinya
- Setelah filter blok operasional (paths, parameters, responses): cek angka
- Setelah exclude 14 tipe generik (ObjectMeta, ManagedFieldsEntry, dll.): 725 node
- Angka ini harus konsisten dengan Bab V (implementasi) dan Bab VI (evaluasi)

#### C. 7 Kategori Relasi dan 18 Jenis Edge

Bab III harus menjelaskan taksonomi edge yang menjadi fondasi Klaim 1:
- 7 kategori relasi semantik
- 18 jenis edge total
- Contoh representatif per kategori

Cek apakah tabel taksonomi edge ada di Bab III atau di Bab II. Konsistensikan cross-reference-nya.

#### D. Analisis Kebutuhan Sistem

Pastikan kebutuhan fungsional (KF) dan non-fungsional (KNF) masih relevan dengan sistem v13:
- KF yang berkaitan dengan T1: pipeline ingestion deterministik
- KF yang berkaitan dengan T2: retrieval bertingkat, intent-adaptive depth
- KF yang berkaitan dengan T3: validasi YAML 3 lapis berbasis KG
- KNF: latensi, format output, dll.

#### E. Audit Bahasa Bab III

- [ ] Tidak ada "dimana"/"di mana" sebagai relative pronoun
- [ ] Angka desimal pakai koma (0,6943 bukan 0.6943)
- [ ] Range angka pakai en-dash (1--5 bukan 1-5)
- [ ] Persona "Penelitian ini..." konsisten
- [ ] Resource K8s italic kapital

---

## Cek Sitasi untuk Bab II & III

Verifikasi di `daftar-pustaka.bib`:

| Citekey | Fungsi |
|---------|--------|
| `soldani_pains_2018` | Microservices complexity |
| `kubernetes_docs` | K8s orchestration |
| `k8s_docs_concepts` | K8s IaC/YAML |
| `pan2024unifying` | KG+LLM unifying |
| `wan2025empowering` | GraphRAG empowering |
| `liu2024deepanalysis` | LLM code evaluation |
| `cncf_2023_survey` | CNCF usage stats |

---

## Checklist Verifikasi Phase 3

### Bab II
- [ ] Ada subsection teori untuk Klaim 1 (schema-derived KG / Neo4j)
- [ ] Ada subsection teori untuk Klaim 2 (intent classification / multi-hop)
- [ ] Ada subsection teori untuk Klaim 3 (schema-based validation)
- [ ] Related work section memposisikan penelitian ini vs. penelitian sebelumnya
- [ ] Terminologi konsisten dengan Aturan B
- [ ] Semua sitasi ada di .bib
- [ ] **SEMUA definisi metrik (IR standar + domain: Path Coverage, Hop Accuracy, RGA) ada di Bab II** (dipindah dari Bab III)
- [ ] Tanpa pembobotan/`eq:total_score`; ReaQ=Hop+Grounding; *hallucination* dibuang; RetQ=F1+NDCG+Path Coverage
- [ ] Definisi metrik di Bab II **persis sama** dengan `evaluate.py` final

### Bab III
- [ ] Bab III tidak lagi mendefinisikan metrik (`subsec:metrik-domain-spesifik` dipindah ke Bab II); hanya merujuk ke Bab II
- [ ] EDA angka konsisten: 725 node, 18 edge types, 7 kategori
- [ ] Analisis kebutuhan (KF/KNF) masih relevan dengan sistem akhir
- [ ] Justifikasi solusi mengarah ke 3 Klaim (deterministik, adaptive depth, KG validation)
- [ ] Cross-reference ke Bab IV sudah benar (setelah restruktur Phase 1)
- [ ] Bahasa audit: dimana, desimal, range, persona

---

## Catatan untuk Phase Selanjutnya

- **Phase 4** (Bab IV-V detail): Berikan justifikasi design decision yang back-referenced ke analisis di Bab III
- Cross-reference dari Bab III ke Bab IV harus menggunakan label baru setelah restruktur Phase 1
