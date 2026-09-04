#!/usr/bin/env python3
"""
CLI for ISTH DIC (Disseminated Intravascular Coagulation) Score Calculator.

Usage:
  python cli.py overt --platelets 80 --fibrin-marker moderate_increase --pt-prolongation 4 --fibrinogen 1.5
  python cli.py non-overt --platelets 90 --fibrin-marker moderate_increase --pt-prolongation 3 --fibrinogen 1.2 --platelet-trend falling
  python cli.py context --context sepsis --dic-score 6
  python cli.py batch -i input.csv -o results.csv
  python cli.py audit --task-id TASK-001
  python cli.py chat <query>
  python cli.py verify-audit
"""
import argparse
import json
import sys

from dic_istn import (
    calculate_overt_dic_score,
    calculate_non_overt_dic_score,
    assess_clinical_context,
    process_batch,
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="dic-score",
        description="ISTH DIC (Disseminated Intravascular Coagulation) Score Calculator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Overt DIC
    overt = subparsers.add_parser("overt", help="Calculate ISTH Overt DIC Score")
    overt.add_argument("--platelets", type=float, required=True, help="Platelet count (×10³/µL)")
    overt.add_argument("--fibrin-marker", required=True,
                       help="Fibrin marker: no_increase, moderate_increase, strong_increase (or numeric fold)")
    overt.add_argument("--pt-prolongation", type=float, required=True, help="PT prolongation (seconds above normal)")
    overt.add_argument("--fibrinogen", type=float, required=True, help="Fibrinogen (g/L)")

    # Non-Overt DIC
    non_overt = subparsers.add_parser("non-overt", help="Calculate ISTH Non-Overt DIC Score")
    non_overt.add_argument("--platelets", type=float, required=True, help="Platelet count (×10³/µL)")
    non_overt.add_argument("--fibrin-marker", required=True, help="Fibrin marker level")
    non_overt.add_argument("--pt-prolongation", type=float, required=True, help="PT prolongation (seconds)")
    non_overt.add_argument("--fibrinogen", type=float, required=True, help="Fibrinogen (g/L)")
    non_overt.add_argument("--platelet-trend", choices=["rising", "falling"], default=None)
    non_overt.add_argument("--fibrinogen-trend", choices=["rising", "falling"], default=None)
    non_overt.add_argument("--d-dimer-trend", choices=["rising", "falling"], default=None)

    # Clinical context
    ctx = subparsers.add_parser("context", help="Get clinical context guidance")
    ctx.add_argument("--context", required=True,
                     help="Clinical context: sepsis, trauma, obstetric, malignancy, snakebite")
    ctx.add_argument("--dic-score", type=int, required=True, help="DIC total score")

    # Batch
    batch = subparsers.add_parser("batch", help="Batch process CSV")
    batch.add_argument("-i", "--input", required=True, help="Input CSV")
    batch.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    # Audit
    audit_parser = subparsers.add_parser("audit", help="Run audit task evaluation")
    audit_parser.add_argument("--task-id", required=True, help="Task identifier for audit")

    # Chat
    chat_parser = subparsers.add_parser("chat", help="Query the LLM reasoning adapter")
    chat_parser.add_argument("query", nargs=argparse.REMAINDER, help="Query text for the LLM")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    args = parser.parse_args(argv)

    if args.command == "overt":
        result = calculate_overt_dic_score(
            args.platelets, args.fibrin_marker, args.pt_prolongation, args.fibrinogen,
        )
        print(json.dumps(result, indent=2))
        return 0

    elif args.command == "non-overt":
        result = calculate_non_overt_dic_score(
            args.platelets, args.fibrin_marker, args.pt_prolongation, args.fibrinogen,
            platelet_trend=args.platelet_trend,
            fibrinogen_trend=args.fibrinogen_trend,
            d_dimer_trend=args.d_dimer_trend,
        )
        print(json.dumps(result, indent=2))
        return 0

    elif args.command == "context":
        result = assess_clinical_context(args.context, args.dic_score)
        print(json.dumps(result, indent=2))
        return 0

    elif args.command == "batch":
        n = process_batch(args.input, args.output)
        print(f"Processed {n} records -> {args.output}")
        return 0

    elif args.command == "audit":
        from agents.supervisor import SystemSupervisor
        from agents.models import SystemTaskPayload
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier="AUDIT-TASK",
            primary_metric=12.0,
            secondary_metric=4.0,
            status_descriptor="NOMINAL",
        )
        dossier = supervisor.process_task(payload)
        print(json.dumps(dossier.to_dict(), indent=2, default=str))
        return 0

    elif args.command == "chat":
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query) if args.query else ""
        response = supervisor.query_supervisory_chat(query)
        print(json.dumps({"query": query, "response": response}, indent=2))
        return 0

    elif args.command == "verify-audit":
        from agents.base import AuditLogger
        valid = AuditLogger.verify_integrity()
        trail_len = len(AuditLogger.get_trail())
        print(json.dumps({"audit_valid": valid, "trail_length": trail_len}, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
