# Fixture Fix Log — Fase 2 (dry-run)

> Otomatis dari `recurate_fixtures.py`. relevant_nodes/expected_path = neighborhood (coverage); key_nodes = answer-bearing. Validasi per kategori dgn Rubrik.


## command (3)

| fixture | rel old→new | key old→new | edges old→new | depth | n_roots | flags |
|---|---|---|---|---|---|---|
| kubectl_export_namespace_resources | 7→4 | 7→4 | 3→3 | 3 | 1 | ok |
| kubectl_find_pods_with_env | 86→38 | 86→6 | 111→42 | 3 | 1 | ok |
| kubectl_force_delete_pod | 86→86 | 86→4 | 111→111 | 3 | 1 | ok |

## conceptual (15)

| fixture | rel old→new | key old→new | edges old→new | depth | n_roots | flags |
|---|---|---|---|---|---|---|
| configmap_usage | 4→4 | 3→4 | 2→0 | 2 | 1 | ok |
| daemonset_purpose | 8→9 | 3→2 | 8→8 | 2 | 1 | ok |
| deployment_basic | 9→9 | 2→4 | 10→9 | 2 | 1 | ok |
| hpa_target | 23→19 | 3→5 | 21→21 | 2 | 1 | ok |
| ingress_purpose | 14→13 | 4→6 | 14→10 | 2 | 1 | ok |
| job_cronjob | 12→11 | 5→2 | 10→10 | 2 | 1 | ok |
| namespace_quota | 5→7 | 2→5 | 5→5 | 2 | 1 | ok |
| persistent_volume_concept | 14→14 | 5→5 | 12→11 | 2 | 1 | ok |
| pod_spec | 73→73 | 2→1 | 93→93 | 2 | 1 | ok |
| required_fields_container | 30→29 | 2→1 | 30→30 | 2 | 1 | ok |
| scope_accuracy_node | 16→17 | 3→3 | 14→14 | 2 | 1 | ok |
| secret_types | 3→2 | 3→2 | 0→0 | 2 | 1 | ok |
| service_types | 13→12 | 2→4 | 12→10 | 2 | 1 | ok |
| statefulset_storage | 14→15 | 2→3 | 15→15 | 2 | 1 | ok |
| storageclass_concept | 5→4 | 2→2 | 2→2 | 2 | 1 | ok |

## followup (12)

| fixture | rel old→new | key old→new | edges old→new | depth | n_roots | flags |
|---|---|---|---|---|---|---|
| add_env_from_configmap | 12→11 | 12→4 | 12→9 | 2 | 1 | ok |
| add_env_from_secret | 10→8 | 3→1 | 9→9 | 2 | 1 | ok |
| add_hpa_to_deployment | 24→19 | 24→5 | 22→21 | 2 | 1 | ok |
| add_liveness_probe | 11→11 | 11→4 | 11→9 | 2 | 1 | ok |
| add_pvc_to_statefulset | 14→14 | 3→1 | 15→15 | 2 | 1 | ok |
| add_readiness_probe | 10→8 | 3→1 | 9→9 | 2 | 1 | ok |
| add_resource_limits | 10→8 | 3→1 | 9→9 | 2 | 1 | ok |
| add_resource_limits_deployment | 10→10 | 10→3 | 10→9 | 2 | 1 | ok |
| change_service_type | 10→10 | 2→1 | 10→10 | 2 | 1 | ok |
| expose_with_ingress | 11→11 | 3→1 | 10→10 | 2 | 1 | ok |
| scale_existing_deployment | 8→8 | 2→1 | 9→9 | 2 | 1 | ok |
| update_image_version | 9→9 | 9→3 | 9→9 | 2 | 1 | ok |

## planning (5)

| fixture | rel old→new | key old→new | edges old→new | depth | n_roots | flags |
|---|---|---|---|---|---|---|
| plan_autoscale_ha | 33→32 | 33→5 | 34→32 | 3 | 1 | ok |
| plan_cronjob_batch | 13→14 | 13→6 | 11→10 | 3 | 1 | ok |
| plan_namespace_isolation | 11→12 | 11→5 | 11→9 | 3 | 1 | ok |
| plan_redis_persistent | 44→45 | 44→7 | 47→46 | 3 | 1 | ok |
| plan_webapp_with_db | 34→36 | 34→9 | 35→32 | 3 | 1 | ok |

## realworld (24)

| fixture | rel old→new | key old→new | edges old→new | depth | n_roots | flags |
|---|---|---|---|---|---|---|
| configmap_volume_mount | 4→3 | 4→3 | 3→0 | 3 | 1 | ok |
| deployment_vs_statefulset_comparison | 31→31 | 4→3 | 34→32 | 3 | 1 | ok |
| hpa_custom_metrics_yaml | 46→42 | 4→4 | 50→50 | 3 | 1 | ok |
| pbased_on_a_hrefhttpsstackoverflowcomquestions599 | 86→86 | 1→1 | 111→111 | 3 | 1 | LOW_CONF(ctx kosong) |
| pcopied_from_here_a_hrefhttpsgithubcomkubeflowpi | 4→4 | 1→1 | 3→3 | 3 | 1 | LOW_CONF(ctx kosong) |
| pheres_a_simplified_version_of_a | 32→32 | 1→1 | 34→34 | 3 | 1 | LOW_CONF(ctx kosong) |
| pi_am_quite_new_to_tektonp | 86→86 | 1→1 | 111→111 | 3 | 1 | LOW_CONF(ctx kosong) |
| pi_am_wondering_if_it_is | 1→1 | 1→1 | 0→0 | 3 | 1 | LOW_CONF(ctx kosong) |
| pi_cant_find_documentation_on_how | 4→4 | 1→1 | 3→3 | 3 | 1 | LOW_CONF(ctx kosong) |
| pi_have_a_command_to_run | 86→86 | 1→1 | 111→111 | 3 | 1 | LOW_CONF(ctx kosong) |
| pi_have_a_google_kubernetes_cluster | 19→20 | 1→2 | 19→19 | 3 | 1 | LOW_CONF(ctx kosong) |
| pi_have_a_tekton_codepipelinecode_and | 14→14 | 1→1 | 14→14 | 3 | 1 | LOW_CONF(ctx kosong) |
| pi_want_to_pass_a_certificate | 1→1 | 1→1 | 0→0 | 3 | 1 | LOW_CONF(ctx kosong) |
| pi_want_to_reject_all_docker | 4→4 | 1→1 | 3→3 | 3 | 1 | LOW_CONF(ctx kosong) |
| pid_like_to_confirm_information_of | 2→2 | 1→1 | 1→1 | 3 | 1 | LOW_CONF(ctx kosong) |
| pim_trying_to_use_a_container | 32→33 | 1→2 | 34→34 | 3 | 1 | LOW_CONF(ctx kosong) |
| pim_using_argocd_and_i_want | 4→4 | 1→1 | 3→3 | 3 | 1 | LOW_CONF(ctx kosong) |
| pkubectl_provides_a_nice_way_to | 1→1 | 1→1 | 0→0 | 3 | 1 | LOW_CONF(ctx kosong) |
| precodespec_containers_image_nginx_imagepul | 86→86 | 1→1 | 111→111 | 3 | 1 | LOW_CONF(ctx kosong) |
| pthis_eks_cluster_has_a_private | 2→2 | 1→1 | 1→1 | 3 | 1 | LOW_CONF(ctx kosong) |
| pusing_kubernetes_v1157_in_minikube_and | 1→1 | 1→1 | 0→0 | 3 | 1 | LOW_CONF(ctx kosong) |
| pwhen_using_istio_with_kubernetes_a | 1→1 | 1→1 | 0→0 | 3 | 1 | LOW_CONF(ctx kosong) |
| pwith_kubectl_i_know_i_can | 4→4 | 1→1 | 3→3 | 3 | 1 | LOW_CONF(ctx kosong) |
| serviceaccount_pod_binding | 6→6 | 4→4 | 5→2 | 3 | 1 | ok |

## relationship (18)

| fixture | rel old→new | key old→new | edges old→new | depth | n_roots | flags |
|---|---|---|---|---|---|---|
| anyof_intorstring | 3→2 | 3→2 | 1→0 | 3 | 1 | ok |
| cronjob_job_pod | 10→10 | 4→1 | 10→10 | 3 | 1 | ok |
| deep_deployment_container_resources | 29→29 | 5→5 | 33→32 | 3 | 1 | ok |
| deep_statefulset_container_probe | 42→42 | 5→5 | 47→46 | 3 | 1 | ok |
| deployment_pod_relation | 29→30 | 3→2 | 32→32 | 3 | 1 | ok |
| extends_hpa_metric | 46→42 | 3→3 | 50→50 | 3 | 1 | ok |
| hpa_deployment_pod | 46→42 | 4→7 | 50→50 | 3 | 1 | ok |
| ingress_service_pod | 22→22 | 4→6 | 23→21 | 3 | 1 | ok |
| namespace_quota_relation | 6→6 | 3→3 | 5→3 | 3 | 1 | ok |
| networkpolicy_pod_selector | 8→9 | 3→2 | 9→9 | 3 | 1 | ok |
| oneof_volume_source | 46→46 | 5→6 | 59→58 | 3 | 1 | ok |
| pod_namespace_relation | 87→87 | 2→2 | 111→111 | 3 | 1 | ok |
| pvc_storageclass | 14→15 | 3→4 | 14→14 | 3 | 1 | ok |
| rbac_binding | 8→9 | 3→4 | 7→7 | 3 | 1 | ok |
| secret_usage | 5→2 | 5→2 | 4→0 | 3 | 1 | ok |
| service_selector | 38→39 | 2→3 | 42→42 | 3 | 1 | ok |
| serviceaccount_token_binding | 5→6 | 3→4 | 4→2 | 3 | 1 | ok |
| statefulset_pvc_pv | 41→42 | 3→2 | 46→46 | 3 | 1 | ok |

## troubleshooting (5)

| fixture | rel old→new | key old→new | edges old→new | depth | n_roots | flags |
|---|---|---|---|---|---|---|
| crashloopbackoff_oomkilled | 87→37 | 87→3 | 112→42 | 3 | 1 | ok |
| deployment_rollout_stuck | 29→29 | 29→6 | 32→32 | 3 | 1 | ok |
| imagepullbackoff_registry_secret | 86→86 | 86→5 | 111→111 | 3 | 1 | ok |
| pod_pending_no_resources | 86→86 | 86→4 | 111→111 | 3 | 1 | ok |
| service_no_endpoints | 39→40 | 39→4 | 43→42 | 3 | 1 | ok |

## yaml_gen (15)

| fixture | rel old→new | key old→new | edges old→new | depth | n_roots | flags |
|---|---|---|---|---|---|---|
| clusterrole_read_pods | 5→5 | 2→2 | 4→4 | 3 | 1 | ok |
| clusterrolebinding_yaml | 10→10 | 3→3 | 9→9 | 3 | 1 | ok |
| configmap_env | 1→1 | 1→1 | 0→0 | 3 | 1 | ok |
| cronjob_backup | 10→10 | 4→1 | 10→10 | 3 | 1 | ok |
| daemonset_fluentd | 29→29 | 3→1 | 31→31 | 3 | 1 | ok |
| deployment_3_replicas | 29→29 | 3→2 | 32→32 | 3 | 1 | ok |
| deployment_liveness_probe | 30→30 | 3→3 | 32→32 | 3 | 1 | ok |
| ingress_rules | 21→21 | 3→2 | 21→21 | 3 | 1 | ok |
| networkpolicy_deny_all | 8→9 | 2→2 | 9→9 | 3 | 1 | ok |
| pod_configmap_volume | 86→86 | 5→1 | 111→111 | 3 | 1 | ok |
| pvc_dynamic | 14→14 | 2→1 | 14→14 | 3 | 1 | ok |
| rolebinding_dev | 8→8 | 2→3 | 7→7 | 3 | 1 | ok |
| service_nodeport | 38→38 | 3→1 | 42→42 | 3 | 1 | ok |
| statefulset_with_pvc | 41→41 | 3→3 | 46→46 | 3 | 1 | ok |
| yaml_layer3_required_fields | 29→29 | 4→1 | 32→32 | 3 | 1 | ok |

---

## Post-Translation Changes (Langkah 3–4)

> Applied per-category after manual validation gate. All 8 categories ✅ applied.

### Translation scope

| Kategori | Fixtures | Aksi |
|----------|----------|------|
| command | 3 | Translate Q/A/context; 3 OOS rewritten to in-scope schema Q in prior session |
| conceptual | 15 | Translate 15; `scope_accuracy_node` reframed (ObjectMeta/RBAC removed from context) |
| followup | 12 | Translate 12; all context entries upgraded to full FQN |
| planning | 5 | Translate 5; all resource K8s valid, context FQN clean |
| realworld | 24 | 4 keep; 6 full rewrite (OOS→in-scope); 14 drop (selection_score=0) |
| relationship | 18 | Translate 18; 3 full rewrites + 3 minor fixes + 2 KG-topology fixes |
| troubleshooting | 5 | Already English from prior session OOS rewrites; GT re-curation applied |
| yaml_gen | 15 | Translate 15; 2 prose answers → proper YAML; all context FQN-upgraded |

### KG-topology fixes (post-translation, relationship category)

| Fixture | Root before | Root after | Reason |
|---------|-------------|------------|--------|
| `anyof_intorstring` | `ContainerPort` (KG leaf, 0 outgoing edges) | `EnvFromSource` | ContainerPort has no outgoing KG edges; actual ANY_OF edges in KG are `EnvFromSource -[ANY_OF]-> ConfigMapEnvSource/SecretEnvSource`; fully rewritten Q/A/context |
| `secret_usage` | `Secret` (KG leaf, 0 outgoing edges) | `PodSpec` | Secret has no outgoing KG edges; engine found ep=0; `PodSpec -[USES_SECRET]-> Secret` and `PodSpec -[HAS_CONTAINER]-> Container -[...]-> SecretKeySelector` paths valid; ep 0→130 |

### Realworld drop list (selection_score=0)

| Fixture | Reason |
|---------|--------|
| `pbased_on_a_hrefhttpsstackoverflowcomquestions599` | Podman-specific |
| `pcopied_from_here_a_hrefhttpsgithubcomkubeflowpi` | Kubeflow Pipelines Python |
| `pi_am_quite_new_to_tektonp` | Tekton Pipelines |
| `pi_cant_find_documentation_on_how` | User groups / auth system |
| `pi_have_a_google_kubernetes_cluster` | GKE VM image change |
| `pi_have_a_tekton_codepipelinecode_and` | Tekton PipelineRun |
| `pim_using_argocd_and_i_want` | ArgoCD application spec |
| `pthis_eks_cluster_has_a_private` | EKS private endpoint |
| `pi_want_to_reject_all_docker` | Admission Controllers runtime |
| `pid_like_to_confirm_information_of` | kubectl auth info |
| `pwith_kubectl_i_know_i_can` | Python kubernetes client |
| `pwhen_using_istio_with_kubernetes_a` | Istio + Kustomize |
| `pkubectl_provides_a_nice_way_to` | kubectl create secret behavior |
| `pusing_kubernetes_v1157_in_minikube_and` | kubectl apply merge behavior |

Files preserved (not deleted) — `selection_score=0` gates them out of `evaluate.py`.

---

## Final Validation Results (Langkah 5)

Run: `python scripts/validate_dataset.py` (Neo4j online, 2026-06-11)

| Check | Result |
|-------|--------|
| Total fixtures processed | 97 (83 active after 14 realworld drops) |
| Expected path edges VALID | 2702 / 2702 (100%) |
| NOT_IN_GRAPH edges | **0** |
| Phantom relevant_nodes | **0** |
| Phantom key_nodes | **0** |
| key⊄relevant violations | **0** |
| YAML syntactic PASS | 23 / 23 |
| YAML schema PASS | 22 / 23 (1 N/A: ArgoCD dropped fixture) |

---

## Post-Devil's-Advocate Critique (2026-06-12)

Systematic re-examination of all 103 active fixtures against scope constraint: answers must be fully derivable from swagger `definitions` block. 14 fixtures amended across 4 issue groups.

### Group A — Scope violations (OOS clause removed from Q/A)

| Fixture | Change |
|---------|--------|
| `planning/plan_cronjob_batch` | Q: removed "sends a notification if the backup fails" clause. A: removed "For failure notifications: ..." sentence (Prometheus/AlertManager are OOS). |
| `realworld/hpa_custom_metrics_yaml` | Q: "from Prometheus" -> "custom external metric" (Prometheus not in swagger definitions). |
| `realworld/deployment_vs_statefulset_comparison` | Q: removed "When should each be used?" (design guidance, not schema). A: removed "Use Deployment for web servers..." sentence. |

### Group B — Question framing issues

| Fixture | Change |
|---------|--------|
| `relationship/namespace_quota_relation` | resource: Namespace -> ResourceQuota. Q + A rewritten to ResourceQuota-centric schema question. Context updated with ResourceQuota/ResourceQuotaSpec/ResourceQuotaStatus seeds. GT re-derived via recurate: rel 7->6, key stays 4. Old GT was broken (expected_path traversed Namespace subgraph but key_nodes had ResourceQuota — internal inconsistency). |
| `relationship/cronjob_job_pod` | Q: "How does a CronJob create and manage Pods?" -> "What schema chain in the CronJob API connects a CronJob definition to the Pod spec it will eventually run?" (removes runtime controller framing). GT unchanged. |
| `relationship/service_selector` | Q: removed "receive its traffic" (runtime routing language). A: removed "The KG represents this relationship with a SELECTS_POD edge from Service to Pod." (KG-meta reference). GT unchanged (by-design neighborhood from Service root). |

### Group C — KG-meta reference in question

| Fixture | Change |
|---------|--------|
| `relationship/anyof_intorstring` | Q: removed "represented in the knowledge graph" clause. Now asks how alternatives are expressed in the API schema. GT unchanged. |

### Group D — Structural bug: multi_hop=True on KG leaf nodes (ep=0)

ConfigMap and Secret are KG leaf nodes (no outgoing edges). multi_hop=True triggered pointless deep traversal.

| Fixture | Change |
|---------|--------|
| `conceptual/configmap_usage` | multi_hop: true -> false |
| `realworld/configmap_volume_mount` | multi_hop: true -> false |
| `realworld/pi_am_wondering_if_it_is` | multi_hop: true -> false |
| `realworld/pi_want_to_pass_a_certificate` | multi_hop: true -> false |
| `yaml_gen/secret_opaque_yaml` | multi_hop: true -> false |

### Group E — Wrong resource leading to inflated GT

| Fixture | Change |
|---------|--------|
| `realworld/precodespec_containers_image_nginx_imagepul` | resource: Pod -> Container. GT re-derived via recurate: rel 87->37, key 4->3. Q specifically asks about Container.securityContext Linux capabilities -- Container is the correct root. |
| `command/kubectl_force_delete_pod` | Kept resource=Pod. Changing to PodSpec expands GT from 86->92 (PodSpec is a deeper hub, reaches more nodes in 3 hops). Pod is the correct root for this question. |
| `troubleshooting/imagepullbackoff_registry_secret` | Kept resource=Pod. Same reason as above (PodSpec > Pod in neighborhood size). Pod is correct. |

### Post-critique validation (2026-06-12)

| Check | Result |
|-------|--------|
| Total fixtures active | 103 (117 total) |
| Expected path edges VALID | 3030 / 3030 (100%) |
| NOT_IN_GRAPH edges | 0 |
| Phantom relevant_nodes | 0 |
| Phantom key_nodes | 0 |
| key⊄relevant violations | 0 |
| YAML syntactic PASS | 33 / 33 |
| YAML schema PASS | 32 / 33 (1 N/A: pim_using_argocd) |

**Exit criteria met.** All Rubrik B4/B5/B6 checks clean.
