# Cheatsheet 3 Klaim Utama — GraphRAG Kubernetes

---

## Klaim 1: GraphRAG Unggul di Retrieval (RetQ)

**Klaim:** GraphRAG menghasilkan *retrieval* yang jauh lebih baik daripada *baseline* berkat traversal multi-hop pada *knowledge graph*.

| Faktor | GraphRAG | Vector RAG | Vanilla LLM | Sig |
|---|---|---|---|---|
| **RetQ** | **0,7259** | 0,4255 | 0,0241 | *** |
| Path Coverage | **0,8515** | 0,5411 | 0,0722 | *** |
| Hop Accuracy | **0,3505** | 0,0000 | 0,0722 | *** |
| RGA | **0,4536** | 0,2784 | 0,0206 | *** |

**Angka kunci:**
- Δ RetQ vs Vector RAG = **+0,30** (CI 95% [+0,23; +0,37])
- Δ RetQ vs Vanilla LLM = **+0,70**
- Uji: Wilcoxon + bootstrap, koreksi Holm-Bonferroni → p < 0,001 (***)

**Bukti ablasi:**
- A2 (no_multihop): RetQ turun **−0,601***  → traversal multi-hop esensial
- A1 (no_phase1): RetQ turun **−0,249*** → exact match Phase 1 penting
- A3 (depth=2): HopAcc turun **−0,124*** → depth optimal = 3 (depth adaptif intent)
- A4 (depth=3 fixed): ≈0 n.s. → depth 3 tidak merusak, tapi adaptif lebih baik untuk explain/followup

**Poin untuk penguji:** RetQ unggul bukan dari parameter model LLM melainkan dari arsitektur retriever deterministik yang memanfaatkan struktur KG Kubernetes.

---

## Klaim 2: GraphRAG Unggul di Reasoning (ReaQ)

**Klaim:** GraphRAG menunjukkan kemampuan *reasoning* yang lebih tinggi karena konteks yang diambil lebih terstruktur dan relevan.

| Faktor | GraphRAG | Vector RAG | Vanilla LLM | Sig |
|---|---|---|---|---|
| **ReaQ** | **0,5554** | 0,3307 | 0,3351 | *** |

**Catatan:** AnsQ tidak signifikan berbeda (n.s.) — kualitas teks jawaban setara, tetapi *reasoning path* yang dilalui lebih tepat.

**Boundary condition:**
- Unggul di **semua 8 tipe fixture** (Δ selalu positif)
- Best: command +0,671, planning +0,605, followup +0,574
- Terendah: realworld +0,089 (tapi tetap positif)
- Spearman degree ρ = +0,467*** — semakin kompleks resource (banyak edge), semakin besar keunggulan GraphRAG
- Spearman hops ρ = +0,290** — multi-hop memberikan keuntungan lebih besar

**Poin untuk penguji:** Keunggulan ReaQ berasal dari *reasoning path* yang eksplisit (dapat di-trace), bukan dari LLM yang lebih canggih.

---

## Klaim 3: Validasi YAML Struktural via Knowledge Graph (tanpa dry-run)

**Klaim:** Sistem ini memperkenalkan metode validasi YAML Kubernetes berbasis *knowledge graph* yang tidak memerlukan *dry-run* pada kluster aktif — sebuah pendekatan baru yang praktis dan aman.

**Yang TIDAK diklaim:**
- Skor *syntactic validity* lebih tinggi dari *baseline* → IDENTIK (0,8947 ketiga sistem)
- Skor schema compliance lebih tinggi → tidak dibandingkan secara langsung antar-sistem

**Yang diklaim:**
1. **Kebaruan metode**: Validasi required-field via traversal KG (Layer 3) tanpa perlu kluster aktif atau `kubectl --dry-run`
2. **Bukti kontribusi (ablasi A5)**: Ketika lapisan 3 Neo4j dinonaktifkan (`no_yaml_layer3`), ReaQ turun signifikan (p = 0,007) → lapisan validasi berkontribusi nyata pada kualitas penalaran

**Angka untuk menjawab pertanyaan penguji:**
- Syntactic Validity: 0,8947 (**sama** untuk GraphRAG, Vector RAG, Vanilla LLM)
- Schema Compliance (GraphRAG, yaml_gen only): 0,7895
- Denominator: 19 fixture yang menghasilkan YAML (15 yaml_gen + 4 realworld); 17 lolos PyYAML

**Poin untuk penguji:** Nilai validitas YAML setara bukan kelemahan — justru membuktikan bahwa validasi struktural KG Layer 3 berhasil menyaring output tanpa over-constraining, sambil memberikan keuntungan pada ReaQ (A5).

---

## Evaluasi Pakar (Informasi Tambahan)

- **n=4** validator chatbot (E.1--E.4): Ahmad Afzalulhaq, Raden Dizi Assyafadi, Zaky Hassani, Muhamad Iqbal Ramadhan
- **n=5** validator fixture (E.1--E.5, termasuk Muhammad Faiq Dhiya Ul Haq)
- Relevansi jawaban: **4,42/5**
- Kepercayaan trace: **4,50/5**

---

*Referensi angka: Tabel 31 (Bab VI §6.4), Tabel 32 (ablasi), Tabel 33 (uji statistik), Tabel 34 (boundary condition)*
