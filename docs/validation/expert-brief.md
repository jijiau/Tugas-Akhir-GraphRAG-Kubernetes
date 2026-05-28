# Expert Brief: Validasi Domain Sistem GraphRAG Kubernetes

**Dokumen ini disiapkan oleh:** Jihan Aurelia (18222001), ITB — Sistem dan Teknologi Informasi
**Pembimbing:** Dr. Ir. Dimitri Mahayana, M.Eng.
**Tujuan dokumen:** Memberikan konteks yang cukup bagi Anda sebagai praktisi Kubernetes untuk melakukan validasi domain terhadap sistem yang dibangun dalam tugas akhir ini.

> **Positioning Kka Zaky:** *perspektif praktisi* terkait apakah sistem ini menjawab masalah nyata, apakah skenario uji realistis, dan di mana sistem ini akan berhasil atau gagal di lapangan.

**Glossary singkat**:

| Istilah | Artinya dalam konteks ini |
|---|---|
| Knowledge Graph | Peta relasi antar-objek K8s — seperti diagram dependency tapi dalam database graph |
| Graph traversal | Penelusuran peta tersebut untuk menemukan semua objek yang relevan dengan pertanyaan |
| Retrieval | Proses pengambilan konteks yang relevan sebelum LLM menjawab |
| Fixture | Skenario uji — pasangan (pertanyaan, jawaban referensi) untuk mengukur performa sistem |
| Hop | Satu langkah traversal dalam graph (A→B = 1 hop; A→B→C = 2 hop) |

---

## 1. Masalah yang Diselesaikan

### Situasi

Kubernetes adalah standar industri untuk orkestrasi container. Namun kompleksitasnya sangat tinggi:

- YAML konfigurasi sangat verbose dan hierarkis
- **Interdependensi antar-objek implisit**: kesalahan kecil seperti ketidakcocokan `label selector` memicu kegagalan berantai
- Sekitar **80% insiden operasional** berakar dari miskonfigurasi YAML *(Rahman et al., 2023)*
- **18% file konfigurasi open-source** mengandung pelanggaran standar keamanan kritis

### Solusi yang Ada dan Keterbatasannya

Engineer sering menggunakan ChatGPT / GitHub Copilot untuk generate YAML. Masalahnya:

| Alat | Kelebihan | Kelemahan |
|---|---|---|
| ChatGPT / Copilot | Mudah, cepat | Sering "halusinasi" — generate field yang tidak valid, atau melewatkan field wajib |
| `kubectl explain` | Akurat per-field | Tidak menjelaskan relasi antar-objek, tidak generate YAML lengkap |
| Dokumentasi resmi | Lengkap | Perlu waktu baca, tidak interaktif |

**Akar masalah:** LLM hanya tahu "kesamaan teks" dari dokumentasi, bukan *relasi struktural* antar-objek Kubernetes (misalnya: `Deployment → ReplicaSet → PodTemplate → Container → ResourceRequirements`). Akibatnya, YAML yang dihasilkan mungkin sintaksisnya benar tapi semantiknya salah.

---

## 2. Solusi yang Dibangun

### Inti Ide

Alih-alih membiarkan LLM mengandalkan memori pelatihan, sistem ini:

1. **Mengekstrak struktur resmi Kubernetes** dari file `swagger.json` v1.30 (spesifikasi API resmi Kubernetes) menjadi sebuah *knowledge graph* — peta dependency antar-objek Kubernetes
2. **Saat pengguna bertanya**, sistem menelusuri peta ini untuk menemukan semua objek yang relevan dan hubungannya (*graph traversal*)
3. **Memberikan konteks struktural** itu ke LLM, sehingga jawaban atau YAML yang dihasilkan selalu mengacu pada skema resmi, bukan "ingatan" LLM

### Ilustrasi: Cara Kerja untuk Pertanyaan "Buat YAML Deployment dengan HPA"

```
Pengguna: "Buat YAML Deployment dengan HPA dan resource limit"
    │
    ▼
[Thinker — GPT-4o-mini]
    Mengenali: primary=Deployment, related=[HPA, Container]
    │
    ▼
[Retriever — menelusuri knowledge graph]
    Deployment → DeploymentSpec → PodTemplateSpec → PodSpec → Container → ResourceRequirements
    HPA → HorizontalPodAutoscalerSpec → CrossVersionObjectReference → Deployment (target)
    Hasil: semua field wajib, struktur relasi yang benar
    │
    ▼
[Speaker — GPT-4o-mini]
    Generate YAML dengan konteks dari graph → YAML yang valid dan lengkap
    │
    ▼
[Validator 3 lapis]
    Lapis 1: Cek sintaksis YAML (PyYAML)
    Lapis 2: Cek skema K8s v1.29 (kubernetes-validate)
    Lapis 3: Cek field wajib dari knowledge graph
```

### Komponen Teknis (Ringkas)

| Komponen | Detail |
|---|---|
| **Knowledge Graph** | Neo4j — 725 node (objek Kubernetes), 18 jenis relasi antar-objek |
| **Sumber data KG** | `swagger.json` Kubernetes v1.30 resmi (3,67 MB, blok `definitions` saja) |
| **LLM** | GPT-4o-mini untuk memahami pertanyaan + generate jawaban |
| **Antarmuka** | Streamlit (web chat) |
| **Kedalaman penelusuran** | Adaptif: 2 hop untuk pertanyaan konseptual, 3 hop untuk generate YAML/relasional |

---

## 3. Dataset yang Digunakan

### Dataset 1 — Sumber Knowledge Graph

- **File:** `swagger.json` Kubernetes v1.30 (spesifikasi API resmi)
- **Isi yang diekstrak:** Blok `definitions` — 730 definisi objek mentah
- **Setelah filtering:** 725 node final
  - Dikecualikan: 14 tipe utility generik (`Quantity`, `IntOrString`, `LocalObjectReference`, `ObjectMeta`, `ManagedFieldsEntry`, dll.) karena dipakai oleh 19–136 resource sekaligus — jika dimasukkan akan jadi noise pada penelusuran graph
  - Dikecualikan: 5 definisi noise lainnya
- **Relasi yang dibangun:** 18 jenis edge dalam 7 kategori

**7 Kategori Relasi:**

| Kategori | Jenis Relasi | Contoh |
|---|---|---|
| Struktural | `HAS_PROPERTY`, `EXTENDS`, `ONE_OF`, `ANY_OF` | Deployment memiliki DeploymentSpec |
| Workload | `CONTAINS_POD_TEMPLATE`, `CONTAINS_JOB_TEMPLATE`, `HAS_CONTAINER` | Deployment mengandung PodTemplate |
| Penyimpanan | `CLAIMS_VOLUME`, `MOUNTS_VOLUME`, `USES_STORAGE_CLASS` | PodSpec mounts Volume |
| Konfigurasi | `LOADS_CONFIGMAP`, `USES_SECRET` | Container loads ConfigMap |
| Jaringan | `SELECTS_POD`, `ROUTES_TO_SERVICE` | Service selects Pod |
| RBAC | `BINDS_ROLE`, `BINDS_SERVICE_ACCOUNT`, `USES_SERVICE_ACCOUNT` | RoleBinding binds ServiceAccount |
| Autoscaling | `SCALES_RESOURCE` | HPA scales Deployment |

### Dataset 2 — Dataset Evaluasi (Fixture)

- **Total:** 97 *fixture* (skenario uji)
- **Distribusi 8 kategori:**

| Kategori | Jumlah | Karakteristik | Contoh Pertanyaan |
|---|---|---|---|
| Conceptual | 15 | "Apa itu X? Bagaimana cara kerja X?" | "Apa yang terjadi ketika saya update image Deployment?" |
| Relationship | 18 | "Bagaimana X berhubungan dengan Y?" | "Bagaimana hubungan Deployment, ReplicaSet, dan Pod?" |
| YAML Generation | 15 | "Buatkan YAML untuk X" | "Buat YAML CronJob backup database tiap jam 2 pagi" |
| Followup | 12 | Modifikasi/ekstensi konfigurasi sebelumnya | "Tambahkan resource limit ke Deployment yang tadi" |
| Realworld | 24 | Pertanyaan operasional nyata dari StackOverflow & GitHub | "Bagaimana mount ConfigMap sebagai file dalam volume?" |
| Planning | 5 | Arsitektur multi-resource | "Rancang arsitektur web app dengan DB yang persistent" |
| Troubleshooting | 5 | Diagnosis error K8s | "Pod OOMKilled terus, penyebab dan solusinya?" |
| Command | 3 | Perintah kubectl | "Kubectl command untuk lihat pods di semua namespace?" |

- **Sumber fixture:**
  - Conceptual, relationship, yaml_gen, followup, planning, command, troubleshooting: dirancang berdasarkan dokumentasi resmi K8s dan pola penggunaan umum
  - Realworld (24 fixture): dipilih dari StackOverflow questions dengan skor tinggi (rata-rata SO answer score = 47) + GitHub issues K8s — pertanyaan real dari komunitas
- **Validasi awal:** 3 praktisi DevOps/SRE independen memberikan rating realisme rata-rata **3,87 / 5,00**
- **Setiap fixture berisi:** pertanyaan input, ground truth (jawaban/YAML referensi), node-node graph yang relevan, dan jalur traversal yang diharapkan

---

## 4. Hasil Evaluasi

### Perbandingan 3 Sistem (97 fixture)

| Sistem | Kualitas Jawaban | **Kualitas Retrieval** | Kualitas Penalaran | **Total** |
|---|---|---|---|---|
| **GraphRAG (sistem ini)** | 0,574 | **0,685** | **0,899** | **0,694** |
| Vector RAG (baseline) | **0,598** | 0,425 | 0,893 | 0,611 |
| Vanilla LLM (tanpa retrieval) | 0,588 | 0,024 | 0,631 | 0,402 |

- **Perbedaan GraphRAG vs Vector RAG statistically significant** (p < 0,001 untuk Retrieval Quality)
- **YAML syntactic validity:** 100% — semua YAML yang dihasilkan lolos validator
- **Multi-hop reasoning success:** 100% — traversal selalu berhasil menemukan jalur relasional

### Di Mana Sistem Ini Unggul dan Lemah

| Situasi | Performa | Alasan |
|---|---|---|
| Pertanyaan relasional (followup, planning, command) | Terbaik (+0,54–0,59 gain) | Graph traversal menemukan dependency chain secara akurat |
| Resource dengan banyak relasi (Deployment, StatefulSet, Service) | Unggul | Node degree 3–7: cukup relasi untuk traversal kaya tapi tidak noise |
| ConfigMap/Secret sebagai topik utama | Lebih lemah | Node degree 2: terlalu sederhana, Vector RAG sudah cukup |
| Pertanyaan operasional kompleks (debug cluster, best practice monitoring) | Lemah (skor 0,50) | Membutuhkan pengetahuan runtime/operasional yang tidak ada di spesifikasi API |

---

## 5. Kebutuhan interview

Diskusi akan mencakup 4 area validasi. **Anda tidak perlu menilai aspek AI/machine learning** — fokus pada perspektif K8s praktisi:

| Area | Pertanyaan Inti |
|---|---|
| **A. Domain-model correctness** | Apakah 18 jenis relasi dan 5 tipe intent sudah merepresentasikan cara K8s bekerja secara akurat? |
| **B. Realisme fixture** | Apakah 97 skenario uji mencerminkan pertanyaan yang benar-benar muncul di lapangan? |
| **C. Utilitas praktis** | Di titik mana dalam workflow DevOps Anda sistem ini akan paling bernilai? |
| **D. Gap & boundary** | Apakah prediksi kami soal di mana sistem ini kuat/lemah sesuai pengalaman Anda? |

---

*Terima kasih atas waktu dan perspektif Anda. Kontribusi Anda akan dikutip dalam dokumen tugas akhir sebagai validasi domain dari sisi praktisi.*
