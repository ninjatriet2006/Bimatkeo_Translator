#!/bin/bash
# Lấy thư mục chứa file script này
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Khởi chạy ứng dụng PySide6 với python trong venv (Kiến trúc mới)
.venv/bin/python app/core/desktop/main.py
