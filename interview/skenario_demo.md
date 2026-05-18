# Skenario Demo — Interview Validasi Sistem GraphRAG Kubernetes

> **Untuk**: Pewawancara (Jihan) — buka file ini di tab terpisah selama demo berlangsung
> **Sebelum mulai**: Neo4j aktif · `streamlit run main.py` jalan · test 1 pertanyaan dulu

---

## S1 — Generate YAML StatefulSet

| | |
|---|---|
| **Kategori** | `yaml_gen` |
| **Skor evaluasi** | 0.85 |
| **Hops traversal** | 46 |

### Pertanyaan (ketik ke sistem)

```
Buat YAML StatefulSet untuk database MySQL dengan PersistentVolumeClaim 10Gi
```

### Output yang diharapkan

YAML lengkap dengan struktur berikut:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8.0
          env:
            - name: MYSQL_ROOT_PASSWORD
              value: password
          volumeMounts:
            - name: mysql-data
              mountPath: /var/lib/mysql
  volumeClaimTemplates:
    - metadata:
        name: mysql-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: standard
        resources:
          requests:
            storage: 10Gi
```

### Yang disorot saat demo

1. **Tombol copy** di kanan atas code block — bisa langsung di-paste ke terminal
2. **Retrieval Trace → Tab Tabel Relasi** — lihat node: `StatefulSet`, `StatefulSetSpec`, `PersistentVolumeClaim`, `VolumeClaimTemplate`
3. **Tab Graph** — tunjukkan visualisasi node yang terhubung
4. **Jumlah hops (~46)** — sistem menelusuri skema lebih dalam dari definisi top-level

### Catatan pewawancara

- Beri waktu **30–45 detik** untuk narasumber baca YAML sebelum lanjut ke form
- Probing: *"Apakah ini sudah memenuhi struktur yang biasanya kamu pakai?"*

---

## S2 — Troubleshooting CrashLoopBackOff / OOMKilled

| | |
|---|---|
| **Kategori** | `troubleshooting` |
| **Skor evaluasi** | 0.61 *(sengaja dipilih — skor lebih rendah)* |
| **Hops traversal** | 32 |

### Pertanyaan (ketik ke sistem)

```
Pod saya terus masuk ke status CrashLoopBackOff dan ketika saya cek dengan kubectl describe pod,
di bagian Last State tertulis reason: OOMKilled. Apa yang menyebabkan ini dan bagaimana cara mengatasinya?
```

### Output yang diharapkan

Penjelasan narasi yang mencakup:

- **Penyebab OOMKilled** — container dihentikan kernel karena melewati `resources.limits.memory`
- **CrashLoopBackOff** — restart berulang dengan delay yang makin panjang (backoff)
- **Langkah solusi** — naikkan memory limit · cek `kubectl top pod` · cari memory leak · set `resources.requests.memory` yang akurat

### Yang disorot saat demo

1. **Struktur jawaban** — ada penyebab + solusi yang terpisah jelas?
2. **Retrieval Trace** — cari node `Container`, `ResourceRequirements`, `resources.limits` di daftar
3. **Catatan jujur ke narasumber**: *"Ini kategori yang performanya lebih rendah — menurut kamu apa yang kurang?"*

### Catatan pewawancara

- Skenario ini sengaja dipilih karena skor lebih rendah — tujuannya mendapat feedback kritis
- Probing: *"Apakah langkah troubleshooting ini sudah dalam urutan yang benar?"*
- Probing: *"Adakah konteks tambahan yang biasanya kamu berikan ke LLM supaya jawaban lebih spesifik?"*

---

## S3 — Relasi Deployment–ReplicaSet–Pod

| | |
|---|---|
| **Kategori** | `relationship` |
| **Skor evaluasi** | 0.82 |
| **Hops traversal** | 32 |

### Pertanyaan (ketik ke sistem)

```
Bagaimana hubungan antara Deployment, ReplicaSet, dan Pod di Kubernetes?
```

### Output yang diharapkan

Penjelasan chain:

- **Deployment** mengontrol ReplicaSet via `spec.selector`
- **ReplicaSet** menjaga jumlah Pod sesuai `spec.replicas`
- **Deployment** mendelegasikan manajemen Pod ke ReplicaSet

Mungkin disertai contoh YAML atau diagram tekstual.

### Yang disorot saat demo

1. **Retrieval Trace → Tab Graph** — ini skenario terbaik untuk visualisasi karena chain 3 komponen terlihat jelas
2. **Tab Tabel Relasi** — tunjukkan edge: `CONTAINS_POD_TEMPLATE`, `SCALES_RESOURCE`
3. **Bandingkan dengan S1/S2** — pada relasional, reasoning path lebih panjang dan eksplisit

### Catatan pewawancara

- **Minta narasumber buka Retrieval Trace sendiri**: *"Coba kamu buka tab Retrieval Trace dan lihat Graph-nya"*
- Ini bagian terpenting untuk menilai apakah fitur Retrieval Trace berguna
- Probing: *"Apakah penjelasan ini sudah cukup untuk dijadikan referensi ketika debugging masalah Deployment?"*

---

## Pertanyaan Suggested — Eksplorasi Mandiri

Gunakan jika narasumber blank saat diminta ketik pertanyaan sendiri.

**Troubleshooting**
> "Pod saya stuck di Pending sudah 10 menit, resource di cluster masih ada. Apa yang perlu dicek?"

> "Deployment saya punya 3 replika tapi HPA tidak mau scale up padahal CPU sudah 80%. Kenapa?"

**Generate YAML**
> "Buatkan YAML CronJob untuk backup database setiap hari jam 2 pagi"

> "Buatkan YAML NetworkPolicy yang block semua traffic masuk ke namespace production kecuali dari namespace monitoring"

**Relasi / Konsep**
> "Bagaimana ServiceAccount digunakan Pod untuk akses Kubernetes API?"

> "Apa bedanya resources.requests dan resources.limits untuk CPU dan memory?"

**Planning**
> "Saya mau deploy web app Node.js + PostgreSQL. Resource Kubernetes apa saja yang perlu dibuat?"

---

## Checklist Teknis Sebelum Demo

- [ ] `streamlit run main.py` → buka `http://localhost:8501`
- [ ] Test query: ketik `"apa itu Pod?"` → pastikan ada jawaban + Retrieval Trace muncul
- [ ] Neo4j browser (`http://localhost:7474`) → verifikasi koneksi
- [ ] Groq API key aktif (cek `.env`)
