from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class K8sField(BaseModel):
    """Represents a field within a K8s resource definition."""
    name: str
    data_type: str
    description: Optional[str] = None
    required: bool = False

class K8sResource(BaseModel):
    """Represents a Kubernetes Resource (e.g., Pod, Deployment)."""
    name: str
    api_version: str
    kind: str
    description: Optional[str] = None
    fields: List[K8sField] = []

class K8sEndpoint(BaseModel):
    """Represents an API Endpoint from Swagger."""
    path: str
    method: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    target_resource: Optional[str] = None  # Links to K8sResource