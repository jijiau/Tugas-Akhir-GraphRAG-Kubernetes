# Mock Penguji — Audit E2E Fase 8

> Simulasi sidang, dibobot ke sisi **domain & konseptual** (judul, Kubernetes, GraphRAG,
> sitasi, kontribusi) sesuai arahan user — penguji berasal dari program studi STI (Sistem
> dan Teknologi Informasi), bukan murni CS/software engineering, sehingga pertanyaan
> cenderung menyasar pemahaman domain dan justifikasi konseptual, bukan hanya detail
> implementasi. Angka yang dirujuk di sini sudah melalui cross-check Pilar B (63/63 match,
> lihat `phases/FASE_8.md`) sehingga aman dipakai sebagai basis argumen di sidang.
>
> Format tiap butir: **Pertanyaan** → **Titik lemah** → **Status pertahanan** → **Rujukan**.

---

## Tema 1 — Judul & Scope

Judul: *"Implementasi Graph Retrieval-Augmented Generation untuk Meningkatkan Presisi
Retrieval dan Validitas Sintaksis pada Konfigurasi Kubernetes"*.

**T1.1 — "Meningkatkan presisi retrieval": benar-benar terbukti signifikan?**
Titik lemah: RetQ GraphRAG (0,7089) vs Vector RAG (0,2437) terlihat dramatis, tapi metrik ini
bergantung pada definisi `relevant_nodes` GT yang cakupannya luas (semua node terhubung
skema dari resource utama) — pernah diuji sensitivitasnya (Fase 4, STATUS 2026-06-17):
dengan GT proxy shortest-path yang lebih ketat, keunggulan turun dari +0,465 ke +0,027.
**Status pertahanan:** DEFENSIBLE dengan syarat jujur. Δ+0,465, p<0,001 (Wilcoxon+bootstrap,
Holm-corrected) — signifikan di GT yang dipakai. Disclosure GT-sensitivity sudah ada di Bab
VI (1 kalimat netral, keputusan user 2026-06-17, bukan disembunyikan). Jawaban sidang:
"arah keunggulan kokoh di kedua definisi GT (tetap unggul di proxy ketat), hanya
magnitudonya GT-dependent — dilaporkan apa adanya, bukan overclaim."
Rujukan: `Bab VI - Evaluasi.tex` §45 (caveat RetQ), `project_faithfulness_context_enrichment`
memory.

**T1.2 — "Meningkatkan validitas sintaksis": mengapa AnsQ GraphRAG vs Vector tidak
signifikan (p_Holm=0,067)?**
Titik lemah: klaim judul menyebut "meningkatkan", tapi AnsQ (yang memuat syntactic_validity)
composite GraphRAG-vs-Vector n.s. secara statistik.
**Status pertahanan:** DEFENSIBLE — perlu dipisahkan levelnya. Syntactic validity KHUSUS
(bukan AnsQ composite) GraphRAG = 1,0000 vs Vector 0,9333 — GraphRAG tidak pernah
menghasilkan YAML unparseable, klaim "validitas sintaksis" bertumpu pada angka ini, bukan
AnsQ composite. AnsQ composite mencampur answer_relevance (cosine similarity, ceiling
alami) yang membuat perbandingan komposit kabur. Jawaban sidang: tunjukkan tabel31 dan
pisahkan level klaim per sub-metrik, jangan biarkan penguji menyamakan "AnsQ" dengan
"validitas sintaksis".
Rujukan: tabel31, Bab VI §integrity note.

**T1.3 — Scope hanya blok `definitions` swagger.json — pantas mengklaim "Konfigurasi
Kubernetes" secara umum di judul?**
Titik lemah: tidak ada klaster aktif, tidak ada `kubectl` runtime, tidak ada CRD custom.
**Status pertahanan:** DEFENSIBLE — Batasan Masalah Bab I eksplisit mengunci scope ini
sejak awal (bukan ditemukan belakangan), dan domain "Konfigurasi Kubernetes" = manifest
YAML deklaratif, yang memang sepenuhnya derivable dari `definitions` OpenAPI schema tanpa
perlu runtime. Siapkan kalimat: "konfigurasi = artefak deklaratif (YAML), bukan state
runtime klaster — scope ini konsisten dari Rumusan Masalah sampai evaluasi."
Rujukan: Bab I Batasan Masalah, `CHARTER.md` §Scope data (locked).

---

## Tema 2 — Domain Kubernetes

**T2.1 — Mengapa hanya blok `definitions`, bukan seluruh swagger.json (paths, operations)?**
Status pertahanan: DEFENSIBLE — `definitions` berisi seluruh skema resource (struktur field,
tipe, referensi `$ref`) yang relevan untuk validasi YAML deklaratif; `paths`/`operations`
adalah REST API endpoint (operasional, bukan struktur konfigurasi) — di luar rumusan
masalah yang berfokus pada penulisan/validasi manifest, bukan pemanggilan API.

**T2.2 — Mengapa K8s v1.30 spesifik, bagaimana generalisasi ke versi lain?**
Titik lemah: hasil (725 node, 18 edge) terikat pada satu snapshot versi API.
Status pertahanan: DEFENSIBLE, sudah teruji langsung — pipeline ingestion (`parser.py`)
deterministik berbasis skema, bukan hardcode versi; ini terlihat dari genuine finding
GraphRAG schema_compliance (0,9259) < Vector (0,9655) karena GraphRAG mengonstruksi
`autoscaling/v2beta2` (deprecated di 1.26+) — bukti bahwa sistem SETIA ke skema versi yang
di-ingest, bukan berhalusinasi API modern. Generalisasi ke versi lain = re-run ingestion
terhadap swagger.json versi tsb, tanpa perubahan arsitektur. Siapkan kalimat: "arsitektur
version-agnostic secara desain; angka 725/18 spesifik untuk snapshot v1.30 yang dievaluasi."

**T2.3 — Kompleksitas YAML dunia nyata (multi-dokumen, Helm templating, Kustomize overlay)
vs fixture single-resource?**
Titik lemah: 102 fixture semuanya single-resource YAML; tidak ada validasi terhadap
multi-document manifest atau templating engine.
Status pertahanan: PARTIAL — akui keterbatasan secara langsung (sudah ada di Bab VII
Keterbatasan), jangan coba menutupi. Fixture `yaml_gen` (n=25) tetap mencakup variasi
resource type nyata (HPA, NetworkPolicy, StatefulSet+PVC, RBAC). Jawaban sidang: "batasan
ini eksplisit di Bab VII, bukan celah yang ditemukan penguji — perluasan ke Helm/Kustomize
adalah arah kerja lanjutan yang jelas."

**T2.4 — Kenapa bukan runtime `kubectl` / klaster aktif?**
Status pertahanan: DEFENSIBLE — dikunci di Rumusan Masalah Bab I sejak awal (`CHARTER.md`
§Scope data locked); command/troubleshooting fixture (F4 di bug register) sengaja
direklasifikasi out-of-scope di Fase 2 bukan dihindari diam-diam, didokumentasikan.

---

## Tema 3 — Konsep GraphRAG

**T3.1 — Definisi GraphRAG yang tepat, dan bedanya dari vector RAG biasa?**
Siapkan definisi presisi: GraphRAG = RAG yang retrieval-nya menelusuri graf terstruktur
(bukan hanya top-k similarity search) untuk menangkap relasi eksplisit antarentitas.
Perbedaan operasional konkret di sistem ini: exact match → vector fallback → multi-hop
graph traversal dengan kedalaman adaptif (`d=2` untuk explain/followup, `d=3` lainnya).

**T3.2 — "14 dari 18 edge hand-coded" — bukankah ini mengurangi klaim otomatisasi/skalabilitas?**
Titik lemah nyata (F9, sudah diaudit Fase 0): hanya 4 edge (HAS_PROPERTY, EXTENDS, ONE_OF,
ANY_OF) yang deterministik struktural; 14 sisanya (BINDS_ROLE, MOUNTS_VOLUME, dst.)
hand-coded oleh domain knowledge penulis di `parser.py:228-371`, bukan auto-derived murni.
**Status pertahanan:** JANGAN klaim "auto-derived" — CHARTER eksplisit melarang framing ini.
Jawaban jujur: "ekstraksi terdeterminasi dari skema (setiap edge dapat ditelusuri ke `$ref`
eksplisit di swagger.json — reproducible), tapi PEMETAAN 14 tipe relasi semantik ke pola
`$ref` adalah keputusan desain domain-expert, bukan inferensi otomatis dari LLM/heuristik
statistik. Ini justru kekuatan (deterministik, dapat diverifikasi) sekaligus batasan
(effort manual untuk domain baru)." Bandingkan eksplisit dengan pendekatan LLM-extraction
stokastik (Pan et al. 2024; Wan et al. 2025) yang sudah dikutip di Bab VII sebagai
pembanding — siapkan kalimat ini di kepala saat ditanya.
Rujukan: `CHARTER.md` F9, Bab VII §Kesimpulan pertama.

**T3.3 — Bagaimana cara kerja hybrid retrieval + intent-adaptive depth, dan mengapa d=2/d=3?**
Status pertahanan: DEFENSIBLE, berbasis ablation A3 (depth=2 fixed, RetQ −0,123 **,
HopAcc −0,147 ***) dan A4 (depth=3 fixed, RetQ −0,050 n.s., HopAcc +0,145) — depth
sensitivity (Bab VI §243) menunjukkan trade-off presisi-vs-cakupan yang berbeda per tipe
intent (followup optimal di d=2, yaml_gen/planning optimal di d=3). Bukan pilihan arbitrer.

**T3.4 — Novelty: ini riset baru atau aplikasi GraphRAG yang sudah ada ke domain baru?**
Titik lemah: GraphRAG sebagai teknik sudah ada (han_graphrag_2024, he2024gretriever, dst).
Status pertahanan: DEFENSIBLE untuk konteks STI/TA (bukan riset PhD) — framing kontribusi
BUKAN "GraphRAG baru" tapi (1) pipeline ekstraksi KG deterministik khusus domain K8s API,
(2) mekanisme intent-adaptive depth yang divalidasi ablation, (3) evaluasi 3-dimensi
(AnsQ/RetQ/ReaQ) yang jujur melaporkan trade-off, bukan cherry-pick. Tabel12 (perbandingan
GraphRAG existing pada domain teknis lain — civiot2025graphrag, hsgrag2025acm) sudah
memposisikan gap yang diisi riset ini (KG statis tanpa taksonomi relasi spesifik domain).

---

## Tema 4 — Audit Sitasi (`daftar-pustaka.bib`, 27 entri aktif setelah Fase 8)

**Metodologi:** setiap citekey di-grep penggunaan in-text-nya di semua `.tex`; entri dibaca
penuh untuk menilai kredibilitas venue dan kesesuaian konteks pemakaian.

**T4.1 — Temuan & fix Fase 8 (transparansi, siap dijelaskan jika ditanya):**
- `gu_2024` (MidMed, dialog medis) sempat tersitasi keliru untuk definisi Hop-Accuracy di
  Bab II §282 — sudah diganti `manning_ir_2008` (konsisten dengan 4 lokasi lain yang
  memakai rumus identik). Entri `.bib` dihapus karena jadi orphan.
- Entri `gu_2024` sebelumnya membocorkan catatan editorial internal (field `note={}`) ke
  Daftar Pustaka tercetak — sudah tidak ada di PDF final.
- Jika penguji entah bagaimana melihat draf lama dengan sitasi ini: jawaban jujur "temuan
  audit internal sebelum sidang, sudah diperbaiki, root cause = 1 instance sitasi yang
  terlewat saat penggantian sitasi massal di fase sebelumnya."

**T4.2 — Kredibilitas & kebaruan sitasi.** 27 entri: 21 artikel jurnal/arXiv, 1 buku
(Manning et al. 2008, Cambridge UP — standar emas IR), 1 prosiding (ICLR 2024), 4
misc/online (Gartner, CNCF, K8s docs ×2). Venue: IEEE TSE/TKDE, ACM TOSEM/TODAES,
Elsevier (JSS, AEI, KBS, JNCA), MDPI (Information, Future Internet), arXiv (2023–2025,
mayoritas preprint tapi domain GraphRAG memang bergerak cepat — banyak kerja rujukan inti
GraphRAG BELUM ter-peer-review pada 2024-2025, ini kondisi bidang, bukan kelemahan
metodologi pemilihan sitasi). Siapkan kalimat ini jika ditanya "kenapa banyak arXiv, bukan
jurnal": "GraphRAG adalah subbidang yang sangat baru (paper seminal Han et al. 2024 sendiri
arXiv preprint); mayoritas rujukan inti bidang ini memang belum melalui siklus review
jurnal penuh per waktu penulisan tesis — dikompensasi dengan memakai `manning_ir_2008`
(buku teks IR yang sudah mapan) untuk fondasi metrik evaluasi."

**T4.3 — Karya fondasi hadir?** Ya: asal-usul RAG umum (`rag_survey`/Gao et al. 2024,
`zhao_rag_survey_2024`), GraphRAG spesifik (`han_graphrag_2024`, `he2024gretriever`),
konstruksi KG (`hofer2024construction`, `pan2024unifying`), evaluasi RAG (`es_ragas_2023`),
IR klasik (`manning_ir_2008`), hallucination (`ji_hallucination_2023`). Tidak ada gap
fondasi yang mencolok untuk cakupan tesis S1.

**T4.4 — Orphan entry: `li_cotrag_2025`.** 0 sitasi in-text ditemukan (grep menyeluruh semua
`.tex`). Tidak tercetak di PDF (biblatex citation-driven — dikonfirmasi via biber log:
"26 citekeys" dipakai dari 27 entri). **Tidak berdampak ke PDF**, murni kebersihan `.bib`.
Tidak digate sebagai fix wajib Fase 8 (di luar scope "TA.tex read-only tapi angka/isi
tesis" — ini file pendukung yang tak terlihat pembaca). Rekomendasi: hapus saat sesi
berikutnya jika ingin `.bib` bersih, atau simpan sebagai referensi bacaan lanjutan CoT-RAG
jika relevan untuk Bab VII Saran.

**T4.5 — Duplikasi ringan: `k8s_docs_concepts` vs `kubernetes_docs`.** Dua entri terpisah
untuk halaman berbeda di situs resmi Kubernetes (Concepts vs Documentation home), dipakai
untuk klaim berbeda (IaC declaration; arsitektur cluster; schema compliance). Bukan
duplikasi tak sah — praktik lazim mengutip halaman spesifik yang mendukung klaim spesifik.
Jika ditanya: "dua URL berbeda dari sumber resmi yang sama, masing-masing mendukung fakta
berbeda — bukan sitasi ganda untuk klaim yang sama."

**T4.6 — Tidak ada sitasi fabrikasi.** "Nguyen et al. 2024" (ditolak Fase 0/Charter, tidak
ada di `.bib`, sudah dipastikan tidak muncul di manapun) dan `gu_2024` (baru diperbaiki
Fase 8) adalah dua kasus yang sudah diaudit tuntas. Tidak ditemukan kasus ketiga dalam
audit Fase 8 ini (27 entri dibaca penuh, semua venue dan tahun dapat diverifikasi kredibel
di permukaan).

---

## Tema 5 — Kontribusi & Positioning (lensa STI)

**T5.1 — Kontribusi sistem/praktis, untuk siapa?**
Jawaban terstruktur (3 kontribusi, Bab VII §Kesimpulan): (1) pipeline ekstraksi KG
deterministik berbasis OpenAPI — reproducible, dapat diaudit ke `$ref` eksplisit, berbeda
dari ekstraksi LLM stokastik; (2) mekanisme retrieval intent-adaptive depth + validasi YAML
3-lapis berbasis KG; (3) evaluasi empiris 3-dimensi (AnsQ/RetQ/ReaQ) dengan ablation +
uji signifikansi statistik penuh. Target pengguna: developer/DevOps yang menulis manifest
K8s dan butuh asisten LLM yang tidak berhalusinasi struktur skema.

**T5.2 — Validitas validasi pakar — n berapa sebenarnya, dan levelnya apa?**
Dua panel terpisah, jangan tertukar saat menjawab: (a) **n=3** praktisi DevOps/SRE untuk
validasi KELAYAKAN DATASET (realisme fixture, skala 1-5 — Tabel 27/28, Bab VI §sec:
expert_validation) — ini validasi KUALITATIF, bukan bukti kuantitatif, dinyatakan eksplisit
di teks; (b) **n=4** pakar terpisah untuk validasi KUALITAS JAWABAN sistem (§414, skor
kepercayaan Retrieval Trace 4,50/5). Total n=5 orang berbeda (memory: "n=3 validasi
kebutuhan, n=4 uji coba chatbot langsung"). Jika ditanya "kenapa n kecil": jawab bahwa ini
validasi kualitatif suportif untuk desain dataset dan UX, bukan pengganti evaluasi
kuantitatif 102-fixture yang menjadi basis klaim utama — perannya melengkapi, bukan
menggantikan RetQ/AnsQ/ReaQ.

**T5.3 — Mengapa AnsQ/RetQ/ReaQ (bukan metrik standar RAG seperti RAGAS penuh atau
BLEU/ROUGE)?**
Status pertahanan: DEFENSIBLE, ditautkan eksplisit ke Rumusan Masalah (Bab II §6):
AnsQ↔T3 (validitas sintaksis + relevansi jawaban), RetQ↔T1 (presisi retrieval, khusus
memungkinkan evaluasi GraphRAG karena reasoning_path eksplisit — RAGAS ctx_precision/
recall tidak applicable untuk graf terstruktur), ReaQ↔T2 (kualitas penalaran multi-hop).
RAGAS metrik lain (ctx_precision/recall) sengaja DIBUANG (dicatat di CHARTER, bukan
disembunyikan) karena tidak cocok untuk retrieval berbasis graf.

**T5.4 — Kejujuran melaporkan soft-spot — siap ditanya "kenapa faithfulness cuma 0,31"?**
Jangan defensif — ini SUDAH dianalisis mendalam (faithfulness decomposition, n=102,
55,6% klaim parametrik vs 41,4% berbasis dokumen — lihat memory
`project_faithfulness_context_enrichment`). Jawaban siap pakai: "sistem dirancang
open-book — LLM boleh melengkapi konteks graf dengan pengetahuan parametrik ketika KG tidak
punya nilai atribut skalar (mis. nilai default field). Ini trade-off desain sengaja, bukan
kegagalan retrieval — dikonfirmasi lebih tinggi signifikan dari Vector RAG (0,3055 vs
0,1675, Δ+0,127, p<0,001), jadi peningkatan RELATIF terhadap baseline, angka absolut
memang punya ceiling karena desain open-book." Juga siap untuk AnsQ n.s. vs Vector
(p_Holm=0,067) dan hop accuracy closure >15 edge (0,5791, lebih rendah dari focused 0,9086)
— keduanya sudah dilaporkan apa adanya di Bab VI/VII, bukan disembunyikan.

---

## Ringkasan kesiapan

| Tema | Jumlah butir | Siap? |
|---|---|---|
| 1. Judul & scope | 3 | Siap, semua sudah ada disclosure di teks |
| 2. Domain Kubernetes | 4 | Siap, 1 keterbatasan diakui terbuka (T2.3) |
| 3. Konsep GraphRAG | 4 | Siap, T3.2 (hand-coded edge) butuh kehati-hatian framing |
| 4. Sitasi | 6 | Siap, 2 temuan Fase 8 sudah diperbaiki, 1 minor belum (li_cotrag_2025 orphan, tak berdampak PDF) |
| 5. Kontribusi & positioning | 4 | Siap, semua bertumpu pada angka yang sudah ter-cross-check |

**Rekomendasi persiapan tambahan (di luar scope Fase 8, untuk sesi belajar mandiri):**
latih menjawab T3.2 dan T1.1 secara lisan tanpa membaca — dua ini paling mungkin memancing
pertanyaan lanjutan berantai dari penguji domain.
