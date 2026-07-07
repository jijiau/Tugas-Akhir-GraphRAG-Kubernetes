// Exact name match — cari root node berdasarkan nama persis.
// Digunakan sebelum vector search untuk memastikan precision.
// Parameter: $primary_resource (str)
MATCH (d:Definition)
WHERE d.name = $primary_resource
   OR d.name ENDS WITH ('.' + $primary_resource)
RETURN d.name AS name, d.kind AS kind, d.description AS description
ORDER BY
  CASE WHEN d.name = $primary_resource THEN 0 ELSE 1 END
LIMIT 1
