# Fixture Validation Checklist — Fase 2

> Rubrik per-fixture untuk gerbang validasi manual per-kategori (Langkah 4 FASE_2.md).
> Tiap fixture PASS semua kriteria sebelum kategori di-apply.
> 🤖 = otomatis (engine / validate_dataset.py sudah cek) · 👁 = mata user.

---

## Cara memakai

Per kategori:
1. Baca tabel `fixture_fix_log.md` untuk kategori tsb (flagged items first).
2. Untuk tiap fixture, centang A1–D2 di bawah.
3. Tandai **PASS** atau **FIX (catatan spesifik)**.
4. Semua PASS → approve kategori → apply + validasi Neo4j per-kategori.
5. Ada FIX → perbaiki dulu → re-review → baru approve.

---

## A. Terjemahan Inggris

| # | Yang dipastikan | Kriteria PASS | Cara cek |
|---|-----------------|---------------|----------|
| A1 | Makna setara versi Indonesia | `question`/`answer`/`context` Inggris natural; tak ada makna hilang atau berubah | 👁 baca fixture |
| A2 | Token K8s identik | Nama node/resource/edge K8s (`PersistentVolumeClaim`, `HAS_PROPERTY`, dll.) **identik** — tidak diterjemahkan | 🤖 grep token K8s + 👁 |
| A3 | YAML verbatim | Blok ` ```yaml ` byte-identik dengan versi Indonesia (indentasi, nilai, key) | 🤖 diff blok YAML + 👁 |
| A4 | Tidak over-translate | Istilah K8s yang berfungsi sebagai nama tetap Inggris (Pod, Service, Volume, kubectl) | 👁 |

---

## B. Ground-truth hasil re-kurasi

| # | Yang dipastikan | Kriteria PASS | Cara cek |
|---|-----------------|---------------|----------|
| B1 | Bukan dump subgraf | `relevant_nodes` = neighborhood objek bersangkutan; ukuran wajar (conceptual/followup ~3–15; Pod-rooted 60–90 accepted per schema size) | 🤖 kolom rel fix_log + 👁 |
| B2 | Tiap node ada alasannya | Tiap `relevant_node` = endpoint (disebut `context`/`answer`) **atau** intermediate penghubung yang sah di jalur skema | 👁 telusuri ke context/answer |
| B3 | Node penting tercakup | Semua node disebut `context`/`answer` muncul di `relevant_nodes` | 🤖 set-diff engine + 👁 |
| B4 | `key_nodes` benar | `key_nodes ⊆ relevant_nodes` **dan** hanya node yang jawaban bergantung padanya | 🤖 subset check + 👁 |
| B5 | Nol phantom | Semua `relevant_nodes`/`key_nodes` ada di KG & `definitions.json` | 🤖 validate_dataset.py — nol NOT_IN_GRAPH |
| B6 | Edge valid & nyata | Tiap `expected_path` edge berstatus VALID di Neo4j | 🤖 validate_dataset.py |
| B7 | Tipe edge asli | `expected_path` pakai tipe edge sebenarnya (USES_STORAGE_CLASS, ONE_OF, dll.) — bukan dipaksa HAS_PROPERTY | 👁 sample 3–5 edge |
| B8 | `gt_depth` sesuai intent | conceptual/followup=2; yaml_gen/relationship/planning/command/troubleshooting/realworld=3 | 🤖 kolom depth fix_log |

---

## C. Scope & kebenaran

| # | Yang dipastikan | Kriteria PASS | Cara cek |
|---|-----------------|---------------|----------|
| C1 | In-scope `definitions` | Pertanyaan dapat dijawab dari swagger `definitions`; tidak butuh runtime/kubectl/cluster state | 👁 + resource ada di definitions.json |
| C2 | OOS rewrite konsisten | (6 OOS fixtures) question baru in-scope; `answer` konsisten dengan question baru | 👁 |
| C3 | `answer` faktual benar | Klaim K8s benar — cross-check dengan `source_reference`/K8s docs | 👁 |

---

## D. Metadata

| # | Yang dipastikan | Kriteria PASS | Cara cek |
|---|-----------------|---------------|----------|
| D1 | Field konsisten | `lang:"en"` ada; `type`/`resource`/`scope`/`multi_hop` cocok isi fixture | 🤖 + 👁 |
| D2 | Referensi valid | `source_reference`/`api_reference` terisi & relevan ke topik | 🤖 validate_dataset.py |

---

## Aturan keputusan

- **PASS**: A1–A4, B1–B8, C1–C3, D1–D2 semua lolos → kategori boleh di-apply.
- **FIX**: ada kriteria gagal → catat & perbaiki → re-review per-fixture tsb → baru approve.
- **DROP** (per D1): fixture LOW_CONF + 1 relevant node + answer tidak menyebut node KG + OOS → buang; catat di fix_log.

---

## Status per-kategori

| Kategori | Fixtures | Status | Catatan |
|----------|----------|--------|---------|
| command | 3 | ✅ applied | 3 OOS already rewritten to English (session 1); GT re-curation applied |
| troubleshooting | 5 | ✅ applied | 5 in English (3 OOS rewritten + 2 SUSPECT in-scope); GT re-curation applied |
| conceptual | 15 | ✅ applied | Terjemahkan 15; scope_accuracy_node reframed (ObjectMeta/RBAC removed); 3 D2 phantom auto-fixed by engine |
| followup | 12 | ✅ applied | Terjemahkan 12; non-FQN context entries upgraded to full FQN format |
| planning | 5 | ✅ applied | Terjemahkan 5; semua resource K8s valid, context FQN clean |
| relationship | 18 | ✅ applied | Terjemahkan 18; 3 full rewrites (hpa_deployment_pod, ingress_service_pod, pod_namespace_relation); 3 minor fixes (deployment_pod_relation, service_selector, serviceaccount_token_binding); 2 KG-topology fixes (anyof_intorstring→EnvFromSource root, secret_usage→PodSpec root) |
| realworld | 24 | ✅ applied | 4 keep; 6 rewrite (job/secret/pod-volume/container-caps); 14 drop (selection_score=0: Tekton×2, ArgoCD, Kubeflow, EKS, GKE, Istio, Podman, kubectl-behavior×3, AdmissionControllers, auth, Python-client) |
| yaml_gen | 15 | ✅ applied | Terjemahkan 15; 2 prose answers → proper YAML (clusterrole_read_pods, configmap_env); all context FQN-upgraded; configmap_env rel=1 correct (ConfigMap is KG leaf) |
