from __future__ import annotations

from importlib.resources import files
import json
from typing import Any, Literal

import yaml

from .model import GraphValidationError

ADAPTER_CONTRACT_ID = "transformation-graph-adapter"
ADAPTER_CONTRACT_VERSION = "0.1"
ContractFormat = Literal["yaml", "json"]


def adapter_contract_text() -> str:
    resource = files("transformation_graph").joinpath("contracts/adapter-contract-v0.1.yaml")
    return resource.read_text(encoding="utf-8")


def load_adapter_contract() -> dict[str, Any]:
    raw = yaml.safe_load(adapter_contract_text())
    if not isinstance(raw, dict) or not isinstance(raw.get("contract"), dict):
        raise GraphValidationError("packaged adapter contract is invalid")
    contract = raw["contract"]
    if contract.get("id") != ADAPTER_CONTRACT_ID or str(contract.get("version")) != ADAPTER_CONTRACT_VERSION:
        raise GraphValidationError("packaged adapter contract identity/version mismatch")
    return raw


def render_adapter_contract(format: ContractFormat = "yaml") -> str:
    contract = load_adapter_contract()
    if format == "yaml":
        return yaml.safe_dump(contract, sort_keys=False, allow_unicode=True)
    if format == "json":
        return json.dumps(contract, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    raise GraphValidationError(f"unsupported adapter contract format: {format}")
