"""Frozen D7 combined nodal output contract; no observed real-format claim."""
from decimal import Decimal
from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research.rod_preview_rules import decimal

PROFILE = "axial_rod_cload_output_v2"
TRUST = "TRUSTED_LOCAL_HIL"
OUTPUT_STATUS = "REAL_OUTPUT_FORMAT_NOT_YET_OBSERVED"
TEMPLATE = (
    "*HEADING\nR010 axial bar a19d17ea - N mm MPa\n*NODE\n1,0,0,0\n2,10,0,0\n"
    "*NSET, NSET=VERIFY\n1,2\n*ELEMENT, TYPE=T3D2, ELSET=BAR\n1,1,2\n*MATERIAL, NAME=LINEAR\n*ELASTIC\n"
    "1000,0.3\n*SOLID SECTION, ELSET=BAR, MATERIAL=LINEAR\n1\n*STEP\n*STATIC\n"
    "1,1,0.00001,1\n*BOUNDARY\n1,1,3,0\n2,2,3,0\n*CLOAD\n2,1,1\n"
    "*NODE PRINT, NSET=VERIFY, FREQUENCY=1, SUMMARY=NO, TOTALS=NO, GLOBAL=YES\nU1,U2,U3,RF1,RF2,RF3\n"
    "*EL PRINT, ELSET=BAR, FREQUENCY=1, POSITION=INTEGRATION POINTS, SUMMARY=NO, TOTALS=NO\n"
    "S11\n*END STEP\n"
).encode("ascii")
BASELINE = digest_bytes(TEMPLATE)
OUTPUT = {"schema": "rod-output-v2", "node_set": "VERIFY", "nodes": [1, 2],
          "columns": ["U1", "U2", "U3", "RF1", "RF2", "RF3"],
          "element_set": "BAR", "element": 1, "integration_point": 1,
          "element_columns": ["S11"], "step": 1, "increment": 1,
          "units": "N_mm_MPa", "missing": "REJECT", "format_status": OUTPUT_STATUS}


def candidate_bytes(load_n):
    value = decimal(load_n)
    require(Decimal("0.5") <= value <= Decimal("2.5"), "LOAD_RANGE")
    force = format(value, "f")
    force = force.rstrip("0").rstrip(".") if "." in force else force
    prefix, suffix = TEMPLATE.split(b"*CLOAD\n2,1,1\n")
    return prefix + b"*CLOAD\n2,1," + force.encode() + b"\n" + suffix


def contract_digest():
    return digest_bytes(canonical_json(OUTPUT))
