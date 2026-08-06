import os

def analyze_project(root_dir):
    summary = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        rel_dir = os.path.relpath(dirpath, root_dir)
        if rel_dir == ".":
            rel_dir = ""
        summary.append(f"\n📂 {rel_dir if rel_dir else root_dir}")
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            try:
                size = os.path.getsize(fpath)
                if size == 0:
                    status = "empty"
                else:
                    # Peek first 200 chars to see if scaffolded or logic
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        head = f.read(200)
                    if "class" in head or "function" in head or "import" in head:
                        status = "contains logic"
                    else:
                        status = "scaffolded"
                summary.append(f"  - {fname} [{status}] ({size} bytes)")
            except Exception as e:
                summary.append(f"  - {fname} [error: {e}]")
    return "\n".join(summary)

if __name__ == "__main__":
    root = os.getcwd()
    print(f"--- Project Analysis for {root} ---")
    print(analyze_project(root))
