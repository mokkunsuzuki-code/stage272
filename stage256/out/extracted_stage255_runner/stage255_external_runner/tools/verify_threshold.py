import yaml
import sys

def main():
    with open("threshold/config.yaml") as f:
        cfg = yaml.safe_load(f)

    required = cfg["threshold_policy"]["required_signers"]
    total = cfg["threshold_policy"]["total_signers"]

    # 仮：署名済みリスト（後で実署名に置き換え）
    provided_signatures = ["self", "reviewer"]  # ←ここを変えるとテストできる

    if len(provided_signatures) >= required:
        print("[OK] Threshold satisfied")
        print(f"required: {required}, provided: {len(provided_signatures)}")
        sys.exit(0)
    else:
        print("[FAIL] Threshold NOT satisfied")
        sys.exit(1)

if __name__ == "__main__":
    main()
