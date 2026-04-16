#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import shutil
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


def json_dumps_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"


def merkle_leaf_hash(manifest_bytes: bytes) -> str:
    return sha256_bytes(b"leaf:" + manifest_bytes)


def merkle_node_hash(left_hex: str, right_hex: str) -> str:
    return sha256_bytes(b"node:" + bytes.fromhex(left_hex) + bytes.fromhex(right_hex))


def build_merkle_tree(leaf_hashes):
    if not leaf_hashes:
        raise ValueError("No leaf hashes to build Merkle tree")

    levels = [leaf_hashes[:]]
    current = leaf_hashes[:]

    while len(current) > 1:
        nxt = []
        i = 0
        while i < len(current):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else current[i]
            nxt.append(merkle_node_hash(left, right))
            i += 2
        levels.append(nxt)
        current = nxt

    return levels


def build_inclusion_proof(levels, index):
    siblings = []
    idx = index

    for level in levels[:-1]:
        if idx % 2 == 0:
            sibling_index = idx + 1 if idx + 1 < len(level) else idx
            position = "right"
        else:
            sibling_index = idx - 1
            position = "left"

        siblings.append({
            "position": position,
            "hash": level[sibling_index],
        })
        idx //= 2

    return siblings


def ensure_clean_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Build claim bundle with Merkle proofs")
    parser.add_argument("--claims", default="claims/claims.yaml", help="Path to claims YAML")
    parser.add_argument("--out-dir", default="out/proofs", help="Output directory")
    args = parser.parse_args()

    repo_root = Path.cwd()
    claims_path = repo_root / args.claims
    out_dir = repo_root / args.out_dir

    if not claims_path.exists():
        raise SystemExit(f"Claims file not found: {claims_path}")

    with claims_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    version = data.get("version", 1)
    claims = data.get("claims", [])

    if not isinstance(claims, list) or not claims:
        raise SystemExit("claims.yaml must contain a non-empty 'claims' list")

    claim_ids = set()
    for claim in claims:
        cid = claim.get("id")
        if not cid:
            raise SystemExit("Each claim must have an 'id'")
        if cid in claim_ids:
            raise SystemExit(f"Duplicate claim id found: {cid}")
        claim_ids.add(cid)

    manifests_dir = out_dir / "manifests"
    proofs_dir = out_dir / "inclusion_proofs"

    ensure_clean_dir(out_dir)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    proofs_dir.mkdir(parents=True, exist_ok=True)

    manifest_records = []
    leaf_hashes = []

    for claim in claims:
        cid = claim["id"]
        title = claim.get("title", "")
        statement = claim.get("statement", "")
        evidence_paths = claim.get("evidence_paths", [])

        if not evidence_paths:
            raise SystemExit(f"{cid}: evidence_paths must not be empty")

        evidence = []
        for rel in evidence_paths:
            rel_path = Path(rel)
            full_path = repo_root / rel_path

            if not full_path.exists():
                raise SystemExit(f"{cid}: evidence file not found: {rel}")

            if not full_path.is_file():
                raise SystemExit(f"{cid}: evidence path is not a file: {rel}")

            evidence.append({
                "path": rel_path.as_posix(),
                "sha256": sha256_file(full_path),
                "size": full_path.stat().st_size,
            })

        manifest = {
            "version": 1,
            "claim_id": cid,
            "title": title,
            "statement": statement,
            "evidence": evidence,
        }

        manifest_bytes = json_dumps_bytes(manifest)
        manifest_hash = sha256_bytes(manifest_bytes)
        leaf_hash = merkle_leaf_hash(manifest_bytes)

        manifest_filename = f"{cid}.json"
        manifest_rel = Path("out/proofs/manifests") / manifest_filename
        manifest_abs = manifests_dir / manifest_filename

        with manifest_abs.open("wb") as f:
            f.write(manifest_bytes)

        manifest_records.append({
            "claim_id": cid,
            "manifest_path": manifest_rel.as_posix(),
            "manifest_sha256": manifest_hash,
            "leaf_hash": leaf_hash,
        })
        leaf_hashes.append(leaf_hash)

    levels = build_merkle_tree(leaf_hashes)
    merkle_root = levels[-1][0]

    tree_obj = {
        "version": 1,
        "hash_algorithm": "sha256",
        "leaf_prefix": "leaf:",
        "node_prefix": "node:",
        "leaf_count": len(leaf_hashes),
        "levels": levels,
        "root": merkle_root,
    }

    with (out_dir / "merkle_tree.json").open("w", encoding="utf-8") as f:
        json.dump(tree_obj, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    with (out_dir / "root.txt").open("w", encoding="utf-8") as f:
        f.write(merkle_root + "\n")

    claim_to_proof = {
        "version": 1,
        "root": merkle_root,
        "claims": []
    }

    for i, rec in enumerate(manifest_records):
        siblings = build_inclusion_proof(levels, i)
        proof_obj = {
            "version": 1,
            "claim_id": rec["claim_id"],
            "manifest_path": rec["manifest_path"],
            "leaf_index": i,
            "leaf_hash": rec["leaf_hash"],
            "siblings": siblings,
            "root": merkle_root,
        }

        proof_filename = f"{rec['claim_id']}.proof.json"
        proof_rel = Path("out/proofs/inclusion_proofs") / proof_filename
        proof_abs = proofs_dir / proof_filename

        with proof_abs.open("w", encoding="utf-8") as f:
            json.dump(proof_obj, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.write("\n")

        claim_to_proof["claims"].append({
            "claim_id": rec["claim_id"],
            "manifest_path": rec["manifest_path"],
            "proof_path": proof_rel.as_posix(),
            "manifest_sha256": rec["manifest_sha256"],
            "leaf_hash": rec["leaf_hash"],
            "root": merkle_root,
        })

    with (out_dir / "claim_to_proof.json").open("w", encoding="utf-8") as f:
        json.dump(claim_to_proof, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    summary = {
        "version": version,
        "claims_file": args.claims,
        "claim_count": len(claims),
        "root": merkle_root,
        "outputs": {
            "mapping": "out/proofs/claim_to_proof.json",
            "tree": "out/proofs/merkle_tree.json",
            "root": "out/proofs/root.txt",
            "manifests_dir": "out/proofs/manifests",
            "proofs_dir": "out/proofs/inclusion_proofs",
        },
    }

    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    print(f"[OK] wrote: {out_dir / 'claim_to_proof.json'}")
    print(f"[OK] wrote: {out_dir / 'merkle_tree.json'}")
    print(f"[OK] wrote: {out_dir / 'root.txt'}")
    print(f"[OK] wrote manifests: {manifests_dir}")
    print(f"[OK] wrote proofs: {proofs_dir}")
    print(f"[OK] merkle_root: {merkle_root}")
    print(f"[OK] claim_count: {len(claims)}")


if __name__ == "__main__":
    main()
