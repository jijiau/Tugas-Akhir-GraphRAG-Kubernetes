# Perubahan yang Diterapkan — Sesi Ini

> Tanggal: 2026-05-18  
> Konteks: Perbaikan evaluasi akhir thesis — Speaker LLM switch, semantic graph validation, followup fixture fix, dan re-evaluasi tiga-arah.

---

## 1. Speaker LLM Switch: Groq → GPT-4o-mini

### File yang Diubah

**`src/chatbot/llm_factory.py`**
- Mengganti `get_speaker_llm()` dari `ChatGroq` → `ChatOpenAI`
- Menghapus import `from langchain_groq import ChatGroq` (tidak lagi dipakai)

```python
# SEBELUM
from langchain_groq import ChatGroq
def get_speaker_llm():
    return ChatGroq(
        model=settings.speaker_model,
        temperature=0.1,
        api_key=settings.groq_api_key,
        max_retries=2,
        timeout=30,
    )

# SESUDAH
def get_speaker_llm():
    return ChatOpenAI(
        model=settings.speaker_model,
        temperature=0.1,
        api_key=settings.openai_api_key,
        max_retries=2,
        timeout=30,
    )
```

**`src/config/settings.py`**
- `speaker_model` default: `"gpt-4o-mini"` (sebelumnya `"llama-3.1-8b-instant"`)
- `groq_api_key`: berubah dari `str` wajib → `Optional[str] = None`
- Menghapus `import os` (tidak dipakai)

---

## 2. Semantic Coherence Checks di Auditor

### File yang Diubah

**`src/validation/auditor.py`**

Menambahkan dua metode baru:

```python
def check_workload_completeness(self) -> list:
    """Semua Workload HARUS punya CONTAINS_POD_TEMPLATE."""
    query = """
        MATCH (r:Definition)
        WHERE r.kind IN ['Deployment','ReplicaSet','DaemonSet','StatefulSet','Job']
        AND NOT (r)-[:CONTAINS_POD_TEMPLATE]->()
        RETURN r.kind as kind
    """
    results = self.db.execute_query(query)
    missing = [r["kind"] for r in results if r]
    return missing

def check_scales_resource_coherence(self) -> list:
    """SCALES_RESOURCE hanya boleh menuju Workload."""
    query = """
        MATCH (h)-[:SCALES_RESOURCE]->(t)
        WHERE NOT t.kind IN ['Deployment','StatefulSet','ReplicaSet']
        RETURN t.kind as invalid_target
    """
    results = self.db.execute_query(query)
    violations = [r["invalid_target"] for r in results if r]
    return violations
```

Menambahkan keduanya ke `run_full_audit()` dan penalti di `calculate_health_score()`:
```python
# Di run_full_audit():
results["workload_completeness_missing"] = self.check_workload_completeness()
results["scales_coherence_violations"] = self.check_scales_resource_coherence()

# Di calculate_health_score():
workload_missing = self.check_workload_completeness()
score -= min(len(workload_missing) * 5, 20)
coherence_violations = self.check_scales_resource_coherence()
score -= min(len(coherence_violations) * 5, 10)
```

Menghapus `List` dari `typing` import (tidak terpakai setelah return type menggunakan `list` builtin).

**`scripts/validate_graph.py`**
- Menambahkan blok tampilan hasil "SEMANTIC COHERENCE CHECKS" baru di output konsol.

---

## 3. Perbaikan Followup Fixtures: Penambahan `context_question`

### Masalah Sebelumnya
12 fixture followup memiliki pertanyaan deictic ("itu", "tadi", "ini") tanpa konteks percakapan sebelumnya — dievaluasi dalam sesi kosong sehingga GraphRAG tidak bisa memanfaatkan session memory.

### Solusi
Menambahkan field `context_question` ke semua 12 file fixture followup di `tests/fixtures/followup/*.json`.

| Fixture | `context_question` yang Ditambahkan |
|---------|--------------------------------------|
| `add_env_from_configmap.json` | `"Buat YAML Deployment nginx"` |
| `add_env_from_secret.json` | `"Buat YAML Deployment nginx"` |
| `add_hpa_to_deployment.json` | `"Buat YAML Deployment nginx dengan 3 replika"` |
| `add_liveness_probe.json` | `"Buat YAML Deployment nginx"` |
| `add_pvc_to_statefulset.json` | `"Buat YAML StatefulSet MySQL"` |
| `add_readiness_probe.json` | `"Buat YAML Deployment nginx"` |
| `add_resource_limits.json` | `"Buat YAML Deployment nginx dengan satu container"` |
| `add_resource_limits_deployment.json` | `"Buat YAML Deployment nginx"` |
| `change_service_type.json` | `"Buat YAML Service ClusterIP untuk nginx di port 80"` |
| `expose_with_ingress.json` | `"Buat YAML Service ClusterIP untuk nginx di port 80"` |
| `scale_existing_deployment.json` | `"Buat YAML Deployment nginx dengan 3 replika"` |
| `update_image_version.json` | `"Buat YAML Deployment nginx:1.24 dengan 2 replika"` |

### File yang Diubah

**`scripts/evaluate.py`**
- Setiap fixture kini menggunakan `_session_id` yang konsisten (bukan inline string)
- Sebelum evaluate fixture utama, jika `context_question` ada: jalankan `invoke_mode(context_question, _session_id)` terlebih dahulu dengan session yang sama, lalu `time.sleep(1)`

```python
_session_id = f"eval_{_run_id}_{data['id']}"
context_question = data.get("context_question")
if context_question:
    logger.info(f"    [context] pre-running: {context_question[:80]}...")
    try:
        invoke_mode(context_question, _session_id)
        time.sleep(1)
    except Exception as _ctx_err:
        logger.warning(f"    [context] pre-run failed (non-fatal): {_ctx_err}")
answer, reasoning_path, graph_context = invoke_mode(question, _session_id)
```

**Catatan**: Hanya GraphRAG yang memanfaatkan context_question (pakai SQLite session memory). VectorRAG dan VanillaLLM bersifat stateless — context_question dijalankan tetapi tidak berpengaruh.

---

## 4. Re-Evaluasi Tiga-Arah (Hasil Final)

Output file:
- GraphRAG: `data/eval_results_v12.csv`
- VectorRAG: `data/eval_results_vector_v2.csv`
- VanillaLLM: `data/eval_results_llm_v2.csv`

### Hasil Global

| Metrik | GraphRAG (v12) | VectorRAG (v2) | VanillaLLM (v2) |
|--------|---------------|----------------|-----------------|
| **Total** | **0.6943** | 0.6111 | 0.4015 |
| AnsQ | 0.5743 | **0.5979** | 0.5880 |
| RetQ | **0.6851** | 0.4249 | 0.0241 |
| ReaQ | **0.8994** | 0.8930 | 0.6313 |
| Hallucination | **0.2322** | 0.3609 | 0.4025 |
| Grounding | **0.7678** | 0.6391 | 0.5975 |

### Sub-Metrik AnsQ

| Sub-Metrik | GraphRAG | VectorRAG | VanillaLLM |
|------------|----------|-----------|------------|
| Syntactic Validity | 0.9474 | 0.8947 | 0.7895 |
| Schema Compliance | 0.7895 | **0.8421** | 0.7368 |
| Answer Relevance | **0.6682** | 0.6423 | 0.6261 |
| Faithfulness | 0.4289 | **0.5040** | 0.5185 |

### Sub-Metrik RetQ

| Sub-Metrik | GraphRAG | VectorRAG | VanillaLLM |
|------------|----------|-----------|------------|
| Precision@k | **0.6705** | 0.3606 | 0.0000 |
| Recall@k | **0.5907** | 0.3431 | 0.0000 |
| F1@k | **0.5658** | 0.2910 | 0.0000 |
| Graph Coverage | **0.8599** | 0.5411 | 0.0722 |
| NDCG@k | **0.7503** | 0.4443 | 0.0000 |
| Edge Coverage | **0.6731** | 0.5693 | 0.0722 |

### Sub-Metrik ReaQ

| Sub-Metrik | GraphRAG | VectorRAG | VanillaLLM |
|------------|----------|-----------|------------|
| Hop Accuracy | 0.8969 | **1.0000** | 0.0000 |
| Multi-Hop Success | 1.0000 | 1.0000 | 1.0000 |
| Scope Accuracy | 0.9330 | 0.9330 | 0.9278 |
| Hallucination Rate | **0.2322** | 0.3609 | 0.4025 |
| Grounding Score | **0.7678** | 0.6391 | 0.5975 |

### Per Kategori (GraphRAG v12)

| Kategori | n | AnsQ | RetQ | ReaQ | Total | Hallucination |
|----------|---|------|------|------|-------|---------------|
| yaml_gen | 15 | 0.81 | 0.89 | 0.87 | **0.85** | 0.40 |
| followup | 12 | 0.53 | **0.92** | 0.91 | **0.76** | 0.36 |
| relationship | 18 | 0.69 | 0.73 | **0.98** | 0.77 | **0.04** |
| conceptual | 15 | 0.64 | 0.73 | 0.93 | 0.74 | 0.13 |
| planning | 5 | 0.45 | 0.80 | 0.90 | 0.69 | 0.39 |
| troubleshooting | 5 | 0.41 | 0.67 | 0.89 | 0.62 | 0.45 |
| command | 3 | 0.33 | 0.75 | 0.87 | 0.61 | 0.37 |
| realworld | 24 | 0.41 | 0.35 | 0.84 | 0.50 | 0.17 |

---

## 5. Catatan Teknis

- **UnicodeEncodeError Windows**: Jalankan script dengan `python -X utf8` jika ada emoji di output.
- **Fresh evaluation**: Gunakan output file baru (bukan `--resume`) agar tidak melanjutkan hasil lama.
- **Evaluate.py resume behavior**: Script otomatis skip fixture yang sudah ada di CSV — pastikan gunakan nama file baru untuk fresh run.
