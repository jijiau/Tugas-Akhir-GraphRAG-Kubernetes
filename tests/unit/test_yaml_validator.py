# tests/unit/test_yaml_validator.py
import pytest
from unittest.mock import patch, MagicMock
from src.validation.yaml_validator import YAMLValidator

pytestmark = pytest.mark.unit


@pytest.fixture
def validator():
    with patch("src.validation.yaml_validator.Neo4jClient") as mock_db_cls:
        mock_db = MagicMock()
        mock_db.execute_query.return_value = []
        mock_db_cls.return_value = mock_db
        yield YAMLValidator()


def test_valid_yaml_syntax(validator):
    yaml_str = "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: test\nspec:\n  replicas: 1"
    result = validator.validate(yaml_str, "Deployment")
    assert result["syntax_errors"] == []


def test_invalid_yaml_syntax(validator):
    yaml_str = "apiVersion: apps/v1\n  invalid: [unclosed"
    result = validator.validate(yaml_str, "Deployment")
    assert result["valid"] is False
    assert len(result["syntax_errors"]) > 0


def test_non_dict_yaml(validator):
    yaml_str = "- item1\n- item2"
    result = validator.validate(yaml_str, "Deployment")
    assert result["valid"] is False
    assert any("mapping" in e for e in result["syntax_errors"])


def test_missing_required_fields(validator):
    with patch.object(validator, "db") as mock_db:
        mock_db.execute_query.return_value = [{"field_name": "spec"}, {"field_name": "metadata"}]
        yaml_str = "apiVersion: apps/v1\nkind: Deployment"
        result = validator.validate(yaml_str, "Deployment")
    assert result["valid"] is False
    assert "spec" in result["missing_fields"] or "metadata" in result["missing_fields"]


def test_all_required_fields_present(validator):
    with patch.object(validator, "db") as mock_db:
        mock_db.execute_query.return_value = [{"field_name": "metadata"}]
        yaml_str = "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: test"
        result = validator.validate(yaml_str, "Deployment")
    assert "metadata" not in result["missing_fields"]


def test_flatten_keys_nested():
    with patch("src.validation.yaml_validator.Neo4jClient"):
        v = YAMLValidator()
    data = {"spec": {"replicas": 3, "template": {"metadata": {}}}}
    keys = v._flatten_keys(data)
    assert "spec" in keys
    assert "spec.replicas" in keys
    assert "spec.template" in keys
    assert "spec.template.metadata" in keys
