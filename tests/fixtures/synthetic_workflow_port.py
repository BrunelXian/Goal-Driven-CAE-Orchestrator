"""Independent TEST_ONLY durable fixture; never AF IPC or physical evidence.

This tiny SQLite oracle counts fixture effects across coordinator/process death.
It is test infrastructure, not a product dispatcher or a recovery service.
"""

import json
import os
import sqlite3
import stat
import tempfile
import uuid
from dataclasses import asdict
from pathlib import Path

from aegiscae.contracts.research_contracts import ContractError, canonical_json, digest_bytes
from aegiscae.research.workflow_rules import SyntheticEvidence, SyntheticReceipt, SyntheticRequest


class FixtureConflict(ValueError):
    pass


def _root(value):
    path = Path(value)
    temporary = Path(tempfile.gettempdir()).resolve()
    if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(temporary):
        raise ValueError("SYNTHETIC_TEMP_REQUIRED")
    for part in (*reversed(path.parents), path):
        if not part.exists():
            continue
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("SYNTHETIC_REPARSE_REJECTED")
    return path


class DurableSyntheticPort:
    """Fixed A=2/B=0.5 metric values; only generated fixture requirements are used."""

    @classmethod
    def create(cls, root, requirements):
        root = _root(root)
        root.mkdir(exist_ok=False)
        source_id = "syntheticport_" + uuid.uuid4().hex
        config = {"schema_version": "test-fixture-port-v1", "source_id": source_id,
                  "root": str(root.resolve()), "requirements": [asdict(r) for r in requirements],
                  "source_classification": "SYNTHETIC_TEST_ONLY", "test_only": True,
                  "qualification": "NOT_ABAQUS_QUALIFIED", "physical_evidence_eligible": False}
        with (root / "fixture.json").open("xb") as stream:
            stream.write(canonical_json(config))
        with sqlite3.connect(root / "fixture.sqlite3") as db:
            db.execute("CREATE TABLE effects (business_key TEXT PRIMARY KEY, request_digest TEXT, "
                       "receipt TEXT NOT NULL, evidence TEXT NOT NULL)")
            db.execute("CREATE TABLE calls (kind TEXT NOT NULL, business_key TEXT NOT NULL)")
        return cls(root)

    def __init__(self, root, *, fault=None):
        self.root = _root(root)
        config = json.loads((self.root / "fixture.json").read_text(encoding="utf-8"))
        if (config["schema_version"] != "test-fixture-port-v1"
                or config["root"] != str(self.root.resolve())
                or config["source_classification"] != "SYNTHETIC_TEST_ONLY"
                or config["test_only"] is not True or config["physical_evidence_eligible"] is not False):
            raise ValueError("SYNTHETIC_FIXTURE_IDENTITY")
        self.source_id = config["source_id"]
        self.requirements = config["requirements"]
        self.fault = fault

    def _connection(self):
        return sqlite3.connect((self.root / "fixture.sqlite3").as_uri() + "?mode=rw",
                               uri=True, timeout=3)

    def _check(self, request):
        if type(request) is not SyntheticRequest:
            raise FixtureConflict("SYNTHETIC_REQUEST_REQUIRED")
        try:
            SyntheticRequest.from_dict(asdict(request))
        except ContractError:
            raise FixtureConflict("SYNTHETIC_REQUEST_REQUIRED") from None
        if (request.source_id != self.source_id
                or request.source_classification != "SYNTHETIC_TEST_ONLY"
                or request.test_only is not True or request.physical_evidence_eligible is not False
                or request.qualification != "NOT_ABAQUS_QUALIFIED"):
            raise FixtureConflict("SYNTHETIC_REQUEST_REQUIRED")

    def accept(self, request):
        self._check(request)
        key, digest = request.business_key, request.digest()
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO calls VALUES ('accept',?)", (key,))
            row = db.execute("SELECT request_digest,receipt FROM effects WHERE business_key=?",
                             (key,)).fetchone()
            if row:
                if row[0] != digest:
                    raise FixtureConflict("SAME_KEY_DIFFERENT_REQUEST")
                receipt = SyntheticReceipt.from_dict(json.loads(row[1]))
            else:
                identity = digest_bytes(key.encode())[7:39]
                receipt_raw = {"schema_version": "synthetic-receipt-v1", "request": asdict(request),
                               "request_digest": digest, "receipt_id": "syntheticreceipt_" + identity,
                               "accepted": True}
                evidence = {"schema_version": "synthetic-evidence-v1", "receipt": receipt_raw,
                            "evidence_id": "syntheticevidence_" + identity, "protocol_valid": True,
                            "metrics": [{"requirement": r, "quantity": {
                                "value": self._metric_value(request),
                                "dimension": r["dimension"], "unit": r["unit"]}}
                                for r in self.requirements]}
                receipt = SyntheticReceipt.from_dict(receipt_raw)
                SyntheticEvidence.from_dict(evidence)
                db.execute("INSERT INTO effects VALUES (?,?,?,?)",
                           (key, digest, json.dumps(receipt_raw), json.dumps(evidence)))
        if self.fault == "exit_after_accept":
            os._exit(74)
        if self.fault == "response_lost":
            raise TimeoutError("SYNTHETIC_RESPONSE_LOST")
        return receipt

    def _metric_value(self, request):
        return "2" if request.step_id == "A" else "0.5"

    def query(self, request):
        self._check(request)
        with self._connection() as db:
            db.execute("INSERT INTO calls VALUES ('query',?)", (request.business_key,))
            row = db.execute("SELECT request_digest,receipt FROM effects WHERE business_key=?",
                             (request.business_key,)).fetchone()
        if self.fault == "query_unknown" or row is None:
            return None
        if row[0] != request.digest():
            raise FixtureConflict("SAME_KEY_DIFFERENT_REQUEST")
        return SyntheticReceipt.from_dict(json.loads(row[1]))

    def read_evidence(self, request, receipt):
        self._check(request)
        with self._connection() as db:
            db.execute("INSERT INTO calls VALUES ('evidence',?)", (request.business_key,))
            row = db.execute("SELECT request_digest,receipt,evidence FROM effects WHERE business_key=?",
                             (request.business_key,)).fetchone()
        if self.fault == "missing_evidence" or row is None:
            return None
        if row[0] != request.digest() or json.loads(row[1]) != asdict(receipt):
            raise FixtureConflict("SYNTHETIC_EVIDENCE_BINDING")
        return SyntheticEvidence.from_dict(json.loads(row[2]))

    def oracle(self):
        """Count actual fixture rows, independently of Workflow/Decision claims."""
        with sqlite3.connect((self.root / "fixture.sqlite3").as_uri() + "?mode=ro",
                             uri=True) as db:
            return {"effects": db.execute("SELECT COUNT(*) FROM effects").fetchone()[0],
                    "keys": [r[0] for r in db.execute("SELECT business_key FROM effects ORDER BY rowid")],
                    "calls": list(db.execute("SELECT kind,business_key FROM calls ORDER BY rowid"))}
