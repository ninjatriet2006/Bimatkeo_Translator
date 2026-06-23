import json

with open('plan.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Update Cell 0 (Metadata)
cell_0 = nb['cells'][0]
src_0 = "".join(cell_0['source'])

old_lines = """current_phase_key = PROJECT_STATUS['current_phase']
print(f"Trạng thái hiện tại: {current_phase_key} - {PROJECT_STATUS['phases'][current_phase_key]}")"""

new_lines = """current_phase_key = PROJECT_STATUS['current_phase']
status_desc = PROJECT_STATUS['phases'].get(current_phase_key, "Tiến hành song song các nhánh")
print(f"Trạng thái hiện tại: {current_phase_key} - {status_desc}")"""

src_0 = src_0.replace(old_lines, new_lines)

cell_0['source'] = src_0.splitlines(True)

with open('plan.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook cell 0 fixed.")
