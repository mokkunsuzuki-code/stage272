#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit(
        "PyYAML is required. Install it with:\n"
        "python3 -m pip install pyyaml"
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def merkle_leaf_hash(manifest_bytes: bytes) -> str:
    return sha256_bytes(b"leaf:" + manifest_bytes)


def merkle_node_hash(left_hex: str, right_hex: str) -> str:
    return sha256_bytes(b"node:" + bytes.fromhex(left_hex) + bytes.fromhex(right_hex))


def verify_inclusion_proof(leaf_hash: str, siblings, expected_root: str) -> bool:
    current = leaf_hash
    for item in siblings:
        pos = item["position"]
        sibling_hash = item["hash"]

        if pos == "left":
            current = merkle_node_hash(sibling_hash, current)
        elif pos == "right":
            current = merkle_node_hash(current, sibling_hash)
        else:
            return False
    return current == expected_root


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Verify security claims against evidence and Merkle proofs")
    parser.add_argument("--claims", default="claims/claims.yaml", help="Path to claims YAML")
    parser.add_argument("--bundle-dir", default="out/proofs", help="Bundle directory")
    args = parser.parse_args()

    repo_root = Path.cwd()
    claims_path = repo_root / args.claims
    bundle_dir = repo_root / args.bundle_dir

    claim_map_path = bundle_dir / "claim_to_proof.json"
    tree_path = bundle_dir / "merkle_tree.json"
    root_path = bundle_dir / "root.txt"

    required = [claims_path, claim_map_path, tree_path, root_path]
    for p in required:
        if not p.exists():
            raise SystemExit(f"Required file not found: {p}")

    with claims_path.open("r", encoding="utf-8") as f:
        claims_doc = yaml.safe_load(f)

    claims = claims_doc.get("claims", [])
    if not claims:
        raise SystemExit("claims.yaml does not contain any claims")

    claim_map = load_json(claim_map_path)
    tree = load_json(tree_path)
    root_txt = root_path.read_text(encoding="utf-8").strip()

    expected_root = claim_map.get("root", "")
    if expected_root != root_txt:
        raise SystemExit("[NG] root mismatch between claim_to_proof.json and root.txt")

    if tree.get("root", "") != root_txt:
        raise SystemExit("[NG] root mismatch between merkle_tree.json and root.txt")

    mapping_by_id = {x["claim_id"]: x for x in claim_map.get("claims", [])}
    claims_by_id = {x["id"]: x for x in claims}

    ok = True

    if set(mapping_by_id.keys()) != set(claims_by_id.keys()):
        print("[NG] claim IDs mismatch between claims.yaml and claim_to_proof.json")
        print("  claims.yaml:", sorted(claims_by_id.keys()))
        print("  claim_to_proof.json:", sorted(mapping_by_id.keys()))
        raise SystemExit(1)

    print("[OK] claim ID set matches")

    for claim_id in sorted(claims_by_id.keys()):
        claim = claims_by_id[claim_id]
        mapped = mapping_by_id[claim_id]

        manifest_path = repo_root / mapped["manifest_path"]
        proof_path = repo_root / mapped["proof_path"]

        if not manifest_path.exists():
            print(f"[NG] {claim_id}: missing manifest {manifest_path}")
            ok = False
            continue

        if not proof_path.exists():
            print(f"[NG] {claim_id}: missing proof {proof_path}")
            ok = False
            continue

        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        proof = load_json(proof_path)

        # 1) manifest metadata check
        if manifest.get("claim_id") != claim_id:
            print(f"[NG] {claim_id}: manifest claim_id mismatch")
            ok = False
            continue

        if manifest.get("title", "") != claim.get("title", ""):
            print(f"[NG] {claim_id}: title mismatch")
            ok = False
            continue

        if manifest.get("statement", "") != claim.get("statement", ""):
            print(f"[NG] {claim_id}: statement mismatch")
            ok = False
            continue

        manifest_evidence = manifest.get("evidence", [])
        claim_evidence_paths = claim.get("evidence_paths", [])

        if len(manifest_evidence) != len(claim_evidence_paths):
            print(f"[NG] {claim_id}: evidence count mismatch")
            ok = False
            continue

        # 2) source file hash verification
        per_claim_ok = True
        for entry, rel in zip(manifest_evidence, claim_evidence_paths):
            src = repo_root / rel
            if not src.exists():
                print(f"[NG] {claim_id}: missing evidence source file {rel}")
                ok = False
                per_claim_ok = False
                continue

            actual_sha = sha256_file(src)
            if entry.get("path") != rel:
                print(f"[NG] {claim_id}: evidence path mismatch for {rel}")
                ok = False
                per_claim_ok = False
                continue

            if entry.get("sha256") != actual_sha:
                print(f"[NG] {claim_id}: sha256 mismatch for {rel}")
                print(f"      expected(manifest): {entry.get('sha256')}")
                print(f"      actual(file):       {actual_sha}")
                ok = False
                per_claim_ok = False

        if not per_claim_ok:
            continue

        # 3) manifest hash check
        actual_manifest_sha = sha256_bytes(manifest_bytes)
        if mapped.get("manifest_sha256") != actual_manifest_sha:
            print(f"[NG] {claim_id}: manifest sha256 mismatch")
            ok = False
            continue

        # 4) leaf hash check
        actual_leaf_hash = merkle_leaf_hash(manifest_bytes)
        if mapped.get("leaf_hash") != actual_leaf_hash:
            print(f"[NG] {claim_id}: leaf hash mismatch (mapping)")
            ok = False
            continue

        if proof.get("leaf_hash") != actual_leaf_hash:
            print(f"[NG] {claim_id}: leaf hash mismatch (proof)")
            ok = False
            continue

        # 5) root consistency
        if proof.get("root") != expected_root:
            print(f"[NG] {claim_id}: proof root mismatch")
            ok = False
            continue

        # 6) inclusion proof verification
        siblings = proof.get("siblings", [])
        if not verify_inclusion_proof(actual_leaf_hash, siblings, expected_root):
            print(f"[NG] {claim_id}: inclusion proof verification failed")
            ok = False
            continue

        print(f"[OK] {claim_id}: verified")

    if not ok:
        raise SystemExit(1)

    print("[OK] all security claims verified")


if __name__ == "__main__":
    main()
