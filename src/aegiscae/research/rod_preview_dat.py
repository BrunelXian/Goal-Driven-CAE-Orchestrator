"""Independent, pure DAT reader for the frozen single-rod printed layout.

This does not call AF's parser, accept its PASS, read files, or validate ODB.
Artifact/run attribution is checked separately by the preview event reducer.
"""

import re
from decimal import Decimal

from aegiscae.contracts.research_contracts import require

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d{1,3})?"


def _number(value):
    require(len(value) <= 40 and re.fullmatch(NUMBER, value), "DAT_INVALID_NUMBER")
    number = Decimal(re.sub("[Dd]", "E", value))
    require(number.is_finite() and abs(number) < Decimal("1e20"), "DAT_INVALID_NUMBER")
    return number


def verify_dat(data, load_n, contract):
    require(type(data) is bytes and 0 < len(data) <= 16384, "DAT_LIMIT")
    try:
        text = data.decode("cp936", errors="strict")
    except UnicodeError:
        require(False, "DAT_ENCODING")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    require(len(lines) <= 512 and all(len(line) <= 1024 for line in lines), "DAT_LIMIT")
    require(not any("***ERROR" in line or "HAS NOT BEEN COMPLETED" in line
                    for line in lines), "DAT_FAILURE_TEXT")
    for line in lines:
        if not line.isascii():
            require(re.fullmatch(r"Abaqus 2024 Date \d{2}-\d{2}月-2026 Time \d{2}:\d{2}:\d{2}",
                                 line) is not None, "DAT_ENCODING")

    def one(pattern):
        found = [(index, re.fullmatch(pattern, line)) for index, line in enumerate(lines)]
        found = [(index, match) for index, match in found if match]
        require(len(found) == 1, "DAT_MARKER_MISSING_OR_DUPLICATE")
        return found[0]

    heading, _ = one(r"R010 axial bar a19d17ea - N mm MPa STEP 1 INCREMENT 1")
    require(sum(bool(re.search(r"STEP \d+ INCREMENT \d+", line)) for line in lines) == 1,
            "DAT_STEP_AMBIGUOUS")
    static, _ = one(r"S T E P 1 S T A T I C A N A L Y S I S")
    summary, _ = one(r"INCREMENT 1 SUMMARY")
    require(sum(bool(re.fullmatch(r"INCREMENT \d+ SUMMARY", line)) for line in lines) == 1,
            "DAT_INCREMENT_AMBIGUOUS")
    inc, values = one("TIME INCREMENT COMPLETED (" + NUMBER +
                      ") , FRACTION OF STEP COMPLETED (" + NUMBER + ")")
    require(all(_number(v) == 1 for v in values.groups()), "DAT_FINAL_TIME")
    final, values = one("STEP TIME COMPLETED (" + NUMBER +
                        ") , TOTAL TIME COMPLETED (" + NUMBER + ")")
    require(all(_number(v) == 1 for v in values.groups()), "DAT_FINAL_TIME")
    complete, _ = one("THE ANALYSIS HAS BEEN COMPLETED")
    finish, _ = one("ANALYSIS COMPLETE")
    require(heading < static < summary < inc < final < complete < finish, "DAT_ORDER")
    require(any(re.fullmatch(r"Abaqus 2024 Date .+ Time \d{2}:\d{2}:\d{2}", line)
                for line in lines), "DAT_VERSION")
    tail = [line for line in lines[finish + 1:] if line]
    require(len(tail) == 5 and tail[0] == "JOB TIME SUMMARY", "DAT_FOOTER")
    for line, label in zip(tail[1:], (r"USER TIME \(SEC\)", r"SYSTEM TIME \(SEC\)",
                                    r"TOTAL CPU TIME \(SEC\)", r"WALLCLOCK TIME \(SEC\)")):
        require(re.fullmatch(label + " = " + NUMBER, line), "DAT_FOOTER")
    metrics, row_lines, order = {}, {}, []
    for header, prefix, entities, labels in (
        ("ELEMENT PT FOOT- S11", 2, {"1"}, ("S11",)),
        ("NODE FOOT- U1 U2 U3", 1, {"1", "2"}, ("U1", "U2", "U3")),
        ("NODE FOOT- RF1 RF2 RF3", 1, {"1", "2"}, ("RF1", "RF2", "RF3")),
    ):
        index, _ = one(re.escape(header))
        require(final < index < complete and lines[index + 1] == "NOTE", "DAT_TABLE_CONTEXT")
        prior = [line for line in lines[final + 1:index] if line]
        if prefix == 2:
            require(prior[-2:] == ["THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS FOR ELEMENT TYPE T3D2 AND ELEMENT SET", "BAR"],
                    "DAT_ELEMENT_LOCATION")
        else:
            require(prior[-1:] == ["THE FOLLOWING TABLE IS PRINTED FOR ALL NODES"],
                    "DAT_NODE_LOCATION")
        cursor = index + 2
        while cursor < complete and not lines[cursor]:
            cursor += 1
        seen = set()
        while cursor < complete and lines[cursor]:
            fields = lines[cursor].split()
            require(len(fields) == prefix + len(labels) and fields[0] in entities
                    and fields[0] not in seen, "DAT_ENTITY")
            require(prefix == 1 or fields[1] == "1", "DAT_INTEGRATION_POINT")
            seen.add(fields[0])
            for label, value in zip(labels, fields[prefix:]):
                metrics[fields[0] + "_" + label] = _number(value)
                row_lines[fields[0] + "_" + label] = cursor + 1
            cursor += 1
        require(seen == entities, "DAT_MISSING_ENTITY")
        order.append(index)
    require(order == sorted(order) and sum(line.startswith(("NODE FOOT-", "ELEMENT PT"))
                                          for line in lines) == 3, "DAT_EXTRA_TABLE")
    force = Decimal(load_n)
    checks = {"2_U1": (force / 100, Decimal(contract["displacement_tolerance_mm"])),
              "1_S11": (force, Decimal(contract["stress_tolerance_mpa"])),
              "1_RF1": (-force, Decimal(contract["reaction_tolerance_n"]))}
    checks.update({key: (Decimal(0), Decimal("0.00000001")) for key in
                   ("1_U1", "1_U2", "1_U3", "2_U2", "2_U3")})
    checks.update({key: (Decimal(0), Decimal(contract["reaction_tolerance_n"])) for key in
                   ("1_RF2", "1_RF3", "2_RF1", "2_RF2", "2_RF3")})
    require(all(abs(metrics[key] - expected) <= tolerance
                for key, (expected, tolerance) in checks.items()), "DAT_NUMERICAL_MISMATCH")
    require(abs(force + metrics["1_RF1"] + metrics["2_RF1"])
            <= Decimal(contract["reaction_tolerance_n"]) * 2, "DAT_FORCE_BALANCE")
    return {"displacement_mm": str(metrics["2_U1"]), "stress_mpa": str(metrics["1_S11"]),
            "reaction_n": str(metrics["1_RF1"]), "source_lines": row_lines,
            "parser_version": "gdcae-independent-rod-dat-v1", "step": 1, "increment": 1,
            "solver_completion": "DAT_COMPLETION_AND_DECLARED_EXIT_ZERO",
            "analytical_crosscheck": "PASS", "units": "N_mm_MPa"}
