/**
 * CARA PAKAI:
 * 1. Buka https://script.google.com → klik "New project"
 * 2. Hapus kode default, paste seluruh isi file ini
 * 3. Klik tombol Run (▶) → pilih fungsi "createInterviewForm"
 * 4. Approve permission yang diminta (perlu akses Google Forms)
 * 5. Setelah selesai, buka tab "Execution log" (Ctrl+Enter) untuk lihat link form
 *
 * Form akan otomatis tersimpan di Google Drive (My Drive).
 */

function createInterviewForm() {

  // ─────────────────────────────────────────────────────────────────────────
  // SETUP FORM
  // ─────────────────────────────────────────────────────────────────────────

  var form = FormApp.create('Evaluasi Sistem GraphRAG Kubernetes — Wawancara Validasi');

  form.setDescription(
    'Terima kasih atas partisipasi Anda. Form ini diisi sambil melihat demonstrasi sistem ' +
    '— ikuti arahan pewawancara untuk setiap bagian.'
  );
  form.setProgressBar(true);
  form.setConfirmationMessage(
    'Terima kasih atas penilaian Anda! Masukan ini sangat berharga untuk penelitian ini.'
  );
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setLimitOneResponsePerUser(false);

  // ─────────────────────────────────────────────────────────────────────────
  // SECTION 0 — PROFIL NARASUMBER
  // ─────────────────────────────────────────────────────────────────────────

  form.addTextItem()
    .setTitle('Inisial nama Anda')
    .setRequired(true);

  form.addTextItem()
    .setTitle('Peran/jabatan saat ini')
    .setRequired(true);

  form.addDateItem()
    .setTitle('Tanggal wawancara')
    .setRequired(true);

  // ─────────────────────────────────────────────────────────────────────────
  // SECTION 1 — SKENARIO S1: GENERATE YAML STATEFULSET
  // ─────────────────────────────────────────────────────────────────────────

  form.addPageBreakItem()
    .setTitle('Skenario 1: Generate YAML StatefulSet + PVC')
    .setHelpText(
      'Pewawancara akan mendemonstrasikan sistem menjawab permintaan: ' +
      '"Buat YAML StatefulSet untuk database MySQL dengan PersistentVolumeClaim 10Gi". ' +
      'Perhatikan output YAML dan Retrieval Trace, lalu isi penilaian berikut.'
    );

  form.addScaleItem()
    .setTitle('Relevansi — Apakah jawaban sistem menjawab pertanyaan yang diajukan?')
    .setBounds(1, 5)
    .setLabels('Sama sekali tidak menjawab', 'Sangat relevan dan lengkap')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Akurasi Teknis — Apakah informasi Kubernetes dalam jawaban ini benar secara teknis?')
    .setBounds(1, 5)
    .setLabels('Banyak kesalahan teknis', 'Akurat sepenuhnya')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Kelengkapan — Apakah semua komponen penting untuk kebutuhan ini sudah tercakup?')
    .setBounds(1, 5)
    .setLabels('Banyak yang kurang', 'Sangat lengkap')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Kesediaan Pakai — Apakah output ini bisa langsung digunakan di pekerjaan tanpa modifikasi signifikan?')
    .setBounds(1, 5)
    .setLabels('Perlu banyak perbaikan', 'Bisa langsung dipakai')
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Komentar atau catatan untuk skenario ini (opsional)')
    .setRequired(false);

  // ─────────────────────────────────────────────────────────────────────────
  // SECTION 2 — SKENARIO S2: TROUBLESHOOTING OOMKILLED
  // ─────────────────────────────────────────────────────────────────────────

  form.addPageBreakItem()
    .setTitle('Skenario 2: Troubleshooting Pod OOMKilled')
    .setHelpText(
      'Pewawancara akan mendemonstrasikan sistem menjawab: ' +
      '"Pod saya terus masuk ke status CrashLoopBackOff dan di Last State tertulis reason: OOMKilled. ' +
      'Apa penyebabnya dan bagaimana mengatasinya?". ' +
      'Perhatikan jawaban sistem, lalu isi penilaian berikut.'
    );

  form.addScaleItem()
    .setTitle('Relevansi — Apakah jawaban sistem menjawab pertanyaan yang diajukan?')
    .setBounds(1, 5)
    .setLabels('Sama sekali tidak menjawab', 'Sangat relevan dan lengkap')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Akurasi Teknis — Apakah penyebab dan solusi yang disebutkan benar secara teknis?')
    .setBounds(1, 5)
    .setLabels('Banyak kesalahan teknis', 'Akurat sepenuhnya')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Kelengkapan — Apakah langkah troubleshooting yang diberikan cukup komprehensif?')
    .setBounds(1, 5)
    .setLabels('Banyak yang kurang', 'Sangat lengkap')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Kesediaan Pakai — Apakah jawaban ini bisa langsung Anda ikuti untuk troubleshoot masalah serupa?')
    .setBounds(1, 5)
    .setLabels('Perlu banyak perbaikan', 'Bisa langsung diikuti')
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Komentar atau catatan untuk skenario ini (opsional)')
    .setRequired(false);

  // ─────────────────────────────────────────────────────────────────────────
  // SECTION 3 — SKENARIO S3: RELASI DEPLOYMENT–REPLICASET–POD
  // ─────────────────────────────────────────────────────────────────────────

  form.addPageBreakItem()
    .setTitle('Skenario 3: Relasi Antar-Komponen Kubernetes')
    .setHelpText(
      'Pewawancara akan mendemonstrasikan sistem menjawab: ' +
      '"Bagaimana hubungan antara Deployment, ReplicaSet, dan Pod di Kubernetes?". ' +
      'Perhatikan jawaban dan fitur Retrieval Trace ' +
      '(grafik yang menunjukkan dari mana sistem mengambil informasi), lalu isi penilaian berikut.'
    );

  form.addScaleItem()
    .setTitle('Relevansi — Apakah jawaban sistem menjawab pertanyaan yang diajukan?')
    .setBounds(1, 5)
    .setLabels('Sama sekali tidak menjawab', 'Sangat relevan dan lengkap')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Akurasi Teknis — Apakah penjelasan hubungan antar-komponen ini benar secara teknis?')
    .setBounds(1, 5)
    .setLabels('Banyak kesalahan teknis', 'Akurat sepenuhnya')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Kelengkapan — Apakah penjelasan ini cukup untuk dipahami oleh rekan kerja yang baru mulai belajar Kubernetes?')
    .setBounds(1, 5)
    .setLabels('Sangat tidak lengkap', 'Sangat lengkap dan jelas')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Kesediaan Pakai — Apakah penjelasan ini bisa langsung Anda gunakan sebagai referensi?')
    .setBounds(1, 5)
    .setLabels('Tidak berguna', 'Bisa langsung dipakai sebagai referensi')
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Komentar atau catatan untuk skenario ini (opsional)')
    .setRequired(false);

  // ─────────────────────────────────────────────────────────────────────────
  // SECTION 4 — PENILAIAN FITUR RETRIEVAL TRACE
  // ─────────────────────────────────────────────────────────────────────────

  form.addPageBreakItem()
    .setTitle('Penilaian Fitur Retrieval Trace')
    .setHelpText(
      'Retrieval Trace adalah fitur yang menampilkan "dari mana sistem mengambil informasi" ' +
      '— berupa grafik node Kubernetes dan daftar relasi yang ditelusuri. ' +
      'Anda sudah melihat fitur ini saat demonstrasi tadi.'
    );

  form.addScaleItem()
    .setTitle('Seberapa mudah informasi di Retrieval Trace untuk dibaca dan dipahami?')
    .setBounds(1, 5)
    .setLabels('Sangat sulit dipahami', 'Sangat mudah dipahami')
    .setRequired(true);

  form.addScaleItem()
    .setTitle('Apakah fitur Retrieval Trace meningkatkan kepercayaan Anda terhadap jawaban sistem?')
    .setBounds(1, 5)
    .setLabels('Tidak berpengaruh sama sekali', 'Sangat meningkatkan kepercayaan')
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Seberapa sering Anda akan membuka Retrieval Trace jika menggunakan sistem ini sehari-hari?')
    .setChoiceValues([
      'Tidak pernah',
      'Hanya saat jawaban meragukan',
      'Kadang-kadang',
      'Selalu untuk setiap jawaban'
    ])
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Komentar tentang fitur Retrieval Trace (opsional)')
    .setRequired(false);

  // ─────────────────────────────────────────────────────────────────────────
  // SECTION 5 — PERTANYAAN REFLEKTIF
  // ─────────────────────────────────────────────────────────────────────────

  form.addPageBreakItem()
    .setTitle('Pertanyaan Reflektif')
    .setHelpText(
      'Tidak ada jawaban benar atau salah. ' +
      'Jawab berdasarkan pengalaman dan perspektif Anda sebagai praktisi.'
    );

  form.addParagraphTextItem()
    .setTitle(
      'Menurut Anda, apa kelebihan terbesar dari sistem ini dibandingkan ' +
      'cara Anda biasanya mencari informasi Kubernetes?'
    )
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Apa keterbatasan atau kelemahan paling signifikan yang Anda rasakan dari sistem ini?')
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle(
      'Untuk YAML yang digenerate sistem (seperti di Skenario 1): apakah menurut Anda ' +
      'output-nya production-ready, atau perlu modifikasi apa sebelum dipakai?'
    )
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Jenis pertanyaan Kubernetes apa yang menurut Anda masih kurang baik ditangani oleh sistem ini?')
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('Apakah Anda akan menggunakan sistem ini dalam pekerjaan sehari-hari? Mengapa atau mengapa tidak?')
    .setRequired(true);

  // ─────────────────────────────────────────────────────────────────────────
  // OUTPUT: PRINT LINKS KE EXECUTION LOG
  // ─────────────────────────────────────────────────────────────────────────

  var publishedUrl = form.getPublishedUrl();
  var editUrl      = form.getEditUrl();

  console.log('==================================================');
  console.log('FORM BERHASIL DIBUAT!');
  console.log('==================================================');
  console.log('Link untuk narasumber  : ' + publishedUrl);
  console.log('Link edit form (kamu)  : ' + editUrl);
  console.log('==================================================');
}
