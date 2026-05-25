import subprocess


def reset_db():
    subprocess.run(["uv", "run", "setup"], check=True)


def main():
    print("\n", "=" * 80, sep="")
    print("Test 1".center(80))
    print("=" * 80)
    reset_db()
    subprocess.run(["node", "src/tests/stress_test_1.js"], check=True)
    print("\n", "=" * 80, sep="")
    print("Test 2".center(80))
    print("=" * 80)
    reset_db()
    subprocess.run(["node", "src/tests/stress_test_2.js"], check=True)
    print("\n", "=" * 80, sep="")
    print("Test 3".center(80))
    print("=" * 80)
    reset_db()
    subprocess.run(["node", "src/tests/stress_test_3.js"], check=True)


if __name__ == "__main__":
    main()
