"""
GatePass - Data Analysis Module
================================
Reads and analyzes outpass records from CSV (simulated benchmark dataset)
or directly from the live application database.

NOTE: All dataset records provided here are SYNTHETIC DEMO DATA generated
for algorithm testing, system verification, and demonstration purposes.
They DO NOT represent real-world student records or field observations.
"""

import os
import csv
from datetime import datetime
from collections import defaultdict
from config import Config

def parse_csv_datetime(dt_str):
    """Safely parse datetime from CSV."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    return None

def analyze_outpass_csv(csv_path="data.csv"):
    """
    Parse outpass CSV file and compute analytical metrics:
      - Total records
      - Status distribution (Approved, Rejected, Pending, Outside, Completed)
      - Late return statistics
      - Average outpass duration in hours/minutes
      - Gate traffic distribution (Exit vs Entry per gate)
      - Peak departure hours
    """
    if not os.path.exists(csv_path):
        return {
            "error": f"File '{csv_path}' not found.",
            "is_synthetic": True
        }

    total_records = 0
    status_counts = defaultdict(int)
    program_counts = defaultdict(int)
    gate_exit_counts = defaultdict(int)
    gate_entry_counts = defaultdict(int)
    late_count = 0
    total_duration_minutes = 0
    completed_with_duration = 0
    destination_counts = defaultdict(int)
    records = []

    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_records += 1
                status = row.get("status", "UNKNOWN").upper()
                status_counts[status] += 1
                
                prog = row.get("program", "Unknown")
                program_counts[prog] += 1
                
                dest = row.get("destination", "Other")
                destination_counts[dest] += 1

                exit_gate = row.get("exit_gate")
                if exit_gate and exit_gate != "-":
                    gate_exit_counts[exit_gate] += 1

                entry_gate = row.get("entry_gate")
                if entry_gate and entry_gate != "-":
                    gate_entry_counts[entry_gate] += 1

                # Late check from CSV
                is_late_val = str(row.get("is_late", "False")).strip().lower()
                if is_late_val in ("true", "1", "yes"):
                    late_count += 1

                # Calculate duration if exit and entry exist
                exit_time = parse_csv_datetime(row.get("exit_time"))
                entry_time = parse_csv_datetime(row.get("entry_time"))
                if exit_time and entry_time and entry_time > exit_time:
                    dur = int((entry_time - exit_time).total_seconds() // 60)
                    total_duration_minutes += dur
                    completed_with_duration += 1
                    
                records.append(row)
    except Exception as e:
        return {"error": f"Failed to parse CSV: {str(e)}", "is_synthetic": True}

    avg_duration_minutes = (
        round(total_duration_minutes / completed_with_duration, 1)
        if completed_with_duration > 0
        else 0
    )
    avg_hours = int(avg_duration_minutes // 60)
    avg_mins = int(avg_duration_minutes % 60)

    # Gate traffic aggregation
    all_gates = sorted(list(set(list(gate_exit_counts.keys()) + list(gate_entry_counts.keys()))))
    gate_activity = []
    for g in all_gates:
        exits = gate_exit_counts.get(g, 0)
        entries = gate_entry_counts.get(g, 0)
        gate_activity.append({
            "gate": g,
            "exits": exits,
            "entries": entries,
            "total": exits + entries
        })

    late_percentage = round((late_count / total_records * 100), 1) if total_records > 0 else 0

    return {
        "is_synthetic": True,
        "dataset_notice": "SYNTHETIC DEMO DATASET - Fictional development records for take-home assignment testing.",
        "total_records": total_records,
        "status_counts": dict(status_counts),
        "program_counts": dict(program_counts),
        "late_returns_count": late_count,
        "late_return_percentage": late_percentage,
        "completed_count": status_counts.get("COMPLETED", 0),
        "outside_count": status_counts.get("OUTSIDE", 0),
        "approved_count": status_counts.get("APPROVED", 0),
        "rejected_count": status_counts.get("REJECTED", 0),
        "pending_count": status_counts.get("PENDING", 0),
        "avg_duration_minutes": avg_duration_minutes,
        "avg_duration_formatted": f"{avg_hours}h {avg_mins}m",
        "gate_activity": gate_activity,
        "top_destinations": sorted(destination_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        "sample_records": records[:10]
    }

def print_cli_report(csv_path="data.csv"):
    """Format and print an administrative analysis report to console."""
    results = analyze_outpass_csv(csv_path)
    if "error" in results:
        print(f"Error: {results['error']}")
        return

    print("=" * 65)
    print("GATEPASS - HOSTEL OUTPASS MANAGEMENT SYSTEM")
    print("DEMONSTRATION ANALYTICS REPORT (from data.csv)")
    print("=" * 65)
    print(f"DATASET PROVENANCE: {results['dataset_notice']}")
    print("-" * 65)
    print(f"Total Outpass Records Analyzed : {results['total_records']}")
    print(f"  - Completed Journeys         : {results['completed_count']}")
    print(f"  - Currently Outside Campus   : {results['outside_count']}")
    print(f"  - Approved (Ready to Exit)   : {results['approved_count']}")
    print(f"  - Rejected Requests          : {results['rejected_count']}")
    print(f"  - Pending Warden Review      : {results['pending_count']}")
    print("-" * 65)
    print(f"Late Returns Identified        : {results['late_returns_count']} ({results['late_return_percentage']}%)")
    print(f"Average Outpass Duration       : {results['avg_duration_formatted']} ({results['avg_duration_minutes']} mins)")
    print("-" * 65)
    print("Gate-wise Movement Traffic:")
    for ga in results["gate_activity"]:
        print(f"  {ga['gate']:<10}: Exits = {ga['exits']:<3} | Entries = {ga['entries']:<3} | Total = {ga['total']}")
    print("-" * 65)
    print("Student Program Breakdown:")
    for prog, count in results["program_counts"].items():
        print(f"  {prog:<10}: {count} requests")
    print("=" * 65)

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    print_cli_report(path)
