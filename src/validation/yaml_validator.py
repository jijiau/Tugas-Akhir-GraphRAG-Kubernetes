# src/validation/yaml_validator.py
import logging
import yaml
from src.graph.neo4j_client import Neo4jClient
from src.graph.queries import REQUIRED_FIELDS_QUERY

logger = logging.getLogger(__name__)


class YAMLValidator:
    """
    Three-layer YAML validation:
      1. PyYAML   — syntax correctness
      2. kubernetes-validate — schema compliance against K8s 1.29 spec
      3. Neo4j graph — required fields cross-check (thesis contribution)
    """

    def __init__(self):
        self.db = Neo4jClient()

    def validate(self, yaml_string: str, kind: str) -> dict:
        result = {
            "valid": True,
            "syntax_errors": [],
            "schema_errors": [],
            "missing_fields": [],
        }

        # ── Layer 1: PyYAML syntax ────────────────────────────────────────────
        try:
            data = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            result["valid"] = False
            result["syntax_errors"].append(str(e))
            return result  # no point checking further

        if not isinstance(data, dict):
            result["valid"] = False
            result["syntax_errors"].append("YAML root must be a mapping (dict), got: " + type(data).__name__)
            return result

        # ── Layer 2: kubernetes-validate schema ───────────────────────────────
        try:
            import kubernetes_validate
            kubernetes_validate.validate(data, "1.29", strict=False)
        except ImportError:
            logger.warning("kubernetes-validate not installed; skipping schema validation layer.")
        except Exception as e:
            result["valid"] = False
            # Extract path and message from the ValidationError if available
            path = "".join(str(p) for p in getattr(e, "path", []))
            msg  = getattr(e, "message", str(e))
            result["schema_errors"].append(f"{path}: {msg}" if path else msg)

        # ── Layer 3: Neo4j required fields ────────────────────────────────────
        try:
            rows = self.db.execute_query(REQUIRED_FIELDS_QUERY, {"kind": kind})
            required_fields = {r["field_name"] for r in rows}
        except Exception as e:
            logger.warning(f"Could not fetch required fields from graph: {e}")
            required_fields = set()

        if required_fields:
            yaml_keys = set(self._flatten_keys(data))
            missing = required_fields - yaml_keys
            if missing:
                result["valid"] = False
                result["missing_fields"] = sorted(missing)

        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _flatten_keys(self, obj, prefix: str = "") -> list[str]:
        """Recursively extract dotted key paths from a nested dict."""
        keys = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{prefix}.{k}" if prefix else k
                keys.append(full_key)
                keys.extend(self._flatten_keys(v, full_key))
        elif isinstance(obj, list):
            for item in obj:
                keys.extend(self._flatten_keys(item, prefix))
        return keys
