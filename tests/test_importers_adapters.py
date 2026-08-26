from pathlib import Path

import yaml
from openpyxl import Workbook

from transformation_graph.adapters import (
    graph_from_interface_as_code,
    graph_from_mapping_as_code,
    graph_from_process_as_code,
)
from transformation_graph.importers import graph_from_excel


def test_excel_import_uses_csv_compatible_contract(tmp_path: Path):
    workbook_path = tmp_path / "inventory.xlsx"
    workbook = Workbook()
    nodes = workbook.active
    nodes.title = "Nodes"
    nodes.append(["id", "type", "title", "description", "tags", "attributes_json"])
    nodes.append(["system.source", "system", "Source", "", "sap;source", '{"landscape":"DEV"}'])
    nodes.append(["interface.customer", "interface", "Customer replication", "", "", ""])
    edges = workbook.create_sheet("Edges")
    edges.append(["from", "to", "type", "label", "attributes_json"])
    edges.append(["system.source", "interface.customer", "publishes_to", "", ""])
    workbook.save(workbook_path)

    graph = graph_from_excel(workbook_path, "excel-demo", "Excel Demo")

    assert graph.stats()["nodes"] == 2
    assert graph.stats()["edges"] == 1
    assert graph.nodes["system.source"].attributes["landscape"] == "DEV"
    assert graph.project["source_format"] == "excel"


def test_mapping_as_code_adapter_builds_field_level_traceability(tmp_path: Path):
    source = tmp_path / "mapping.yaml"
    source.write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "mapping": {
                    "id": "customer-core",
                    "source": "SAP-MDG.BusinessPartner",
                    "target": "SAP-S4.Customer",
                    "fields": [
                        {"source": "business_partner_id", "target": "KUNNR", "rule": "preserve"},
                        {"source": "country", "target": "LAND1", "rule": "ISO-3166-alpha2"},
                    ],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    graph = graph_from_mapping_as_code(source)

    assert "mapping.customer-core" in graph.nodes
    assert graph.stats()["node_types"]["rule"] == 2
    assert graph.path("mapping.customer-core", "rule.customer-core.1") == [
        "mapping.customer-core",
        "rule.customer-core.1",
    ]
    assert graph.path("rule.customer-core.1", "field.SAP-S4.Customer.KUNNR") == [
        "rule.customer-core.1",
        "field.SAP-S4.Customer.KUNNR",
    ]


def test_interface_as_code_adapter_preserves_operational_context(tmp_path: Path):
    source = tmp_path / "interface.yaml"
    source.write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "interface": {
                    "id": "CUSTOMER-MDG-S4-01",
                    "name": "Customer replication",
                    "source": {"system": "SAP-MDG", "object": "BusinessPartner"},
                    "target": {"system": "SAP-S4", "object": "Customer"},
                    "mode": "async",
                    "criticality": "high",
                },
                "ownership": {"business": "Customer Master Data"},
                "route": {"middleware": ["SAP-Integration-Layer"]},
                "mapping": {"file": "mapping.yaml", "profile": "customer-core"},
                "tests": [{"id": "happy-path", "description": "Customer arrives", "expected": "processed"}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    graph = graph_from_interface_as_code(source)

    interface = graph.nodes["interface.CUSTOMER-MDG-S4-01"]
    assert interface.attributes["mode"] == "async"
    assert "system.SAP-MDG" in graph.nodes
    assert "mapping.customer-core" in graph.nodes
    assert graph.path("test.CUSTOMER-MDG-S4-01.happy-path", "system.SAP-S4") == [
        "test.CUSTOMER-MDG-S4-01.happy-path",
        "interface.CUSTOMER-MDG-S4-01",
        "system.SAP-S4",
    ]


def test_process_as_code_adapter_builds_step_transitions_and_links(tmp_path: Path):
    source = tmp_path / "process.yaml"
    source.write_text(
        yaml.safe_dump(
            {
                "version": "0.2",
                "process": {"id": "customer_creation", "name": "Customer Creation", "owner": "data_governance_lead", "start": "request"},
                "roles": [{"id": "data_governance_lead", "name": "Data Governance Lead"}],
                "systems": [{"id": "mdg", "name": "SAP MDG"}],
                "objects": [{"id": "business_partner", "name": "Business Partner"}],
                "interfaces": [{"id": "customer_replication", "name": "Customer replication"}],
                "controls": [], "risks": [], "evidence": [],
                "steps": [
                    {"id": "request", "name": "Submit request", "type": "user_task", "actor": "data_governance_lead", "system": "mdg", "objects": ["business_partner"], "transitions": [{"to": "replicate"}]},
                    {"id": "replicate", "name": "Replicate", "type": "service_task", "system": "mdg", "interfaces": ["customer_replication"], "transitions": [{"to": "complete"}]},
                    {"id": "complete", "name": "Complete", "type": "end"},
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    graph = graph_from_process_as_code(source)

    assert graph.path("process_step.customer_creation.request", "process_step.customer_creation.complete") == [
        "process_step.customer_creation.request",
        "process_step.customer_creation.replicate",
        "process_step.customer_creation.complete",
    ]
    assert "interface.customer_replication" in graph.nodes
    assert "owner.data_governance_lead" in graph.nodes
