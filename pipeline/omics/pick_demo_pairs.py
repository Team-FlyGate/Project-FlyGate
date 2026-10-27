"""시연 쌍을 추출 파일에서 고릅니다. 기억이 아니라 데이터로 고르기 위한 스크립트입니다.

정직한 음성: 니라파립-혈소판감소증. 두 표적 모두 안전성 책임 기록이 없고 문헌 제외 연관 점수가 0 인지 확인합니다.
양성 후보: safety_match 에 relation=term 이 있고 L4 의 문헌 제외 점수가 0 보다 큰 쌍을, 표적 수가 적은 약부터 정렬해 냅니다.
SignalLab 프리셋 약은 앞에 표시합니다.

사용: python3 -m pipeline.omics.pick_demo_pairs [api/_data/omics.json.gz]
"""
import gzip
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PRESETS = {"NIRAPARIB", "SEMAGLUTIDE", "TIRZEPATIDE", "DUPILUMAB", "METFORMIN", "CANAGLIFLOZIN", "PEMBROLIZUMAB",
           "ADALIMUMAB", "MONTELUKAST", "LEVOFLOXACIN", "ISOTRETINOIN"}


def main(path: pathlib.Path) -> None:
    with gzip.open(path, "rt") as f:
        o = json.load(f)
    neg = o["pairs"].get("NIRAPARIB|thrombocytopenia")
    tg = [o["targets"][t] for t in o["drugs"]["NIRAPARIB"]["targets"]]
    print("honest negative NIRAPARIB|thrombocytopenia:",
          {"safety": [t["safety"] for t in tg], "assoc": neg and neg["assoc"], "mapping": neg and o["terms"][neg["term"]]["match"]})
    rows = []
    for key, p in o["pairs"].items():
        drug, pt = key.split("|", 1)
        terms_match = [m for m in p.get("safety_match") or [] if m["relation"] == "term"]
        a = p.get("assoc") or {}
        if not terms_match or not (a.get("score_no_literature") or 0) > 0:
            continue
        n_targets = len(o["drugs"][drug]["targets"])
        ev = [(o["targets"][m["target"]]["symbol"], o["targets"][m["target"]]["safety"][m["index"]]) for m in terms_match]
        rows.append((drug not in PRESETS, n_targets, -a["score_no_literature"], drug, pt, ev, a))
    rows.sort()
    print(f"positive candidates: {len(rows)} (relation=term and no-literature score > 0)")
    for _, n, _, drug, pt, ev, a in rows[:15]:
        liab = "; ".join(f"{s}: {l['event']} [{l['event_id']}] src={l['datasource']} pmid={l['pmid']}" for s, l in ev)
        print(f"  {drug}|{pt}  targets={n}  score={a['score']}  no_lit={a['score_no_literature']}  {liab}")


if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "api" / "_data" / "omics.json.gz")
