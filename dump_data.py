import io

with io.open('old_app.py', 'r', encoding='utf-16le', errors='ignore') as f:
    lines = f.readlines()

with io.open('dump_data.txt', 'w', encoding='utf-8') as f:
    for i, line in enumerate(lines[410:650]):
        f.write(f"{i + 410}: {line}")
