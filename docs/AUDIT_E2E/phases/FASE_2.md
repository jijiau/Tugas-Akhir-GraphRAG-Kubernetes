# FASE 2 — Re-kurasi Ground-Truth Fixture (data)

> Dokumen rujukan stabil Fase 2 Audit E2E. Selaras `CHARTER.md` + `STATUS.md` + `STYLE_GUIDE.md`. Tunduk pada **INTEGRITY GUARDRAIL** (koreksi bug terbukti salah, bukan tuning; tiap perubahan dikonfirmasi user).
>
> **Status preflight (terverifikasi 2026-06-11):** Neo4j ON · **725** Definition node (sesuai KG terdokumentasi) · **18** tipe edge hadir · node v1.30 ada · snapshot `git tag pre-fase2-fixtures` (→ commit `9f847cb`) dibuat. Catatan: edge semantik sangat jarang (`HAS_PROPERTY`=1011 dominan; sisanya 1–6 instans) — konsisten F9/F14.

---

## Context — kenapa fase ini ada

Skrip [scripts/expand_relevant_nodes.py](../../../scripts/expand_relevant_nodes.py) **membalik logika ground-truth**: ia menimpa `relevant_nodes` + `expected_path` SEMUA fixture dengan **dump seluruh subgraf** resource (traversal depth 1–3, semua 18 edge). GT seharusnya mencerminkan **apa yang dibutuhkan pertanyaan**, bukan apa yang kebetulan dikembalikan retriever.

Akibatnya (bug **F2**, root-cause kelas 2 = gold-standard bug, *terbukti salah*):
- `relevant_nodes` membengkak (mis. `kubectl_force_delete_pod` = 86 node vs ~8 ditelusuri) → **recall rendah** → F1 rendah → **RetQ ditekan** (0,6631).
- `expected_path` membengkak (mis. 111 edge) → **path_coverage rendah**; juga `d_gt` salah untuk hop_accuracy (F3, Fase 1).
- `key_nodes` membengkak (= `relevant_nodes` pada fixture OOS) → **faithfulness rendah** → AnsQ ditekan (0,5771).

Mekanika konsumsi GT terverifikasi di `scripts/evaluate.py:302-356` (`relevant_nodes`→precision/recall/f1/ndcg; `expected_path`→path_coverage) & `:224-235` (`key_nodes`→faithfulness). Re-kurasi ke GT benar menaikkan angka **secara sah** (perbaikan gold-standard, bukan tuning).

**Sumber kebenaran:** git-recovery TIDAK viable (fixture `command`/`troubleshooting` lahir sudah bloated). Sinyal hand-authored = field **`context`** + node disebut di **`answer`**, diverifikasi ke Neo4j. (⚠️ `realworld` ber-`context:[]` → lihat empty-context fallback.)

**Urutan eksekusi (dikoreksi user):** **Fase 2 → Fase 1 → Fase 3**. `gt_depth` dari sini dikonsumsi F3 di Fase 1. Re-kurasi tak bergantung perubahan kode Fase 1 (mis. F14): `expected_path` pakai tipe edge asli KG.

**Strategi bahasa — EVALUASI PENUH BAHASA INGGRIS (keputusan user).** Sistem berinteraksi dalam bahasa Inggris; evaluasi sepenuhnya Inggris (n penuh, tanpa subset Indonesia). Justifikasi:
1. **Persona pengguna**: praktisi K8s beroperasi dalam Inggris (swagger, `kubectl`, galat API, dokumentasi) → Inggris **adalah** bahasa deployment.
2. **Penyelarasan substrat**: nama+deskripsi node KG, prompt thinker/speaker, ekstraksi intent semuanya Inggris (`vector_index.py:60-61`, `prompts.py`) — sebelumnya hanya jawaban akhir di-Indonesia-kan (`prompts.py:36`).
3. **Memperbaiki confound yang TESIS akui**: Bab VI:52 & Bab VII:26 menyatakan eval cross-lingual **meremehkan** faithfulness → beralih ke Inggris menghapus limitasi yang diakui, bukan menciptakan keunggulan.
4. **Tak melanggar bagian terkunci**: Bab I (Tujuan/Rumusan/Batasan) & Abstrak tak memuat klaim bahasa Indonesia (terverifikasi grep).

**Syarat integritas (mengikat):** wajib lapor **Indonesia-baseline → Inggris-final berdampingan** (baseline dari `_final` CSV lama); atribusikan kenaikan ke penghilangan confound. Karena re-run mengubah dua hal (GT + bahasa), Fase 3 usahakan pemisahan efek atau akui keduanya. Konsekuensi: flip speaker → Inggris (**Fase 1**, `prompts.py:36`); tulis ulang caveat Bab VI:52 & VII:26 + framing RAGAS (**Fase 4/5**); nyatakan scope "interaksi sistem berbahasa Inggris" + justifikasi di Bab I Batasan/Bab IV (**Fase 5**). **Dokumen tesis tetap bahasa Indonesia** (syarat ITB) — hanya bahasa interaksi sistem yang Inggris.

---

## Keputusan terkunci (user)

| # | Keputusan |
|---|-----------|
| D1 | Jumlah fixture **boleh berubah** (tak dikunci 97): per fixture **update / buang / (tambah)** sesuai ketersediaan di `data/definitions.json` (735 def). Default Fase 2: update atau buang; **tidak menambah** kecuali sub-keputusan terpisah. |
| D2 | 3 node phantom (`AccessMode`, `SecretType` tak ada di KG; `StorageClass` FQN salah) → fix FQN / buang. |
| D3 | Metode: context-driven semi-otomatis (subgraf-minimal Neo4j; cek ketersediaan ke `definitions.json`) + spot-review. |
| D4 | Cakupan: SEMUA fixture, metodologi tunggal konsisten. |
| D5 | Bahasa: **eval penuh Inggris**, tanpa subset Indonesia. Terjemah `question`/`answer`/`context`; node-name & YAML verbatim. Lapor before/after. |
| D6 | Target `relevant_nodes` **diputuskan dari PILOT** (5 fixture). Keadilan embed F15/F1 & flip speaker **ditunda Fase 1**. |

---

## Metodologi re-kurasi (context-driven, semi-deterministik)

Per fixture, hitung **subgraf-penghubung minimal** (bukan dump):

1. **Seed (answer-bearing):** FQN dari `context` (regex `io\.k8s\.[\w.]+`) + node disebut di `answer` (cocok kata-utuh case-sensitive ke kosakata KG) + resource root.
   - **Empty-context fallback** (`realworld` dll ber-`context:[]`): seed dari root + answer-mention saja; tandai **low-confidence**; bila answer pun tak menyebut node KG → kandidat buang.
2. **Verifikasi** seed ke KG + `definitions.json`; node tak ada → flag phantom (F4): fix FQN / buang.
3. **Subgraf-minimal:** shortest-path antar seed dibatasi `gt_depth`, **edge tipe asli**; **tie-break deterministik** (urut leksikografis edge+child).
   - `relevant_nodes` = root ∪ seed ∪ intermediate penghubung.
   - `expected_path` = edge jalur, format `Parent -[REL_TYPE]-> Child`.
   - `key_nodes` = subset answer-bearing (⊂ relevant_nodes).
4. **`gt_depth`** per intent (`_DEPTH_BY_INTENT`, `custom_retriever.py:33-40`): explain/followup=2; generate_yaml/trace_relationship/planning=3. Multi-entity (planning/generate_yaml): depth per-root + simpan `n_roots`.
5. Tulis balik (node sorted, edge dedup).

Metode **semi-deterministik** (tie-break + match fuzzy) — di Bab IV jelaskan apa adanya: turunan-otomatis + kurasi-manual ber-rubrik.

---

## Langkah eksekusi

**Preflight (✅ selesai):** Neo4j ON · KG 725 node / 18 edge / v1.30 · snapshot tag `pre-fase2-fixtures`.

- **Langkah 0** ✅ — tulis dokumen fase ini.
- **Langkah 1** — Terjemah seluruh fixture ke Inggris (`question`/`answer`/`context`; node-name & YAML verbatim; `lang:"en"`). `realworld` diterjemah dari teks Indonesia (tak ada asal Inggris). Sebelum re-kurasi GT. Masuk gerbang Rubrik A.
- **Langkah 2** — Bangun `scripts/recurate_fixtures.py` (`seeds_from_fixture`/`verify_in_kg`/`minimal_subgraph`/`depth_for`; empty-context fallback; tie-break; `--dry-run --report` → `fixture_fix_log.md`; apply `--category`). Deprecate `expand_relevant_nodes.py` (header SUPERSEDED).
- **Langkah 2b** — **PILOT gate (KONFIRMASI user):** 5 fixture, GT Operasional vs Semantik-minimal, ukur `compute_retq` vs output retriever nyata; pilih target (D6). Jangan apply 97 sampai lulus.
- **Langkah 3** — Dry-run report per kategori (8 batch). Tangani 6 OOS (update/buang) + 3 phantom. Semua kandidat tampil di `fixture_fix_log.md`.
- **Langkah 4** — **Gerbang validasi manual per-kategori (cakupan 100%):** tiap fixture dinilai dgn Rubrik → PASS/FIX → kategori di-approve → apply per kategori + validasi Neo4j kategori. Tak ada tulisan permanen sebelum approve.
- **Langkah 5** — Perluas `validate_dataset.py` (eksistensi node + key⊆relevant). Exit: nol `NOT_IN_GRAPH`, nol phantom, nol key⊄relevant, semua PASS rubrik.
- **Langkah 6** — Lengkapi `fixture_fix_log.md`; update `STATUS.md` (handoff Fase 1: gt_depth+n_roots untuk F3, flip speaker Inggris, isu embed F15/F1; Fase 4/5: caveat Bab VI:52/VII:26, scope statement, before/after). Commit bila diminta.

### Arah update 6 OOS (final dikonfirmasi gerbang)
| Fixture | Arah (runtime → struktur definitions) |
|---------|----------------------------------------|
| `command/kubectl_force_delete_pod` | `PodSpec`/`ObjectMeta`: `terminationGracePeriodSeconds`, `finalizers` |
| `command/kubectl_find_pods_with_env` | `EnvVar`/`EnvFromSource` di `Container` |
| `command/kubectl_export_namespace_resources` | `ObjectMeta`/`Namespace` |
| `troubleshooting/crashloopbackoff_oomkilled` | `ResourceRequirements` & `Probe` di `Container` |
| `troubleshooting/deployment_rollout_stuck` | `DeploymentSpec.strategy` & `DeploymentStatus`/`DeploymentCondition` |
| `troubleshooting/service_no_endpoints` | `ServiceSpec.selector` & `Service`→`Pod`/`Endpoints` |

Cek 2 SUSPECT (`imagepullbackoff_registry_secret`, `pod_pending_no_resources`) — kemungkinan sudah in-scope (Secret/ResourceQuota).

### Fix 3 phantom (D2)
- `persistent_volume_concept`: buang `AccessMode`. · `secret_types`: buang `SecretType`. · `storageclass_concept`: FQN → `io.k8s.api.storage.v1.StorageClass`.

---

## Rubrik Validasi Manual per-Fixture

> Dipakai di gerbang per-kategori (Langkah 4). Tiap fixture **PASS semua kriteria** sebelum kategori di-apply. 🤖 = otomatis (engine/`validate_dataset.py`) · 👁 = mata user.

**A. Terjemahan Inggris** — A1 makna setara (👁) · A2 nama node/edge K8s identik (🤖+👁) · A3 YAML verbatim (🤖+👁) · A4 tak over-translate (👁).

**B. Ground-truth** — B1 bukan dump, ukuran wajar ~3–12 (🤖+👁) · B2 tiap node ada alasan: endpoint/intermediate sah (👁) · B3 node `context`/`answer` tercakup (🤖+👁) · B4 `key_nodes`⊆relevant & answer-bearing (🤖+👁) · B5 nol phantom (🤖) · B6 tiap `expected_path` edge `VALID` di Neo4j (🤖) · B7 tipe edge asli, bukan dipaksa `HAS_PROPERTY` (👁) · B8 `gt_depth` sesuai intent (🤖+👁).

**C. Scope & kebenaran** — C1 in-scope `definitions`, tak butuh runtime (👁+def) · C2 OOS rewrite konsisten (👁) · C3 `answer` faktual benar, silang docs (👁).

**D. Metadata** — D1 `lang:"en"` ada, `type`/`resource`/`scope`/`multi_hop` cocok (🤖+👁) · D2 `source_reference`/`api_reference` valid (🤖).

**Aturan:** PASS hanya bila A1–A4, B1–B8, C1–C3, D1–D2 lolos. Ada FIX → perbaiki → re-review → baru apply kategori.

---

## Celah (devil's-advocate) & mitigasi

| # | Celah | Mitigasi |
|---|-------|----------|
| 1 | "Re-kurasi naikkan F1" tak terbukti; GT kecil bisa jatuhkan precision | PILOT (2b); target dari data (D6) |
| 2 | Target relevant_nodes tak terdefinisi | Diputuskan pilot; default operasional (sertakan intermediate) |
| 3 | `path_coverage` match substring (`:335`) tak linear | Diukur eksplisit di pilot |
| 4 | Eval Inggris vs sistem ter-deploy | Selesai: persona+substrat+confound-diakui (D5) |
| 5 | `gt_depth` skalar rusak multi-entity | depth per-root + `n_roots` |
| 6 | Fondasi Neo4j/KG tak diverifikasi | ✅ Preflight (725/18/v1.30) |
| 7 | Tak ada snapshot | ✅ tag `pre-fase2-fixtures` |
| 8 | "Reproducible" overstated | Tie-break deterministik + framing jujur |
| 9 | Kebenaran `answer` kurang dicek | Rubrik C3 wajib; low-confidence ditandai |
| 10 | Risiko state separuh-jadi | Apply/validasi per kategori + snapshot rollback |
| 11 | D1 "tambah fixture" tak terdefinisi | Default TIDAK menambah; bila perlu → sub-keputusan |
| 12 | `realworld` context kosong + tak ada asal Inggris | Empty-context fallback (seed answer+root, low-confidence) |

---

## File terdampak

- **BUAT:** `scripts/recurate_fixtures.py`; `docs/AUDIT_E2E/{phases/FASE_2.md, fixture_fix_log.md, fixture_validation_checklist.md}`; snapshot tag `pre-fase2-fixtures`.
- **UBAH/HAPUS:** `tests/fixtures/**/*.json` (terjemah + `lang:"en"`; `relevant_nodes`/`expected_path`/`key_nodes`/`gt_depth`; 6 OOS ditulis ulang; boleh dibuang).
- **UBAH:** `scripts/validate_dataset.py` (cek eksistensi node + key⊆relevant); `scripts/expand_relevant_nodes.py` (header SUPERSEDED); `docs/AUDIT_E2E/STATUS.md`.
- **BUKAN Fase 2 (→ Fase 1):** flip speaker `prompts.py:36`; keadilan embed F15/F1. `TA.tex` & `Bab *.tex` tak disentuh (angka di-update Fase 4).

## Verifikasi

1. Dry-run report tunjukkan ukuran GT turun wajar (command 86→~3–8) & key⊆relevant.
2. `validate_dataset.py` (Neo4j ON): nol `NOT_IN_GRAPH`, nol phantom.
3. Spot-check: `pvc_storageclass` stabil; `kubectl_force_delete_pod` mengecil+in-scope; `persistent_volume_concept` AccessMode hilang.
4. Mean |relevant_nodes|/|key_nodes| turun signifikan vs baseline (~24,8); catat jumlah fixture akhir.
5. Integritas terjemahan: semua Inggris; node-name & YAML tak berubah.
6. Pilot lulus (target GT terdokumentasi).
7. TIDAK menjalankan evaluate.py penuh di Fase 2 (itu Fase 3).
