// Validasi required-field — dipakai oleh YAMLValidator (Layer 3:
// verifikasi required fields terhadap knowledge graph).
// Parameter: $kind (str)
MATCH (d:Definition {name: $kind})-[r:HAS_PROPERTY {is_required: true}]->(p)
RETURN p.name AS field_name
