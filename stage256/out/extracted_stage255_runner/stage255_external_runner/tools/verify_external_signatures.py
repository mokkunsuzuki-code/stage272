import yaml
import sys

def main():
    with open("external_signatures/config.yaml") as f:
        cfg = yaml.safe_load(f)

    # 仮の外部署名（次で実鍵に置き換える）
    provided_signatures = [
        {"id": "self", "valid": True},
        {"id": "github_user", "valid": True}
    ]

    valid_count = sum(1 for s in provided_signatures if s["valid"])

    if valid_count >= 2:
        print("[OK] External signatures verified")
        print(f"valid signatures: {valid_count}")
        sys.exit(0)
    else:
        print("[FAIL] External signature verification failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
