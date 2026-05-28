# Kuesioner Validasi Domain: Sistem GraphRAG Kubernetes

**Untuk:** Expert Kubernetes / DevOps-SRE Practitioner
**Dari:** Jihan Aurelia — Tugas Akhir ITB (Sistem dan Teknologi Informasi)
**Estimasi waktu:** 30–45 menit untuk menjawab secara tertulis

> **Catatan sebelum mulai:** Semua pertanyaan ini murni tentang domain Kubernetes dan pengalaman Anda sebagai praktisi. Tidak ada pertanyaan tentang algoritma AI, embedding, atau machine learning. Jawab berdasarkan apa yang Anda tahu dan alami di lapangan.

Jika sudah membaca **Expert Brief** dan melihat **Sample Outputs**, Anda sudah punya konteks yang cukup. Jika belum, silakan baca keduanya terlebih dahulu.

---

## Bagian A — Domain-Model Correctness

*Tujuan: Memvalidasi apakah 18 jenis relasi dan 5 tipe intent yang dimodelkan sudah merepresentasikan cara Kubernetes bekerja secara akurat.*

### A1. Kelengkapan dan Akurasi Relasi Antar-Objek

Sistem ini memodelkan **18 jenis relasi** antar-objek Kubernetes, dibagi dua kelompok berdasarkan cara pembuatannya:

#### Kelompok 1 — Relasi dari struktur skema langsung (4 relasi)

Empat relasi ini dibuat otomatis dengan membaca struktur `$ref` di `swagger.json` — tidak ada keputusan manual:

| Relasi | Artinya | Contoh |
|---|---|---|
| `HAS_PROPERTY` | Objek A memiliki field yang bertipe objek B | `DeploymentSpec` punya field `selector` bertipe `LabelSelector` |
| `EXTENDS` | Objek A mewarisi/memperluas definisi objek B | `Deployment` memperluas `DeploymentSpec` via `allOf` |
| `ONE_OF` | Objek A bisa berupa salah satu dari B, C, D | `Volume` bisa berupa `ConfigMapVolumeSource` atau `SecretVolumeSource` atau `EmptyDir...` |
| `ANY_OF` | Objek A menerima kombinasi dari B atau C | `EnvFromSource` bisa dari `ConfigMapEnvSource` atau `SecretEnvSource` |

#### Kelompok 2 — Relasi berdasarkan pengetahuan domain K8s (14 relasi)

Relasi ini **tidak bisa diderive otomatis** dari swagger.json — perlu tahu cara K8s bekerja untuk mendefinisikannya. Ini yang kami minta Anda validasi:

| Relasi | Dari → Ke | Artinya | Cara mendefinisikannya |
|---|---|---|---|
| `CONTAINS_POD_TEMPLATE` | Deployment/ReplicaSet/DaemonSet/Job/StatefulSet → PodTemplateSpec | Workload ini mengandung template Pod yang akan dibuat | Mengikuti path `spec.template` di schema |
| `CONTAINS_JOB_TEMPLATE` | CronJob → JobTemplateSpec | CronJob mengandung template Job yang dijalankan terjadwal | Mengikuti path `spec.jobTemplate` di schema |
| `HAS_CONTAINER` | PodSpec → Container | Pod dijalankan dalam container | Mengikuti field `containers` di PodSpec |
| `CLAIMS_VOLUME` | StatefulSet → PersistentVolumeClaim | StatefulSet memesan storage persisten | Mengikuti `spec.volumeClaimTemplates` di schema |
| `MOUNTS_VOLUME` | PodSpec → Volume | Pod dapat menggunakan volume yang didefinisikan | Mengikuti field `volumes` di PodSpec |
| `USES_STORAGE_CLASS` | PersistentVolumeClaim → StorageClass | PVC menggunakan StorageClass untuk provisioning | Keputusan domain — PVC perlu StorageClass |
| `LOADS_CONFIGMAP` | Container → ConfigMap | Container dapat menggunakan ConfigMap sebagai env atau file | Keputusan domain — Container bisa envFrom/volumeMount ke ConfigMap |
| `USES_SECRET` | PodSpec → Secret | Pod dapat menggunakan Secret untuk credentials | Keputusan domain — Pod bisa imagePullSecrets, volumeMount Secret |
| `SELECTS_POD` | Service → Pod | Service mengarahkan traffic ke Pod via label selector | Keputusan domain — selector di Service memilih Pod |
| `ROUTES_TO_SERVICE` | Ingress → Service | Ingress meneruskan request ke Service sebagai backend | Keputusan domain — Ingress rules mengarah ke Service |
| `BINDS_ROLE` | RoleBinding/ClusterRoleBinding → Role/ClusterRole | Binding mengaitkan role dengan subject | Keputusan domain — binding adalah jembatan role ke subject |
| `BINDS_SERVICE_ACCOUNT` | RoleBinding/ClusterRoleBinding → ServiceAccount | Binding memberikan role ke ServiceAccount | Keputusan domain — subjek binding adalah ServiceAccount |
| `USES_SERVICE_ACCOUNT` | PodSpec → ServiceAccount | Pod berjalan dengan identitas ServiceAccount tertentu | Keputusan domain — Pod pakai SA untuk akses API K8s |
| `SCALES_RESOURCE` | HPA → Deployment/StatefulSet/ReplicaSet | HPA mengontrol jumlah replika resource target | Keputusan domain — HPA hanya bisa scale workload ini |

#### Data Aktual: Jumlah Edge per Tipe di Graph

Perlu diingat: ini adalah **schema-level graph**, bukan instance graph. Di schema Kubernetes, hanya ada **satu node** `Service`, satu node `Pod`, satu node `Deployment` — bukan ribuan instance seperti di cluster nyata. Jadi `SELECTS_POD` = 1 edge (Service-node → Pod-node), bukan satu per Service yang berjalan.

| Relasi | Jumlah edge | Penjelasan |
|---|---|---|
| `HAS_PROPERTY` | **1.011** | Backbone graph — semua referensi `$ref` antar-field di swagger.json |
| `SCALES_RESOURCE` | 6 | 3 target (Deployment/StatefulSet/ReplicaSet) × 2 versi HPA di K8s v1.30 |
| `CONTAINS_POD_TEMPLATE` | 5 | Deployment + ReplicaSet + DaemonSet + Job + StatefulSet |
| `ONE_OF` | 5 | Volume ONE_OF: ConfigMapVolumeSource, SecretVolumeSource, EmptyDir, HostPath, PVC |
| `BINDS_ROLE` | 2 | RoleBinding→Role + ClusterRoleBinding→ClusterRole |
| `BINDS_SERVICE_ACCOUNT` | 2 | RoleBinding→ServiceAccount + ClusterRoleBinding→ServiceAccount |
| `EXTENDS` | 2 | Pod→PodSpec + Deployment→DeploymentSpec (logical inference) |
| `ANY_OF` | 2 | EnvFromSource ANY_OF: ConfigMapEnvSource, SecretEnvSource |
| `CONTAINS_JOB_TEMPLATE` | 1 | CronJob → JobTemplateSpec |
| `HAS_CONTAINER` | 1 | PodSpec → Container |
| `CLAIMS_VOLUME` | 1 | StatefulSet → PersistentVolumeClaim |
| `MOUNTS_VOLUME` | 1 | PodSpec → Volume |
| `USES_STORAGE_CLASS` | 1 | PersistentVolumeClaim → StorageClass |
| `LOADS_CONFIGMAP` | 1 | Container → ConfigMap |
| `USES_SECRET` | 1 | PodSpec → Secret |
| `SELECTS_POD` | 1 | Service → Pod |
| `ROUTES_TO_SERVICE` | 1 | Ingress → Service |
| `USES_SERVICE_ACCOUNT` | 1 | PodSpec → ServiceAccount |
| **Total** | **~1.046** | |

`HAS_PROPERTY` mendominasi 97% dari semua edge. 14 semantic edge types secara total hanya menghasilkan ~35 edge karena masing-masing memodelkan relasi antar-tipe resource, bukan antar-instance.

> **Catatan penting untuk Anda sebagai expert:** Tiga relasi berikut adalah simplifikasi yang kami buat secara sadar dan perlu validasi:
> - `Container LOADS_CONFIGMAP ConfigMap` — dimodelkan sebagai "tipe Container dapat menggunakan tipe ConfigMap" (1 edge generik), padahal di realita hanya ConfigMap yang direferensikan eksplisit di spec yang relevan
> - `Service SELECTS_POD Pod` — 1 edge generik Service→Pod; label selector yang spesifik baru diketahui saat runtime
> - `PodSpec USES_SECRET Secret` — sama seperti ConfigMap, ini generalisasi tipe-ke-tipe

**Pertanyaan:**

- a) Apakah ada relasi K8s yang menurut Anda **kritis tapi tidak ada** dalam 14 relasi domain di atas?
  *(Contoh yang kemungkinan terlewat: NetworkPolicy → Pod, VPA → Deployment, PodDisruptionBudget → Pod, CRD → custom resource)*

- b) Dari 14 relasi domain ini, mana yang **paling sering** menjadi akar miskonfigurasi di tim Anda?

- c) Untuk tiga simplifikasi yang saya sebutkan di atas (`LOADS_CONFIGMAP`, `SELECTS_POD`, `USES_SECRET`) — apakah menurut Anda level abstraksi ini acceptable untuk tujuan "generate dan validasi YAML"? Atau justru menyesatkan?

- d) Ada relasi yang menurut Anda **tidak perlu ada** atau **penamaannya kurang tepat** secara domain K8s?

**Respons Anda:**
*(Tulis di sini — tidak ada format khusus, bebas)*

---

### A2. Kedalaman Relasi

Sistem ini hanya memodelkan relasi dari blok `definitions` di `swagger.json` — tidak mencakup relasi runtime, admission webhook, atau relasi lintas-cluster.

**Pertanyaan:**

- a) Menurut Anda, apakah batasan "schema-only, no runtime" ini membatasi kegunaan sistem secara signifikan untuk use case yang Anda temui sehari-hari?

- b) Jika sistem diperluas ke data runtime (event log, metrics, pod conditions aktual), relasi apa yang paling valuable untuk ditambahkan?

**Respons Anda:**

---

### A3. Taksonomi Intent (5 tipe)

Sistem mengenali 5 tipe pertanyaan dari pengguna:

| Intent | Deskripsi | Contoh |
|---|---|---|
| `explain` | "Apa itu X? Bagaimana X bekerja?" | "Apa itu PodDisruptionBudget?" |
| `generate_yaml` | "Buatkan YAML untuk X" | "Buat YAML Deployment dengan HPA" |
| `trace_relationship` | "Bagaimana X berhubungan dengan Y?" | "Apa relasi antara Service dan Ingress?" |
| `followup` | Modifikasi dari percakapan sebelumnya | "Tambahkan resource limit ke Deployment tadi" |
| `planning` | Desain arsitektur multi-resource | "Rancang setup web app dengan DB persisten" |

**Pertanyaan:**

- a) Apakah 5 kategori ini cukup mewakili cara DevOps engineer biasanya bertanya ke dokumentasi atau tools AI?

- b) Ada tipe pertanyaan yang sering Anda atau tim Anda ajukan yang tidak masuk ke 5 kategori ini?
  *(Contoh kemungkinan: upgrade compatibility, cost estimation, security audit, migration guide)*

- c) Apakah pemisahan antara `explain` (konseptual) dan `generate_yaml` (generasi) sesuai dengan cara Anda biasanya berinteraksi dengan tools dokumentasi?

**Respons Anda:**

---

## Bagian B — Realisme Dataset Evaluasi

*Tujuan: Memvalidasi apakah 97 skenario uji mencerminkan pertanyaan yang benar-benar muncul di lapangan.*

### B1. Rating Realisme Fixture per Kategori

Untuk tiap kategori berikut, saya sertakan 2–3 contoh pertanyaan nyata dari dataset. Tolong berikan:
- **Rating 1–5** (1=sangat artifisial, 5=sangat realistis)
- **Komentar singkat** — mengapa rating tersebut

**Conceptual (15 fixture):**
- "Apa yang terjadi pada Pod yang sedang berjalan ketika saya update image Deployment ke versi baru? Apakah ada downtime?"
- "Kapan sebaiknya menggunakan StatefulSet dibanding Deployment?"
- "Apa fungsi readinessProbe vs livenessProbe?"

Rating: ___/5 | Komentar:

**Relationship (18 fixture):**
- "Bagaimana hubungan antara Deployment, ReplicaSet, dan Pod?"
- "Apa perbedaan antara Service types (ClusterIP, NodePort, LoadBalancer)?"
- "Bagaimana HPA menentukan target Deployment yang akan di-scale?"

Rating: ___/5 | Komentar:

**YAML Generation (15 fixture):**
- "Buatkan YAML CronJob untuk menjalankan backup database setiap hari jam 2 pagi"
- "Buat YAML Deployment Node.js dengan 3 replicas, resource limit, dan readiness probe"
- "Buatkan YAML ClusterRole yang bisa read pods di semua namespace"

Rating: ___/5 | Komentar:

**Followup (12 fixture):**
- "Tambahkan env variable dari ConfigMap ke Deployment yang tadi dibuat"
- "Ubah jumlah replicas dari 3 menjadi 5"
- "Tambahkan HPA ke Deployment itu"

Rating: ___/5 | Komentar:

**Realworld — dari StackOverflow & GitHub (24 fixture):**
- "Bagaimana cara mount ConfigMap sebagai file dalam volume di dalam Pod?" (SO score: 47)
- "Pod saya terus CrashLoopBackOff dengan OOMKilled, penyebab dan solusinya?"
- "Bagaimana cara set environment variable yang berbeda per-environment di K8s tanpa duplikasi YAML?"

Rating: ___/5 | Komentar:

**Planning (5 fixture):**
- "Rancang arsitektur Kubernetes untuk web app Node.js dengan PostgreSQL yang persistent dan auto-scaling"
- "Bagaimana setup namespace isolation untuk multi-tenant environment?"

Rating: ___/5 | Komentar:

**Troubleshooting (5 fixture):**
- "Service tidak bisa reach Pod-nya, tidak ada endpoints yang terdaftar. Apa yang perlu dicek?"
- "Deployment rollout stuck di status Progressing. Cara diagnosisnya?"

Rating: ___/5 | Komentar:

---

### B2. Representativitas Realworld Fixtures

24 fixture kategori *realworld* terinspirasi dari StackOverflow questions dan GitHub issues tentang Kubernetes dengan engagement tinggi.

**Pertanyaan:**

- a) Apakah pertanyaan-pertanyaan operasional di atas mencerminkan jenis masalah yang nyata Anda atau tim Anda hadapi?

- b) Ada topik operasional K8s yang sering muncul di lapangan tapi tidak tercakup? *(Misal: network policy troubleshooting, PVC binding issues, image pull secrets across namespaces, node drain behavior, cert-manager integration, dll.)*

- c) Pertanyaan realworld yang paling sering Anda hadapi sehari-hari dan belum saya cover adalah...

**Respons Anda:**

---

### B3. Kategori yang Hilang

Apakah ada kategori pertanyaan K8s yang menurut Anda perlu ada tapi tidak ada dalam 8 kategori saya? Misalnya:
- Security scanning / policy audit
- GitOps workflow (ArgoCD/Flux pattern)
- Multi-cluster management
- Upgrade/migration guidance
- Cost optimization
- Observability setup

**Respons Anda:**

---

## Bagian C — Utilitas Praktis

*Tujuan: Memahami di mana sistem ini akan punya nilai nyata dalam workflow DevOps.*

### C1. Kelayakan Output untuk Produksi

Berdasarkan 5 contoh output di dokumen **Sample Outputs**:

**Pertanyaan:**

- a) Untuk contoh YAML (CronJob backup, Deployment + HPA) — apakah Anda akan langsung pakai output ini di staging, atau masih butuh review manual? Apa yang perlu diubah?

- b) Untuk output troubleshooting (OOMKilled) — apakah panduan yang diberikan sudah actionable untuk junior engineer di tim Anda?

- c) Secara keseluruhan, level kepercayaan Anda terhadap output sistem ini adalah: *(pilih satu)*
  - [ ] Bisa langsung ke produksi tanpa review
  - [ ] Butuh review ringan (5–10 menit) sebelum dipakai
  - [ ] Butuh review mendalam — hanya dipakai sebagai starting point
  - [ ] Terlalu berisiko — tidak akan dipakai tanpa verifikasi penuh

**Respons Anda:**

---

### C2. Posisi dalam Workflow DevOps

**Pertanyaan:**

- a) Dalam workflow harian Anda, di tahap mana sistem seperti ini paling berguna?
  *(Misal: onboarding junior, draft konfigurasi awal, PR review, dokumentasi internal, incident response, dll.)*

- b) Tools yang saat ini Anda pakai untuk kebutuhan serupa (generate YAML, cari dokumentasi K8s, debug konfigurasi):
  - Tool 1: ___ | Untuk apa: ___
  - Tool 2: ___ | Untuk apa: ___
  - Tool 3: ___ | Untuk apa: ___

- c) Jika dibandingkan dengan tools tersebut, apa nilai tambah spesifik yang Anda lihat dari sistem ini? Dan apa yang masih kurang?

**Respons Anda:**

---

### C3. Adopsi Hipotetikal

Jika sistem ini sudah production-grade:

**Pertanyaan:**

- a) Siapa di tim Anda yang paling akan diuntungkan oleh sistem ini? (junior engineer, senior devops, platform engineer, all of them?)

- b) Fitur apa yang **harus ada** agar Anda mau menggunakan ini dalam proyek nyata?
  *(Misal: output diff dari konfigurasi existing, integrasi dengan kubectl, support CRD tambahan, validasi di-cluster, multi-cluster support, dll.)*

- c) Red flag apa yang akan membuat Anda **tidak** mau menggunakannya?

**Respons Anda:**

---

## Bagian D — Gap dan Boundary Condition

*Tujuan: Memvalidasi prediksi kami tentang di mana sistem ini efektif dan di mana ia gagal.*

### D1. Validasi Boundary Condition

Kami mengukur **RetQ-gain** (seberapa besar GraphRAG lebih baik dari Vector RAG dalam menemukan informasi yang relevan, per skenario uji). Nilai positif = GraphRAG lebih baik; nilai negatif = Vector RAG ternyata lebih baik.

**Temuan per tipe pertanyaan:**

| Tipe pertanyaan | Gain rata-rata | Interpretasi kami |
|---|---|---|
| Followup (lanjutan dari percakapan) | **+0,593** | Graph traversal sangat efektif — konteks relasional sudah dibangun |
| Planning (arsitektur multi-resource) | **+0,586** | Graph menemukan dependency antar banyak resource sekaligus |
| Command (perintah kubectl) | **+0,541** | Relasi struktural membantu identifikasi resource yang tepat |
| Troubleshooting (diagnosis error) | **+0,406** | Graph menemukan path Pod→Status→Error dengan akurat |
| Conceptual, YAML gen, Relationship | +0,21 s/d +0,37 | Gain positif tapi lebih kecil |
| **Realworld (StackOverflow-style)** | **+0,041** | Hampir tidak ada gain — bottleneck terbesar sistem |

**Temuan per tingkat kompleksitas relasi resource (graph degree):**

| Tingkat | Contoh resource | Gain rata-rata | Interpretasi kami |
|---|---|---|---|
| **Rendah** — degree 2 | ConfigMap, Secret | **−0,089** | GraphRAG justru lebih *buruk* — resource terlalu sederhana, Vector RAG sudah cukup |
| **Sedang** — degree 3–7 | Deployment (7), StatefulSet (6), Service (5), HPA (4) | **+0,35 s/d +0,55** | Sweet spot — traversal kaya tapi tidak noise |
| **Tinggi** — degree ≥17 | Pod (jika ditanya langsung) | **negatif** | Terlalu banyak relasi → noise, presisi turun |

*Catatan: degree = jumlah jenis relasi langsung yang dimiliki resource di knowledge graph.*

**Boundary condition yang kami rumuskan:**

```
GraphRAG signifikan lebih baik JIKA:
  → pertanyaan bersifat relasional (followup, planning, command, troubleshooting)
  DAN/ATAU resource yang ditanyakan punya degree 3–7 di graph

GraphRAG tidak unggul atau justru lebih buruk JIKA:
  → pertanyaan operasional luas yang butuh pengetahuan runtime
  → resource terlalu sederhana (degree 2: ConfigMap, Secret)
  → resource terlalu generik (degree ≥17: Pod langsung)
```

**Satu temuan menarik:** flag "pertanyaan multi-hop" ternyata bukan prediktor yang kuat (korelasi tidak signifikan). Yang lebih prediktif adalah **tingkat konektivitas resource** di graph (korelasi +0,442, sangat signifikan). Artinya: bukan "seberapa dalam traversalnya", tapi "seberapa kaya relasi resource yang ditanyakan".

**Pertanyaan:**

- a) Berikut dua pertanyaan dari dataset dengan karakteristik berbeda:
  - **Followup** *(gain +0,593)*: *"Tambahkan HPA ke Deployment yang tadi dibuat — scale antara 2–10 replicas saat CPU > 70%"*
  - **Conceptual** *(gain lebih kecil)*: *"Apa itu PodDisruptionBudget?"*

  Untuk menjawab pertanyaan **followup** dengan benar, apakah Anda perlu tahu relasi struktural antara HPA dan Deployment (misalnya: `scaleTargetRef` di HPA harus merujuk ke `apiVersion` dan `name` Deployment yang tepat)? Apakah menurut Anda ini yang membuat pertanyaan followup lebih "relasional" dibanding conceptual?

- b) Data kami menunjukkan: sistem lebih buruk dari baseline di **ConfigMap** (gain = −0,089) tapi jauh lebih baik di **Deployment** (gain ≈ +0,55). Interpretasi kami: ConfigMap adalah resource yang relatif *berdiri sendiri* — ia hanya menyimpan data, dan cara menggunakannya bisa dijelaskan tanpa perlu tahu relasi ke resource lain. Deployment sebaliknya — pemahaman yang benar membutuhkan pengetahuan tentang ReplicaSet, PodTemplateSpec, HPA, label selector, dsb.
  
  **Apakah interpretasi ini sesuai dengan pengalaman Anda?** Jika tidak, resource mana yang menurut Anda justru "sederhana di schema tapi kompleks di praktik", atau sebaliknya?

- c) Tunjukkan tiga pertanyaan *realworld* dari dataset kami (terinspirasi StackOverflow):
  - *"Bagaimana cara mount ConfigMap sebagai file dalam volume di dalam Pod?"*
  - *"Pod stuck di status Pending padahal resource node masih tersedia — apa yang harus dicek?"*
  - *"Bagaimana cara set environment variable berbeda per-environment tanpa duplikasi YAML?"*

  Untuk tiap pertanyaan, jawab: **apakah pertanyaan ini bisa dijawab akurat hanya dari dokumentasi schema API Kubernetes (swagger.json), tanpa perlu tahu runtime state, log, atau tool seperti Helm/Kustomize?**
  - Pertanyaan 1: Bisa / Tidak bisa / Sebagian — alasan singkat: ___
  - Pertanyaan 2: Bisa / Tidak bisa / Sebagian — alasan singkat: ___
  - Pertanyaan 3: Bisa / Tidak bisa / Sebagian — alasan singkat: ___

- d) Apakah ada resource Kubernetes yang menurut Anda **kelihatan sederhana** (sedikit field, sedikit konfigurasi) tapi justru sering menjadi sumber miskonfigurasi yang tidak terduga? Atau sebaliknya — resource yang kelihatan kompleks tapi sebenarnya mudah begitu paham satu hal kuncinya?
  *(Jawaban ini membantu kami mengidentifikasi kasus di mana prediksi boundary condition kami mungkin salah)*

**Respons Anda:**

---

### D2. Gap Pengetahuan Operasional

Sistem hanya mengetahui apa yang ada di `swagger.json` — struktur schema dan relasi antar-objek. Ia tidak tahu:
- Behavior runtime (kenapa scheduler tidak menjadwalkan Pod di node tertentu)
- Event log dan error messages dari controller
- Best practice operasional yang tidak tertulis di schema
- Helm chart patterns, Kustomize conventions

**Pertanyaan:**

- a) Menurut Anda, gap ini bisa ditutup hanya dengan menambah lebih banyak relasi di graph, atau memang butuh sumber data yang berbeda sama sekali?

- b) Jika harus pilih satu sumber data tambahan (selain swagger.json) yang paling akan meningkatkan kegunaan sistem untuk Anda, apa itu?
  *(Misal: event log Kubernetes, Helm chart corpus, runbook internal tim, audit log, metrics dari Prometheus, dokumentasi HTML resmi)*

- c) Untuk pertanyaan troubleshooting seperti "Pod stuck di Pending dengan resource tersedia" — informasi apa yang Anda butuhkan untuk menjawabnya yang tidak mungkin ada di swagger.json?

**Respons Anda:**

---

### D3. Directionality Graph (Pertanyaan Lanjutan — Opsional)

*Lewati bagian ini jika tidak familiar dengan konsep directed graph.*

Knowledge graph yang dibangun bersifat **satu arah**: jika `RoleBinding → ServiceAccount` ada di schema, itu berarti sistem tahu cara retrieve ServiceAccount dari konteks RoleBinding. Tapi jika Anda mulai dari ServiceAccount, sistem tidak otomatis tahu bahwa ServiceAccount itu terikat ke RoleBinding tertentu — karena edge hanya dari RoleBinding ke ServiceAccount, bukan sebaliknya.

Ini adalah keputusan desain: edge A→B merepresentasikan "A bergantung pada B untuk didefinisikan" (dependensi struktural), bukan relasi dua arah.

**Pertanyaan:**

- a) Dari perspektif Kubernetes, apakah ini cara yang masuk akal untuk merepresentasikan schema dependency? Atau menurut Anda ada relasi tertentu yang seharusnya dua arah?

- b) Contoh konkret: `Deployment → Service` tidak ada di graph saya (Deployment tidak secara eksplisit me-reference Service di schema). Untuk pertanyaan "Service mana yang me-route traffic ke Deployment ini?" sistem tidak bisa menjawab dari graph. Apakah ini limitasi yang Anda harapkan atau mengejutkan Anda?

**Respons Anda:**

---

## Penutup

Terima kasih sudah meluangkan waktu. Kontribusi Anda akan dikutip dalam dokumen tugas akhir sebagai **validasi domain dari praktisi Kubernetes**.

**Preferensi attribusi:**
- [ ] Nama lengkap dan jabatan/organisasi boleh disebutkan
- [ ] Hanya jabatan/pengalaman, tanpa nama (misal: "Senior DevOps Engineer dengan 5 tahun pengalaman K8s")
- [ ] Anonymized sepenuhnya

**Apakah Anda bersedia dihubungi untuk follow-up jika ada jawaban yang perlu klarifikasi?**
- [ ] Ya — hubungi via: ___
- [ ] Tidak

**Apakah ada hal lain yang ingin Anda sampaikan tentang sistem ini yang tidak tercakup dalam pertanyaan di atas?**

*(Ruang bebas — tulis di sini)*
