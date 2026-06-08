#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


def normalize(value):
    if value is None:
        return ""
    v = str(value).strip()
    if v == "":
        return ""

    # normalize hex
    if v.lower().startswith("0x"):
        try:
            return hex(int(v, 16))
        except ValueError:
            return v.lower()

    # normalize integers
    try:
        return str(int(v))
    except ValueError:
        pass

    # normalize floats like 1.0 vs 1
    try:
        f = float(v)
        if f.is_integer():
            return str(int(f))
        return format(f, ".15g")
    except ValueError:
        pass

    return v


def read_csv_rows(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")

        fieldnames = [h.strip() for h in reader.fieldnames]
        rows = []
        for row in reader:
            norm = {k.strip(): normalize(v) for k, v in row.items()}
            rows.append(norm)
        return fieldnames, rows


def list_csvs(base_dir):
    base = Path(base_dir).resolve()
    return {
        p.resolve().relative_to(base).as_posix(): p.resolve()
        for p in base.rglob("*.csv")
        if p.is_file()
    }


def compare_csvs(left_path, right_path, rel_path, max_diffs_per_file=20):
    try:
        left_cols, left_rows = read_csv_rows(left_path)
        right_cols, right_rows = read_csv_rows(right_path)
    except Exception as e:
        print(f"[FAIL] {rel_path}")
        print(f"       Error reading CSV: {e}")
        return False

    ok = True

    left_col_set = set(left_cols)
    right_col_set = set(right_cols)

    if left_col_set != right_col_set:
        ok = False
        print(f"[FAIL] {rel_path}")
        print("       Column mismatch")
        print(f"       Emulator-Output-directory : {sorted(left_col_set)}")
        print(f"       Firmware-Output-directory: {sorted(right_col_set)}")
        return False

    if len(left_rows) != len(right_rows):
        ok = False
        print(f"[FAIL] {rel_path}")
        print("       Row count mismatch")
        print(f"       Emulator-Output-directory : {len(left_rows)}")
        print(f"       Firmware-Output-directory: {len(right_rows)}")
        # continue comparing overlapping rows

    ordered_cols = [c for c in left_cols if c in right_col_set]
    n_common = min(len(left_rows), len(right_rows))

    diff_count = 0
    for i in range(n_common):
        lrow = left_rows[i]
        rrow = right_rows[i]
        for col in ordered_cols:
            lv = lrow.get(col, "")
            rv = rrow.get(col, "")
            if lv != rv:
                if diff_count == 0:
                    print(f"[FAIL] {rel_path}")
                diff_count += 1
                print(f"       row={i}, column={col}")
                print(f"       Emulator-Output-directory : {lv}")
                print(f"       Firmware-Output-directory: {rv}")
                if diff_count >= max_diffs_per_file:
                    print(f"       ... stopping after {max_diffs_per_file} differences")
                    return False
                ok = False

    if ok:
        print(f"[OK] {rel_path}")

    return ok


def main():
    if len(sys.argv) != 3:
        print("Usage: compare.py <Emulator-Output-directory> <Firmware-Output-directory>")
        sys.exit(1)

    left_dir = Path(sys.argv[1]).resolve()
    right_dir = Path(sys.argv[2]).resolve()

    if not left_dir.is_dir():
        print(f"Emulator-Output-directory is not a directory: {left_dir}")
        sys.exit(1)
    if not right_dir.is_dir():
        print(f"Firmware-Output-directory is not a directory: {right_dir}")
        sys.exit(1)

    left_csvs = list_csvs(left_dir)
    right_csvs = list_csvs(right_dir)

    left_keys = set(left_csvs.keys())
    right_keys = set(right_csvs.keys())

    only_left = sorted(left_keys - right_keys)
    only_right = sorted(right_keys - left_keys)
    common = sorted(left_keys & right_keys)

    all_ok = True

    if only_left:
        all_ok = False
        print("[FAIL] CSVs only in Emulator-Output-directory:")
        for rel in only_left:
            print(f"       {rel}")

    if only_right:
        all_ok = False
        print("[FAIL] CSVs only in Firmware-Output-directory:")
        for rel in only_right:
            print(f"       {rel}")

    for rel in common:
        ok = compare_csvs(left_csvs[rel], right_csvs[rel], rel)
        all_ok = all_ok and ok

    print()
    print(f"Emulator-Output-directory directory : {left_dir}")
    print(f"Firmware-Output-directory directory: {right_dir}")
    print(f"Common CSVs    : {len(common)}")
    print(f"Only in Emulator-Output-directory   : {len(only_left)}")
    print(f"Only in Firmware-Output-directory  : {len(only_right)}")

    if all_ok:
        print("\nAll matched.")
        sys.exit(0)
    else:
        print("\nDifferences found.")
        sys.exit(2)


if __name__ == "__main__":
    main()