#!/usr/bin/env python3
import os
import sys
import pymysql

TABLES = [
    "bajaj_auto",
    "eicher_motors",
    "hero_motocorp",
    "infosys",
    "tcs",
    "tvs_motors",
]


def load_env(env_path):
    env = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    return env


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env = load_env(os.path.join(script_dir, ".env"))

    host = env.get("MYSQL_HOST", "127.0.0.1")
    port = int(env.get("MYSQL_PORT", 3306))
    user = env.get("MYSQL_USER", "root")
    password = env.get("MYSQL_ROOT_PASSWORD", "")
    database = sys.argv[1] if len(sys.argv) > 1 else env.get("MYSQL_DATABASE", "stock_analysis")

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        cursorclass=pymysql.cursors.Cursor,
    )

    all_passed = True
    try:
        with conn.cursor() as cursor:
            for table in TABLES:
                print("=" * 60)
                print(f"Table: {table}")

                cursor.execute(f"SELECT COUNT(*), MIN(date), MAX(date) FROM {table};")
                row_count, min_date, max_date = cursor.fetchone()
                print(f"  Row Count : {row_count} (Expect: 889)")
                print(f"  MIN(date) : {min_date} (Expect: 2015-01-01)")
                print(f"  MAX(date) : {max_date} (Expect: 2018-07-31)")

                if row_count != 889 or str(min_date) != "2015-01-01" or str(max_date) != "2018-07-31":
                    all_passed = False

                # Get columns
                cursor.execute(f"SHOW COLUMNS FROM {table};")
                columns = [row[0] for row in cursor.fetchall()]

                print("  NULL counts per column:")
                for col in columns:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE `{col}` IS NULL;")
                    cnt = cursor.fetchone()[0]
                    expected_null = 1 if col in ("deliverable_qty", "pct_deli_qty") else 0
                    status = "OK" if cnt == expected_null else f"MISMATCH (expected {expected_null})"
                    if cnt != expected_null:
                        all_passed = False
                    print(f"    - {col}: {cnt} [{status}]")

            # Check bajaj_auto close on 2018-07-31
            print("=" * 60)
            cursor.execute("SELECT close_price FROM bajaj_auto WHERE date = '2018-07-31';")
            bajaj_close = cursor.fetchone()[0]
            print(f"bajaj_auto close on 2018-07-31: {bajaj_close:.2f} (Expect: 2700.70)")
            if abs(float(bajaj_close) - 2700.70) > 0.001:
                all_passed = False

        if all_passed:
            print("\nALL LOAD CHECKS PASSED!")
        else:
            print("\nSOME LOAD CHECKS FAILED!")
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
