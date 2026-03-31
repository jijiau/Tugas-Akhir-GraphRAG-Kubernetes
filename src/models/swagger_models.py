# src/models/swagger_models.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class PropertyEdge(BaseModel):
    """Represents a :HAS_PROPERTY relationship for YAML construction."""
    target_id: str = Field(..., description="The ID of the target SubResource")
    field_name: str = Field(..., description="The exact YAML key name")
    is_array: bool = False
    is_map: bool = False
    is_required: bool = False

class SemanticEdge(BaseModel):
    """Represents shortcut relationships like :CONTAINS_POD_TEMPLATE."""
    target_id: str
    relation_type: str = Field(..., description="e.g., CONTAINS_POD_TEMPLATE, SCALES_RESOURCE")

class K8sNode(BaseModel):
    """Core hierarchical node representing any K8s definition."""
    model_config = ConfigDict(strict=True) # Enforce strict typing

    id: str = Field(..., description="Full OpenAPI schema ID, e.g., io.k8s.api.apps.v1.Deployment")
    name: str = Field(..., description="Short name, e.g., Deployment")
    kind: str
    is_root: bool = Field(default=False, description="True if it can be deployed directly")
    scope: str = Field(default="Namespaced")
    description: str
    
    properties: List[PropertyEdge] = Field(default_factory=list)
    semantics: List[SemanticEdge] = Field(default_factory=list)