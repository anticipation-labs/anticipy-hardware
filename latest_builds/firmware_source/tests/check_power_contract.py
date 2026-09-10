#!/usr/bin/env python3
"""Check generated firmware configuration against the corrected native netlist.
This is a revision-pairing check, not an electrical or physical power test.
"""
import re, sys, json, hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

def check(dts_path, netlist_path):
    raw = dts_path.read_text()
    text = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
    checks = []
    def require(name, result):
        checks.append({"check": name, "pass": bool(result)})
    def node(label):
        match = re.search(label+r":\s*\w+\s*\{([^{}]*)\};", text, re.S)
        return match.group(1) if match else ""
    def voltage(body, prop):
        match = re.search(prop+r"\s*=\s*<\s*(0x[0-9a-fA-F]+|[0-9]+)\s*>", body)
        return int(match.group(1),0) if match else None
    b1, b2, charger = node("e1_buck1"), node("e1_buck2"), node("e1_charger")
    for prop in ["regulator-min-microvolt", "regulator-max-microvolt", "regulator-init-microvolt"]:
        require("BUCK1 auxiliary "+prop+"=2500000", voltage(b1,prop)==2500000)
        require("BUCK2 main "+prop+"=3000000", voltage(b2,prop)==3000000)
    require("BUCK1 auxiliary boot-off", "regulator-boot-off;" in b1 and "regulator-always-on;" not in b1)
    require("BUCK2 main always-on never boot-off", "regulator-always-on;" in b2 and "regulator-boot-off;" not in b2)
    require("charger node exists with no enable properties", bool(charger) and "charging-enable" not in charger and "vbatlow-charge-enable" not in charger)
    nets = {}
    for net in ET.parse(netlist_path).getroot().findall("./nets/net"):
        for n in net.findall("node"):
            nets[(n.attrib["ref"],n.attrib["pin"])]=net.attrib["name"]
    for ref,pin in [("U2","32"),("L2","1"),("C8","1"),("U1","28"),("U1","30"),("U5","8")]:
        require(ref+"."+pin+" on BUCK2 3V_MAIN", nets.get((ref,pin))=="/3V_MAIN")
    for ref,pin in [("U2","1"),("L1","1"),("C7","1"),("TP12","1")]:
        require(ref+"."+pin+" on BUCK1 2V5_AUX", nets.get((ref,pin))=="/2V5_AUX")
    for ref,pin,net in [("U2","3","/SW1"),("L1","2","/SW1"),("U2","5","/SW2"),("L2","2","/SW2")]:
        require(ref+"."+pin+" retains "+net, nets.get((ref,pin))==net)
    return {"status":"PASS" if all(c["pass"] for c in checks) else "FAIL", "checks":checks,
        "dts_sha256":hashlib.sha256(dts_path.read_bytes()).hexdigest(),
        "native_netlist_sha256":hashlib.sha256(netlist_path.read_bytes()).hexdigest(),
        "scope":"firmware/native-netlist revision pairing only; physical tests NOT_RUN"}

if __name__ == "__main__":
    result=check(Path(sys.argv[1]),Path(sys.argv[2]))
    print(json.dumps(result,indent=2))
    sys.exit(0 if result["status"]=="PASS" else 1)
