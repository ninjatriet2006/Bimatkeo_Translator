import json

with open("plan.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# Update PROJECT_STATUS cell
cell_0 = nb["cells"][0]["source"]
for i, line in enumerate(cell_0):
    if '"Phase 2: Decoupled Process Isolation": "Hoàn thành",' in line:
        cell_0.insert(i, '        "Phase 1.5: Core Code Optimization (AI Agent Skills)": "Hoàn thành",\n')
        break

# Update Markdown cell
cell_2 = nb["cells"][2]["source"]

mermaid_injection = """  %% 1.5 AI Skills
  Root --> Skill(Thiết lập AI Agent Skills):::done
  Skill --> skill1[Modern Python & Pytest]:::done
  Skill --> skill2[Bảo mật & Decoupling]:::done
  
"""

table_injection = """| **Phase 1.5: Core Code Optimization**<br>*(Chuẩn hóa Mã Nguồn)* | **Bộ kỹ năng AI Agent:**<br>• `modern-python` (Cú pháp Python 3.10+, Type Hinting gắt gao).<br>• `pytest-skill` (Testability, loại bỏ phụ thuộc cứng).<br>• `security-best-practices` (Quản lý SSL, tránh rò rỉ Key).<br>• `ask-questions` (Chặn ảo giác, yêu cầu làm rõ trước khi code). | • Áp dụng `match/case` loại bỏ if/else dài.<br>• Refactor toàn bộ utils. | 🟢 **Hoàn thành 100%** |
"""

for i, line in enumerate(cell_2):
    if "Root --> Core(Kiến trúc Lõi)" in line:
        cell_2.insert(i, mermaid_injection)
        break

for i, line in enumerate(cell_2):
    if "| **Phase 1: UI & Config**" in line:
        cell_2.insert(i+1, table_injection)
        break

nb["cells"][0]["source"] = cell_0
nb["cells"][2]["source"] = cell_2

with open("plan.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
