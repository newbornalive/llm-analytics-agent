import argparse
import json
from pathlib import Path
from .workflow import run_analysis
from .chart import render_svg

def main():
    parser = argparse.ArgumentParser(description="Guarded channel-conversion analytics")
    parser.add_argument("question", nargs="?", default="Compare conversion rates by channel")
    parser.add_argument("--mode", choices=["demo", "openai"], default="demo")
    parser.add_argument("--db", type=Path, default=Path("data/marketing.db"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--svg", type=Path)
    args = parser.parse_args()
    try:
        report = run_analysis(args.question, args.db, args.mode)
        text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        if args.svg:
            args.svg.parent.mkdir(parents=True, exist_ok=True)
            args.svg.write_text(render_svg(report), encoding="utf-8")
        print(text)
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")

if __name__ == "__main__":
    main()
