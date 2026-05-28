# Demo Script: Sesi Live 5 Menit

**Tujuan demo:** Tunjukkan cara kerja sistem secara konkret sebelum masuk ke diskusi validasi.
**Format:** Live demo di Streamlit (atau screencast jika koneksi tidak stabil).
**Prinsip:** Tunjukkan 1 keberhasilan, 1 showcase fitur utama, dan 1 kegagalan — kejujuran intelektual membangun kepercayaan.

---

## Persiapan Sebelum Demo

- [ ] Neo4j sudah berjalan (verifikasi: buka Neo4j Browser, query `MATCH (n) RETURN count(n)` → harus return 725)
- [ ] Streamlit app sudah berjalan (`streamlit run main.py`)
- [ ] OpenAI API key aktif
- [ ] Browser tab sudah dibuka di `localhost:8501`
- [ ] Koneksi internet stabil (untuk API call)
- [ ] Backup: screencast video sudah direkam sebagai fallback

---

## Skenario 1 — Pertanyaan Konseptual (1,5 menit)

**Tujuan:** Tunjukkan bahwa sistem bisa menjawab pertanyaan teknis K8s dengan *reasoning path* yang bisa diverifikasi.

### Input yang diketik di chat:

```
Pod saya terus masuk ke status CrashLoopBackOff dan ketika saya cek 
dengan kubectl describe pod, di bagian Last State tertulis reason: OOMKilled. 
Apa yang menyebabkan ini dan bagaimana cara mengatasinya?
```

### Yang perlu ditunjukkan saat output muncul:

1. **Jawaban naratif** — sistem memberikan diagnosis dan solusi konkret (naikkan `resources.limits.memory`, cek memory leak, set `resources.requests.memory` yang akurat)
2. **Reasoning path** — tunjukkan jalur yang ditemukan:
   ```
   Pod → PodSpec → PodStatus → ContainerStatus → ContainerState → ContainerStateTerminated
   Container → ResourceRequirements
   ```
3. **Tunjukkan ke expert:** *"Jalur ini bisa diverifikasi — setiap langkah punya sumber resmi di schema K8s. Ini beda dengan ChatGPT yang tidak bisa menunjukkan dari mana jawabannya berasal."*

### Talking point:
> "Perhatikan bagian Reasoning Path di bawah jawaban. Sistem ini selalu menunjukkan *dari mana* informasinya berasal — field mana di schema Kubernetes yang mendukung setiap pernyataan. Ini fitur yang tidak dimiliki RAG berbasis teks biasa."

---

## Skenario 2 — Generate YAML dengan Multi-Entity (2,5 menit)

**Tujuan:** Showcase kemampuan utama sistem — generate YAML multi-resource yang valid dan terstruktur.

### Input yang diketik di chat:

```
Buatkan YAML Deployment untuk aplikasi web Node.js dengan:
- 3 replicas
- Resource limit: 256Mi memory, 250m CPU
- HPA yang scale antara 2-10 replicas berdasarkan CPU 70%
```

### Yang perlu ditunjukkan saat output muncul:

1. **Proses multi-entity retrieval** (sambil sistem loading, jelaskan):
   - Sistem mengenali 2 entity: Deployment + HPA
   - Traversal dijalankan terpisah untuk keduanya lalu digabung
   - Deployment path: `Deployment → DeploymentSpec → PodTemplateSpec → PodSpec → Container → ResourceRequirements`
   - HPA path: `HPA → HPASpec → CrossVersionObjectReference` (link ke Deployment sebagai target)

2. **YAML output** — tunjukkan bahwa:
   - `spec.selector.matchLabels` **identik** dengan `spec.template.metadata.labels` (sering salah di LLM biasa)
   - Resource limit berisi **both requests AND limits** (sering LLM hanya isi salah satu)
   - HPA `scaleTargetRef` mengarah ke Deployment yang benar
   - Format valid — tidak ada field yang tidak dikenal

3. **Validasi 3 lapis** — tunjukkan status validator:
   - ✅ Lapis 1: PyYAML parse sukses
   - ✅ Lapis 2: kubernetes-validate schema v1.29 — tidak ada pelanggaran
   - ✅ Lapis 3: Neo4j check required fields — semua field wajib terpenuhi

### Talking point:
> "Sistem ini tidak hanya generate YAML — ia memvalidasinya dari 3 sisi berbeda. Ini menghilangkan kelas error yang paling umum: YAML yang secara sintaksis valid tapi melanggar schema Kubernetes."

### Poin diskusi yang bisa ditanyakan langsung setelah ini:
> *"Menurut Anda, apakah output ini sudah cukup untuk Anda kirim ke staging tanpa review manual? Atau ada yang masih perlu diubah?"*

---

## Skenario 3 — Batas Sistem (1 menit)

**Tujuan:** Tunjukkan dengan jujur di mana sistem ini tidak bekerja dengan baik.

### Input yang diketik di chat:

```
Kenapa Pod saya stuck di status Pending terus-menerus padahal node 
masih punya resource? Saya sudah cek CPU dan memory tersedia.
```

*(Ini adalah pertanyaan realworld operasional yang melampaui kemampuan sistem)*

### Yang perlu ditunjukkan saat output muncul:

1. **Jawaban yang diberikan** — sistem memberikan jawaban generik (taint/toleration, node affinity, PVC pending)
2. **Bandingkan dengan ground truth** — jawaban benar seharusnya juga mencakup: anti-affinity conflicts, pending PVC, resource quota di namespace, atau scheduler backpressure — semua ini tidak ada di `swagger.json`
3. **Jelaskan kenapa:**
   > *"Knowledge graph saya hanya berisi struktur schema API Kubernetes — seperti spec dan field yang ada di swagger.json. Untuk pertanyaan 'kenapa Pod stuck', Anda butuh pengetahuan operasional: event log, scheduler behavior, bahkan cluster topology. Ini memang di luar scope data yang saya punya."*

### Talking point:
> "Ini bukan bug — ini adalah batasan yang saya pahami dan dokumentasikan. Sistem ini efektif untuk pertanyaan struktural dan generasi konfigurasi, tapi untuk diagnosis runtime yang kompleks, masih butuh sumber data tambahan seperti event log atau runbook operasional."

### Poin diskusi yang bisa ditanyakan langsung setelah ini:
> *"Menurut Anda, apakah gap ini bisa ditutup hanya dengan menambah relasi di graph, atau memang butuh sumber data yang berbeda sama sekali?"*

---

## Checklist Setelah Demo

Sebelum lanjut ke diskusi validasi, pastikan:

- [ ] Expert sudah mengerti *apa yang system lakukan* (retrieval dari graph, bukan internet atau training data)
- [ ] Expert sudah melihat contoh reasoning path
- [ ] Expert sudah melihat validasi YAML 3 lapis
- [ ] Expert sudah melihat satu kasus di mana sistem *tidak* bekerja baik
- [ ] Tanyakan: *"Ada pertanyaan soal cara kerja sistem sebelum kita masuk ke diskusi validasi?"*
