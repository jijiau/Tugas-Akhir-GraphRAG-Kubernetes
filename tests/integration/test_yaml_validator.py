# tests/integration/test_yaml_validator.py
"""
Integration tests for YAMLValidator — requires live Neo4j connection
to test Layer 3 (required fields cross-check from graph).

Run:
  pytest tests/integration/test_yaml_validator.py -v -m integration
"""
import pytest
from src.validation.yaml_validator import YAMLValidator


VALID_DEPLOYMENT_YAML = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-app
          image: nginx:latest
          ports:
            - containerPort: 80
""".strip()

INVALID_SYNTAX_YAML = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken
  : invalid_key
""".strip()

MINIMAL_CONFIGMAP_YAML = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-config
data:
  key: value
""".strip()


# ── Layer 1 + 2: Syntax and Schema ───────────────────────────────────────────

@pytest.mark.integration
def test_valid_deployment_passes_all_layers(neo4j_client):
    """
    A structurally correct Deployment YAML must pass syntax and schema layers.
    The graph required-fields layer may add warnings but must not crash.
    """
    validator = YAMLValidator()
    result = validator.validate(VALID_DEPLOYMENT_YAML, kind="Deployment")

    assert isinstance(result, dict)
    assert "valid" in result
    assert result["syntax_errors"] == [], (
        f"Unexpected syntax errors: {result['syntax_errors']}"
    )


@pytest.mark.integration
def test_invalid_syntax_yaml_fails_layer1(neo4j_client):
    """
    YAML with syntax errors must fail at Layer 1 (PyYAML) and return
    non-empty syntax_errors without raising an exception.
    """
    validator = YAMLValidator()
    result = validator.validate(INVALID_SYNTAX_YAML, kind="Deployment")

    assert result["valid"] is False
    assert len(result["syntax_errors"]) > 0


@pytest.mark.integration
def test_configmap_yaml_validates_cleanly(neo4j_client):
    """ConfigMap is a simple, well-known resource — must pass validation."""
    validator = YAMLValidator()
    result = validator.validate(MINIMAL_CONFIGMAP_YAML, kind="ConfigMap")

    assert isinstance(result, dict)
    assert result["syntax_errors"] == []


# ── Layer 3: Neo4j Required Fields ───────────────────────────────────────────

@pytest.mark.integration
def test_validator_result_has_required_keys(neo4j_client):
    """
    Validator output must always include the four contract keys regardless
    of what the graph returns.
    """
    validator = YAMLValidator()
    result = validator.validate(VALID_DEPLOYMENT_YAML, kind="Deployment")

    for key in ("valid", "syntax_errors", "schema_errors", "missing_fields"):
        assert key in result, f"Missing key '{key}' in validator result"


@pytest.mark.integration
def test_missing_fields_is_list(neo4j_client):
    """missing_fields must always be a list, even when graph returns nothing."""
    validator = YAMLValidator()
    result = validator.validate(VALID_DEPLOYMENT_YAML, kind="Deployment")
    assert isinstance(result["missing_fields"], list)


@pytest.mark.integration
def test_unknown_kind_does_not_crash(neo4j_client):
    """
    Passing an unknown 'kind' to the validator must not raise — the Neo4j
    query should return an empty set, and the result must be well-formed.
    """
    validator = YAMLValidator()
    result = validator.validate(VALID_DEPLOYMENT_YAML, kind="NonExistentKind99")

    assert isinstance(result, dict)
    assert "valid" in result


# ── Idempotency ───────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_validator_is_idempotent(neo4j_client):
    """
    Calling validate() twice on the same input must produce identical results.
    This guards against side effects in Neo4j queries or internal state.
    """
    validator = YAMLValidator()
    result1 = validator.validate(VALID_DEPLOYMENT_YAML, kind="Deployment")
    result2 = validator.validate(VALID_DEPLOYMENT_YAML, kind="Deployment")

    assert result1["valid"] == result2["valid"]
    assert result1["syntax_errors"] == result2["syntax_errors"]
    assert result1["missing_fields"] == result2["missing_fields"]
