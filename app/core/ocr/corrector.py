"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.corrector
- RESPONSIBILITY: Sử dụng Heuristics, Regex và Từ điển để sửa các lỗi OCR phổ biến.
- CALLED BY: app.core.ocr.local_runner
- CALLS TO: None
- IN = OUT: Độc lập logic, nhận văn bản lỗi -> trả về văn bản đã sửa.
=============================================================================
"""

import numpy as np
import re

class OfflineOCRCorrector:
    """
    Offline Pipeline for OCR Correction.
    Sử dụng Regex và Heuristics để tự động nắn lại các lỗi chính tả phổ biến của OCR
    mà không cần gọi API LLM. Được chia thành nhiều Stage để quản lý luồng xử lý sạch sẽ.
    """
    def __init__(self, log_callback=None, aggressive_level=1):
        self.log_callback = log_callback
        self.aggressive_level = aggressive_level
        
        # Từ điển các từ thường xuyên bị nhận diện sai toàn bộ
        self.glossary = {
            "0nly": "Only",
            "0NLY": "ONLY",
            "1l": "ll",
            "rnother": "mother",
            "lI": "ll",
            "rneturn": "return"
        }

    def _normalize_spaces(self, text: str) -> str:
        """Stage 1: Dọn dẹp khoảng trắng dư thừa và ký tự rác"""
        # Xóa nhiều khoảng trắng liên tiếp
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _fix_punctuation(self, text: str) -> str:
        """Stage 1.5: Chuẩn hóa dấu câu"""
        # Fix .. . thành ...
        text = re.sub(r'\.\.+', '...', text)
        text = re.sub(r'\.\s+\.', '...', text)
        # Fix hai dấu phẩy liên tiếp
        text = re.sub(r',+', ',', text)
        text = re.sub(r',\s+,', ',', text)
        return text

    def _apply_glossary(self, text: str) -> str:
        """Stage 2: Thay thế theo từ điển (Hardcoded Mapping)"""
        # Duyệt qua từng cặp từ điển để fix (có thể phát triển thành tìm kiếm theo Word Boundary)
        for wrong, correct in self.glossary.items():
            # Chỉ thay thế nếu nó đứng như một từ độc lập hoặc dính liền vẫn an toàn
            # Dùng regex \b để match ranh giới từ, tránh thay thế nhầm chữ bên trong từ khác
            pattern = r'\b' + re.escape(wrong) + r'\b'
            text = re.sub(pattern, correct, text, flags=re.IGNORECASE)
        return text

    def _apply_regex_rules(self, text: str) -> str:
        """Stage 3: Sửa lỗi nhầm l/I/1, O/0, rn/m bằng Regex dựa theo bối cảnh"""
        
        # 1. Sửa lỗi số 0 kẹp giữa các chữ cái (Ví dụ: c0ntent -> content, H0W -> HOW)
        # Nếu số 0 đứng giữa 2 chữ cái A-Z, nó chắc chắn là chữ O
        text = re.sub(r'([A-Za-z])0([A-Za-z])', r'\1O\2', text)
        # Bắt thêm trường hợp H0w (Chữ o thường)
        text = re.sub(r'([A-Za-z])0([a-z])', r'\1o\2', text)
        
        # 2. Sửa chữ I in hoa nằm giữa các chữ thường (Ví dụ: chIld -> child, wIll -> will)
        # Trong tiếng Anh hiếm có từ nào kẹp I in hoa ở giữa (trừ CamelCase)
        text = re.sub(r'([a-z])I([a-z])', r'\1l\2', text)
        
        # 3. Sửa số 1 nằm giữa các chữ cái (Ví dụ: on1y -> only, wi11 -> will)
        text = re.sub(r'([A-Za-z])1([a-z])', r'\1l\2', text)
        text = re.sub(r'([a-z])1([A-Za-z])', r'\1l\2', text)
        
        # 4. Sửa 'rn' thành 'm' nếu kẹp giữa từ (rất hay gặp trong manga OCR)
        # Ví dụ: cornputer -> computer, rnother -> mother
        text = re.sub(r'([a-z])rn([a-z])', r'\1m\2', text)
        
        return text

    def _clean_mixed_garbage(self, text: str) -> str:
        """Stage 4: Loại bỏ Hán tự/Rác bị dính vào câu tiếng Anh"""
        cjk_pattern = r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]'
        cjk_chars = re.findall(cjk_pattern, text)
        
        eng_pattern = r'[A-Za-z]'
        eng_chars = re.findall(eng_pattern, text)
        
        # Nếu câu chủ yếu là tiếng Anh (hơn 5 ký tự) và có một ít chữ Hán (có thể do background bị dính)
        if len(eng_chars) > 5 and len(cjk_chars) > 0 and len(eng_chars) > len(cjk_chars) * 2:
            return re.sub(cjk_pattern, '', text).strip()
        return text

    def _apply_spellcheck(self, text: str) -> str:
        """Stage 5: Dùng pyspellchecker để nắn lại các từ tiếng Anh (Ví dụ: 5EX -> SEX)"""

            
        # Dùng regex để đếm số ký tự Latin thay vì langdetect vì langdetect hay sai với từ ngắn (như WARNINE)
        eng_chars = len(re.findall(r'[A-Za-z]', text))
        if len(text) > 0 and eng_chars / len(text) < 0.2:
            return text
            
            
        try:
            from spellchecker import SpellChecker
            if not hasattr(self, 'spell'):
                self.spell = SpellChecker()
                
            def correct_word(match):
                word = match.group(0)
                # Bỏ qua từ quá ngắn
                if len(word) < 3:
                    return word
                
                # Heuristic OCR: Thử thay thế số bằng chữ cái tương tự nếu từ bị lẫn lộn số và chữ
                if not word.isnumeric() and any(char.isdigit() for char in word):
                    potential_word = word.replace('5', 'S').replace('0', 'O').replace('1', 'I').replace('8', 'B')
                    if self.spell.known([potential_word.lower()]):
                        # Nếu từ tiềm năng (sau khi thay số bằng chữ) là có nghĩa, ta ưu tiên dùng nó
                        word = potential_word
                elif word.isnumeric():
                    # Bỏ qua từ chỉ có số
                    return word
                
                # Bỏ qua từ viết hoa viết thường lộn xộn kiểu CamelCase
                if not word.isupper() and not word.islower() and not word.istitle():
                    return word
                    
                c = self.spell.correction(word)
                if c:
                    if word.isupper():
                        return c.upper()
                    elif word.istitle():
                        return c.capitalize()
                    return c
                return word
                
            # Bảo vệ các URL bằng cách bóc tách ra trước khi quét chính tả
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, text)
            
            # Thay thế URL bằng placeholder
            for i, url in enumerate(urls):
                text = text.replace(url, f"__URL_PLACEHOLDER_{i}__")
                
            # Quét các cụm chữ và số dính nhau (Ví dụ: 5EX, 0nly)
            text = re.sub(r'\b[A-Za-z0-9]+\b', correct_word, text)
            
            # Phục hồi URL
            for i, url in enumerate(urls):
                text = text.replace(f"__URL_PLACEHOLDER_{i}__", url)
                
            return text
        except ImportError:
            # Nếu chưa cài pyspellchecker thì an toàn bỏ qua
            return text

    def correct(self, original_texts: list[str], full_image: np.ndarray | None = None) -> list[str]:
        """
        Nhạc trưởng (Coordinator): Dẫn dắt từng dòng text đi qua quy trình Pipeline.
        """
        if not original_texts:
            return original_texts
            
        if self.log_callback:
            self.log_callback("INFO", "Kích hoạt Offline OCR Corrector Pipeline (Heuristics + SpellChecker)...")
            
        corrected_texts = []
        for text in original_texts:
            if not text.strip():
                corrected_texts.append(text)
                continue
                
            original = text
            
            # Chạy qua dây chuyền 4 bước
            text = self._normalize_spaces(text)
            text = self._fix_punctuation(text)
            text = self._apply_glossary(text)
            text = self._apply_regex_rules(text)
            text = self._clean_mixed_garbage(text)
            text = self._apply_spellcheck(text)

            
            # Ghi lại log nếu có sự thay đổi để debug
            if original != text and self.log_callback:
                self.log_callback("DEBUG", f"OCR Fixed: '{original}' -> '{text}'")
                
            corrected_texts.append(text)
                
        if self.log_callback:
            self.log_callback("SUCCESS", "Hoàn thành sửa lỗi OCR Offline.")
            
        return corrected_texts
