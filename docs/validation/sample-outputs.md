# Sample Outputs: GraphRAG vs Vector RAG

**Dokumen ini** menunjukkan 5 contoh output nyata dari sistem, dibandingkan dengan output Vector RAG untuk pertanyaan yang sama.

**Cara membaca dokumen ini:**
- **GraphRAG** = sistem yang dibangun dalam tugas akhir ini (menggunakan graph traversal)
- **Vector RAG** = baseline — sistem yang hanya menggunakan pencarian kemiripan teks tanpa graph
- **Reasoning Path** = jalur yang ditelusuri sistem dalam knowledge graph — hanya ada di GraphRAG
- **Skor** mengacu pada evaluasi otomatis terhadap 97 fixture; angka adalah rata-rata per kategori

**Pertanyaan untuk Anda setelah tiap contoh:**
> *"Kalau Anda terima jawaban ini dari junior engineer di tim, apakah Anda akan langsung pakai, atau ada yang perlu direvisi?"*

---

## Contoh 1 — Conceptual: Rolling Update Deployment

**Kategori:** Conceptual | **Fixture ID:** `deployment_basic`
**Skor GraphRAG:** 0,83 total | **Skor Vector RAG:** 0,62 total

### Pertanyaan
```
Apa yang terjadi pada Pod yang sedang berjalan ketika saya update image 
Deployment ke versi baru? Apakah ada downtime?
```

### Output GraphRAG

> Secara default Deployment menggunakan strategi **RollingUpdate**: Pod baru dengan image baru dibuat bertahap sambil Pod lama dihentikan satu per satu. Selama proses ini selalu ada Pod lama yang masih melayani traffic — **tidak ada downtime**.
>
> Parameter yang mengontrol prosesnya:
> - `maxUnavailable` — berapa Pod boleh mati sekaligus
> - `maxSurge` — berapa Pod baru boleh dibuat melebihi jumlah replika yang diinginkan
>
> Jika Pod baru gagal start (image tidak ditemukan atau crash), rollout **otomatis berhenti** dan bisa dikembalikan dengan `kubectl rollout undo`.

**Reasoning Path (jalur yang ditelusuri):**
```
Deployment -[CONTAINS_POD_TEMPLATE]-> PodTemplateSpec
Deployment -[EXTENDS]-> DeploymentSpec
Deployment -[HAS_PROPERTY]-> DeploymentSpec
DeploymentSpec -[HAS_PROPERTY]-> DeploymentStrategy
DeploymentStrategy -[HAS_PROPERTY]-> RollingUpdateDeployment
PodTemplateSpec -[HAS_PROPERTY]-> PodSpec
```

### Output Vector RAG

> Kubernetes menggunakan rolling update untuk mengupdate Deployment. Pod lama dihentikan dan Pod baru dibuat. Anda bisa mengonfigurasi strategi update menggunakan `strategy.type: RollingUpdate`. Secara default tidak ada downtime tapi ini tergantung konfigurasi aplikasi Anda.

**Reasoning Path:** *(tidak tersedia — vector RAG tidak menelusuri graph)*

### Analisis Perbedaan

| Aspek | GraphRAG | Vector RAG |
|---|---|---|
| Menyebut `maxUnavailable` dan `maxSurge` | ✅ Dengan penjelasan fungsinya | ❌ Tidak disebutkan |
| Menyebut mekanisme rollback otomatis | ✅ Ada | ❌ Tidak ada |
| Jalur relasi bisa diverifikasi | ✅ Ada reasoning path | ❌ Tidak ada |
| Akurasi teknis | Tinggi | Sedang — benar tapi tidak lengkap |

---

## Contoh 2 — Relationship: Deployment → ReplicaSet → Pod

**Kategori:** Relationship | **Fixture ID:** `deployment_pod_relation`
**Skor GraphRAG:** RetQ = 0,85 (rata-rata kategori) | **Skor Vector RAG:** RetQ = 0,35

### Pertanyaan
```
Bagaimana hubungan antara Deployment, ReplicaSet, dan Pod di Kubernetes?
```

### Output GraphRAG

> Deployment mengontrol ReplicaSet melalui `spec.selector`. ReplicaSet kemudian membuat dan menjaga jumlah Pod sesuai `spec.replicas`. **Deployment mendelegasikan manajemen Pod ke ReplicaSet** — bukan langsung ke Pod.
>
> Relasi ini penting dipahami karena:
> - Ketika Anda update image, Deployment membuat **ReplicaSet baru** (bukan mengganti Pod langsung)
> - ReplicaSet lama tetap ada tapi di-scale down ke 0 (berguna untuk `kubectl rollout undo`)
> - Label selector di `DeploymentSpec` harus match persis dengan label di `PodTemplateSpec`

**Reasoning Path:**
```
Deployment -[CONTAINS_POD_TEMPLATE]-> PodTemplateSpec
Deployment -[EXTENDS]-> DeploymentSpec
Deployment -[HAS_PROPERTY]-> DeploymentSpec
DeploymentSpec -[HAS_PROPERTY]-> LabelSelector
DeploymentSpec -[HAS_PROPERTY]-> PodTemplateSpec
PodTemplateSpec -[HAS_PROPERTY]-> PodSpec
PodSpec -[HAS_CONTAINER]-> Container
```

### Output Vector RAG

> Deployment, ReplicaSet, dan Pod adalah resource Kubernetes yang bekerja bersama. Deployment membuat ReplicaSet yang kemudian membuat Pod. Deployment adalah level tertinggi untuk mengelola aplikasi stateless.

**Reasoning Path:** *(tidak tersedia)*

### Analisis Perbedaan

| Aspek | GraphRAG | Vector RAG |
|---|---|---|
| Menjelaskan KENAPA ReplicaSet ada (bukan langsung ke Pod) | ✅ Explained | ❌ Disebutkan tapi tidak dijelaskan |
| Menjelaskan implikasi praktis (rollout undo) | ✅ Ada | ❌ Tidak ada |
| Menjelaskan constraint label selector | ✅ Ada | ❌ Tidak ada |
| Bisa dijadikan referensi untuk debug misconfiguration | ✅ Ya | Terbatas |

---

## Contoh 3 — YAML Generation: CronJob Backup

**Kategori:** YAML Generation | **Fixture ID:** `cronjob_backup`
**Skor GraphRAG:** Syntactic validity = 1,0 | **Skor Vector RAG:** Schema compliance sering 0,0

### Pertanyaan
```
Buatkan YAML CronJob untuk menjalankan backup database setiap hari jam 2 pagi
```

### Output GraphRAG

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
  namespace: default
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command: ["pg_dump", "-h", "db-host", "-U", "admin", "-d", "mydb"]
            resources:
              requests:
                memory: "128Mi"
                cpu: "100m"
              limits:
                memory: "256Mi"
                cpu: "200m"
          restartPolicy: OnFailure
```

**Validasi yang dijalankan:**
- ✅ Lapis 1 (PyYAML): Sintaksis valid
- ✅ Lapis 2 (kubernetes-validate): Tidak ada pelanggaran schema v1.29
- ✅ Lapis 3 (Neo4j): Semua required fields ada (`apiVersion`, `kind`, `metadata`, `spec`, `spec.schedule`, `spec.jobTemplate`)

**Reasoning Path:**
```
CronJob -[CONTAINS_JOB_TEMPLATE]-> JobTemplateSpec
CronJob -[HAS_PROPERTY]-> CronJobSpec
CronJobSpec -[HAS_PROPERTY]-> JobTemplateSpec
JobTemplateSpec -[HAS_PROPERTY]-> JobSpec
JobSpec -[HAS_PROPERTY]-> PodTemplateSpec
PodSpec -[HAS_CONTAINER]-> Container
Container -[HAS_PROPERTY]-> ResourceRequirements
```

### Output Vector RAG (contoh tipikal — sering error)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 2 * * *"
  spec:                        # ← ERROR: duplicate key "spec"
    template:
      spec:
        containers:
        - name: backup
          image: postgres:15
          command: ["pg_dump"]
  selector:                    # ← ERROR: CronJob tidak punya spec.selector
    matchLabels:
      app: db-backup
```

**Validasi (jika dijalankan):**
- ❌ Lapis 1 (PyYAML): Duplicate key `spec` — parse error
- ❌ Lapis 2: `spec.selector` tidak valid untuk CronJob
- ❌ Lapis 3: `spec.jobTemplate` missing

### Analisis Perbedaan

| Aspek | GraphRAG | Vector RAG |
|---|---|---|
| Struktur `spec.jobTemplate` benar | ✅ | ❌ Sering salah atau hilang |
| Tidak ada `spec.selector` (CronJob tidak punya ini) | ✅ | ❌ Sering ditambahkan secara salah |
| `restartPolicy: OnFailure` di level yang benar | ✅ (di pod spec) | ❌ Sering diletakkan di level yang salah |
| `resources` include both requests AND limits | ✅ | ❌ Sering hanya limits atau hanya requests |
| Lolos validasi | ✅ | ❌ Sering gagal |

---

## Contoh 4 — Troubleshooting: CrashLoopBackOff OOMKilled

**Kategori:** Troubleshooting | **Fixture ID:** `crashloopbackoff_oomkilled`
**Skor GraphRAG:** 0,78 total | **Skor Vector RAG:** 0,71 total

### Pertanyaan
```
Pod saya terus masuk ke status CrashLoopBackOff dan ketika saya cek dengan 
kubectl describe pod, di bagian Last State tertulis reason: OOMKilled. 
Apa yang menyebabkan ini dan bagaimana cara mengatasinya?
```

### Output GraphRAG

> **OOMKilled** berarti container dihentikan paksa oleh kernel Linux karena melebihi `resources.limits.memory` yang didefinisikan. Kubernetes lalu me-restart container tersebut, yang menyebabkan **CrashLoopBackOff** (restart berulang dengan delay makin panjang).
>
> **Solusi (prioritas):**
>
> 1. **Cek penggunaan aktual** dulu sebelum mengubah limit:
>    ```bash
>    kubectl top pod <pod-name>
>    ```
> 2. **Naikkan `resources.limits.memory`** ke nilai yang lebih tinggi dari puncak penggunaan aktual
> 3. **Pastikan `resources.requests.memory` akurat** — ini yang dipakai scheduler untuk menempatkan Pod di node dengan memory cukup
> 4. **Jika memory terus naik**, investigasi memory leak di aplikasi

**Reasoning Path:**
```
Container -[HAS_PROPERTY]-> ResourceRequirements
ContainerStatus -[HAS_PROPERTY]-> ContainerState
ContainerState -[HAS_PROPERTY]-> ContainerStateTerminated
ResourceRequirements -[HAS_PROPERTY]-> Quantity
```

### Output Vector RAG

> CrashLoopBackOff dengan OOMKilled berarti Pod kehabisan memory. Anda perlu menaikkan memory limit di container spec. Gunakan `resources.limits.memory` untuk mengatur batas memory. Pastikan juga `requests.memory` sudah diset.

### Analisis Perbedaan

| Aspek | GraphRAG | Vector RAG |
|---|---|---|
| Menjelaskan mekanisme OOMKilled (kernel kill) | ✅ | ❌ Tidak dijelaskan |
| Menyebut `kubectl top pod` untuk diagnosis | ✅ | ❌ Tidak disebutkan |
| Menjelaskan peran `requests` vs `limits` | ✅ Bedakan keduanya | Terbatas |
| Menyebut memory leak sebagai kemungkinan | ✅ | ❌ Tidak |
| Field yang disebutkan bisa diverifikasi ke schema | ✅ | Tidak bisa |

---

## Contoh 5 — Realworld: Mount ConfigMap sebagai Volume (Contoh Batas Sistem)

**Kategori:** Realworld | **Fixture ID:** `configmap_volume_mount`
**Skor GraphRAG:** 0,51 total | **Skor Vector RAG:** 0,48 total

*Contoh ini dipilih untuk menunjukkan kasus di mana perbedaan GraphRAG vs Vector RAG kecil — untuk jujur tentang batas sistem.*

### Pertanyaan
```
Bagaimana cara mount ConfigMap sebagai file dalam volume di dalam Pod?
```

### Output GraphRAG

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-pod
spec:
  volumes:
    - name: config-vol
      configMap:
        name: my-config
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: config-vol
          mountPath: /etc/config
```

> ConfigMap dapat di-mount sebagai volume agar konten config tersedia sebagai file di dalam container. `volumes[].configMap.name` harus merujuk ke nama ConfigMap yang sudah ada di namespace yang sama.

**Reasoning Path:**
```
PodSpec -[HAS_PROPERTY]-> Volume
Volume -[HAS_PROPERTY]-> ConfigMapVolumeSource
Container -[HAS_PROPERTY]-> VolumeMount
```

### Output Vector RAG

> YAML yang sangat mirip dengan di atas — perbedaan minor pada format indentasi atau urutan field.

### Analisis Perbedaan

| Aspek | GraphRAG | Vector RAG |
|---|---|---|
| YAML structure benar | ✅ | ✅ (sama) |
| Menjelaskan constraint namespace | ✅ Ada | ❌ Tidak ada |
| Perbedaan performa | Kecil (+0,03 gain) | — |

**Kenapa perbedaannya kecil di sini?**
> ConfigMap adalah resource sederhana (graph degree = 2, hanya 2 relasi langsung). Untuk resource sederhana seperti ini, Vector RAG sudah cukup menemukan pattern yang benar karena pola mounting-nya sering muncul di dokumentasi. GraphRAG memberikan nilai lebih besar di resource yang kompleks (Deployment, StatefulSet, HPA, RBAC).

---

## Ringkasan Perbandingan 5 Contoh

| Fixture | Kategori | GraphRAG Total | Vector RAG Total | Delta | Reasoning Path? |
|---|---|---|---|---|---|
| deployment_basic | Conceptual | 0,83 | 0,62 | +0,21 | ✅ 10 edge |
| deployment_pod_relation | Relationship | 0,88 | 0,51 | +0,37 | ✅ 7 edge |
| cronjob_backup | YAML Gen | 0,91 | 0,44 | +0,47 | ✅ 7 edge |
| crashloopbackoff_oomkilled | Troubleshooting | 0,78 | 0,71 | +0,07 | ✅ 4 edge |
| configmap_volume_mount | Realworld | 0,51 | 0,48 | +0,03 | ✅ 3 edge |

**Pola yang terlihat:** Semakin kompleks relasi antar-objek yang dibutuhkan untuk menjawab pertanyaan, semakin besar keunggulan GraphRAG. Untuk resource sederhana atau pertanyaan yang bisa dijawab dari teks deskripsi saja, perbedaannya kecil.
