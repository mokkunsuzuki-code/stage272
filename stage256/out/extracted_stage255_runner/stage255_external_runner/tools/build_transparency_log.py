import argparse
import hashlib
import json
from pathlib import Path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_leaf(entry: dict) -> str:
    canonical = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_hex(canonical)


def hash_pair(left_hex: str, right_hex: str) -> str:
    return sha256_hex(bytes.fromhex(left_hex) + bytes.fromhex(right_hex))


def build_merkle_tree(leaf_hashes: list[str]) -> list[list[str]]:
    if not leaf_hashes:
        return [["0" * 64]]

    levels = [leaf_hashes]
    current = leaf_hashes

    while len(current) > 1:
        nxt = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else current[i]
            nxt.append(hash_pair(left, right))
        levels.append(nxt)
        current = nxt

    return levels


def build_inclusion_proof(levels: list[list[str]], index: int) -> list[dict]:
    proof = []
    idx = index

    for level in levels[:-1]:
        if idx % 2 == 0:
            sibling_index = idx + 1 if idx + 1 < len(level) else idx
            sibling_position = "right"
        else:
            sibling_index = idx - 1
            sibling_position = "left"

        proof.append(
            {
                "sibling_hash": level[sibling_index],
                "sibling_position": sibling_position,
            }
        )
        idx //= 2

    return proof


def should_skip(path: Path, output_dir: Path) -> bool:
    path_str = path.as_posix()

    if str(path).startswith(str(output_dir)):
        return True

    skip_prefixes = [
        "out/transparency/",
        "out/checkpoint/",
    ]
    for prefix in skip_prefixes:
        if path_str.startswith(prefix):
            return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Build transparency log, Merkle tree, and inclusion proofs")
    parser.add_argument("--input-dir", required=True, help="Input directory")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    proofs_dir = output_dir / "inclusion_proofs"

    output_dir.mkdir(parents=True, exist_ok=True)
    proofs_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    files = []

    for path in sorted(input_dir.rglob("*")):
        if not path.is_file():
            continue
        if should_skip(path, output_dir):
            continue

        rel_path = path.relative_to(Path.cwd()) if path.is_absolute() else path
        data = path.read_bytes()
        file_hash = sha256_hex(data)

        entry = {
            "path": rel_path.as_posix(),
            "sha256": file_hash,
            "size": len(data),
        }
        entries.append(entry)
        files.append(path)

    transparency_log = {
        "version": "1.0",
        "type": "transparency_log",
        "entry_count": len(entries),
        "entries": entries,
    }

    leaf_hashes = [hash_leaf(entry) for entry in entries]
    levels = build_merkle_tree(leaf_hashes)
    merkle_root = levels[-1][0]

    merkle_tree = {
        "version": "1.0",
        "leaf_count": len(leaf_hashes),
        "merkle_root": merkle_root,
        "levels": levels,
    }

    checkpoint = {
        "version": "1.0",
        "type": "transparency_checkpoint",
        "entry_count": len(entries),
        "merkle_root": merkle_root,
    }

    transparency_log_path = output_dir / "transparency_log.json"
    merkle_tree_path = output_dir / "merkle_tree.json"
    root_txt_path = output_dir / "root.txt"
    checkpoint_path = output_dir / "checkpoint.json"

    transparency_log_path.write_text(
        json.dumps(transparency_log, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    merkle_tree_path.write_text(
        json.dumps(merkle_tree, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    root_txt_path.write_text(merkle_root + "\n", encoding="utf-8")
    checkpoint_path.write_text(
        json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    for i, entry in enumerate(entries):
        proof = {
            "version": "1.0",
            "type": "inclusion_proof",
            "entry": entry,
            "leaf_hash": leaf_hashes[i],
            "merkle_root": merkle_root,
            "proof": build_inclusion_proof(levels, i),
        }

        safe_name = entry["path"].replace("/", "__")
        proof_path = proofs_dir / f"{safe_name}.proof.json"
        proof_path.write_text(
            json.dumps(proof, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"[OK] wrote: {transparency_log_path}")
    print(f"[OK] wrote: {merkle_tree_path}")
    print(f"[OK] wrote: {root_txt_path}")
    print(f"[OK] wrote: {checkpoint_path}")
    print(f"[OK] wrote proofs: {proofs_dir}")
    print(f"[OK] merkle_root: {merkle_root}")
    print(f"[OK] entry_count: {len(entries)}")


if __name__ == "__main__":
    main()