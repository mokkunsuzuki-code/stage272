#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import yaml

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def verify(pub, sig, artifact):
    r = run([
        "openssl","pkeyutl",
        "-verify","-pubin",
        "-inkey", pub,
        "-sigfile", sig,
        "-rawin",
        "-in", artifact
    ])
    return r.returncode == 0

def main():
    if len(sys.argv) != 2:
        print("usage: verify_multi_party.py <artifact>")
        sys.exit(1)

    artifact = sys.argv[1]

    with open("policy/policy.yaml") as f:
        policy = yaml.safe_load(f)

    required = policy["threshold"]["required"]
    signers = policy["signers"]

    ok_count = 0
    results = []

    for s in signers:
        ok = verify(s["public_key"], s["signature"], artifact)
        results.append({"id": s["id"], "ok": ok})

        print(f"[INFO] signer: {s['id']} -> {'OK' if ok else 'FAIL'}")

        if ok:
            ok_count += 1

    print(f"[INFO] threshold: {ok_count}/{required}")

    if ok_count < required:
        print("[FAIL] threshold not satisfied")
        sys.exit(1)

    os.makedirs("out/multi_party", exist_ok=True)

    with open("out/multi_party/result.json","w") as f:
        json.dump(results, f, indent=2)

    print("[OK] multi-party verification passed")

if __name__ == "__main__":
    main()
