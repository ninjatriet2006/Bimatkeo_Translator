import threading
import queue
import fnmatch
import re
from app.core.dto import PageContext

try:
    from langdetect import detect
except ImportError:
    detect = None

class TranslatorWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, translator_or_chain, src_lang: str, tgt_lang: str, log_callback=None, hitl_callback=None, skip_languages=None, filter_texts=None, no_text_lang_skip=False, max_request_length=-1, editor_translator=None, context_window=10, stride_window=5):
        super().__init__()
        self.in_q = in_q
        
        # Determine if we have a single translator or a chain
        if isinstance(translator_or_chain, list):
            self.chained_translators = translator_or_chain
        else:
            self.chained_translators = [(translator_or_chain, tgt_lang)] if translator_or_chain else []
            
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.log_callback = log_callback
        self.skip_languages = skip_languages or {}
        self.filter_texts = filter_texts or []
        self.no_text_lang_skip = no_text_lang_skip
        self.max_request_length = max_request_length
        
        self.editor_translator = editor_translator
        self.context_window = max(1, context_window)
        self.stride_window = max(1, stride_window)
        self.daemon = True

    def _should_skip_text(self, text, current_tgt_lang):
        if not text or not text.strip():
            return True
            
        # 1. Filter texts check
        for pattern in self.filter_texts:
            pattern = str(pattern).strip()
            if not pattern: continue
            # Regex match
            if pattern.startswith('/') and pattern.endswith('/'):
                regex = pattern[1:-1]
                try:
                    if re.search(regex, text):
                        return True
                except re.error:
                    pass
            # Exact match
            elif pattern.startswith('"') and pattern.endswith('"'):
                if text == pattern[1:-1]:
                    return True
            # Wildcard / Substring match
            else:
                if fnmatch.fnmatch(text, pattern) or pattern in text:
                    return True

        # 2. Language detect check
        if detect and (self.skip_languages or not self.no_text_lang_skip):
            try:
                detected_lang = detect(text).upper()
                
                # Check skip languages
                # Some codes from langdetect need to be mapped if needed, but we'll do direct match
                if self.skip_languages.get(detected_lang, False):
                    return True
                
                # Check translate same language
                if not self.no_text_lang_skip and detected_lang == current_tgt_lang.upper()[:2]:
                    return True
            except Exception:
                pass # langdetect might throw LangDetectException if no features

        return False

    def run(self):
        stage1_buffer = []
        stage2_buffer = []
        
        window_size1 = self.context_window
        stride1 = self.stride_window
        
        window_size2 = window_size1 * 2
        stride2 = stride1 * 2
        
        def process_stage1_window(window: list[PageContext]):
            if not self.chained_translators:
                for ctx in window:
                    if ctx.stage1_candidates is None:
                        ctx.stage1_candidates = []
                return
                
            step_translator, step_tgt_lang = self.chained_translators[0]
            texts_to_translate = []
            page_line_map = []
            
            for ctx in window:
                if ctx.stage1_candidates is None:
                    ctx.stage1_candidates = [[] for _ in range(len(ctx.original_texts or []))]
                    
                if not ctx.original_texts:
                    texts_to_translate.append(f"[Trang {ctx.page_id}: Silent Panel / Không có thoại]")
                    page_line_map.append((ctx, -1))
                else:
                    for i, t in enumerate(ctx.original_texts):
                        if self._should_skip_text(t, step_tgt_lang):
                            if ctx.stage1_candidates is not None:
                                ctx.stage1_candidates[i].append({"text": t, "score": 1.0})
                        else:
                            texts_to_translate.append(t)
                            page_line_map.append((ctx, i))
                        
            if not texts_to_translate:
                return
                
            def _process_recursive(texts, mapping):
                if not texts:
                    return
                    
                total_chars = sum(len(t) for t in texts)
                
                if self.max_request_length > 0 and total_chars > self.max_request_length and len(texts) > 1:
                    if self.log_callback:
                        self.log_callback("TRANSLATE", f"Stage 1 payload ({total_chars} chars) exceeds limit. Splitting into 2 batches...")
                    mid = len(texts) // 2
                    _process_recursive(texts[:mid], mapping[:mid])
                    _process_recursive(texts[mid:], mapping[mid:])
                    return
                    
                try:
                    if self.log_callback:
                        self.log_callback("TRANSLATE", f"Stage 1: Processing batch of {len(texts)} lines ({total_chars} chars).")
                    
                    translated_part = step_translator.translate(texts, self.src_lang, step_tgt_lang, [])
                    
                    for j, (ctx, line_idx) in enumerate(mapping):
                        if j < len(translated_part):
                            res = translated_part[j]
                            text = res if isinstance(res, str) else res.get("text", "")
                            if self.log_callback:
                                self.log_callback("DEBUG", f"OCR: {texts[j]} -> TRANSLATED: {text}")
                            score = 0.5 if isinstance(res, str) else res.get("score", 0.5)
                            if line_idx != -1 and ctx.stage1_candidates is not None:
                                ctx.stage1_candidates[line_idx].append({"text": text, "score": score})
                except Exception as e:
                    if self.log_callback:
                        self.log_callback("ERROR", f"Stage 1 Error: {e}")

            _process_recursive(texts_to_translate, page_line_map)

        def commit_stage1_page(ctx: PageContext):
            if ctx.stage1_candidates is None:
                ctx.translated_texts = list(ctx.original_texts or [])
                return
                
            best_translations = []
            if ctx.stage1_candidates is not None:
                for line_cands in ctx.stage1_candidates:
                    if not line_cands:
                        best_translations.append("")
                    else:
                        best_cands = sorted(line_cands, key=lambda x: x["score"], reverse=True)
                        best_translations.append(best_cands[0]["text"])
            ctx.translated_texts = best_translations

        def process_stage2_window(window: list[PageContext]):
            if not self.editor_translator:
                return
                
            texts_to_translate = []
            page_line_map = []
            
            for ctx in window:
                if ctx.stage2_candidates is None:
                    ctx.stage2_candidates = [[] for _ in range(len(ctx.translated_texts or []))]
                    
                if not ctx.translated_texts:
                    texts_to_translate.append(f"[Trang {ctx.page_id}: Silent Panel / Không có thoại]")
                    page_line_map.append((ctx, -1))
                else:
                    for i, t in enumerate(ctx.translated_texts):
                        texts_to_translate.append(t)
                        page_line_map.append((ctx, i))
                        
            if not texts_to_translate:
                return
                
            def _process_recursive(texts, mapping):
                if not texts:
                    return
                    
                total_chars = sum(len(t) for t in texts)
                
                if self.max_request_length > 0 and total_chars > self.max_request_length and len(texts) > 1:
                    if self.log_callback:
                        self.log_callback("TRANSLATE", f"Stage 2 payload ({total_chars} chars) exceeds limit. Splitting into 2 batches...")
                    mid = len(texts) // 2
                    _process_recursive(texts[:mid], mapping[:mid])
                    _process_recursive(texts[mid:], mapping[mid:])
                    return
                    
                try:
                    if self.log_callback:
                        self.log_callback("TRANSLATE", f"Stage 2 (Double Check): Editing batch of {len(texts)} lines ({total_chars} chars).")
                    
                    translated_part = self.editor_translator.translate(texts, "vi", "vi", [])
                    
                    for j, (ctx, line_idx) in enumerate(mapping):
                        if j < len(translated_part):
                            res = translated_part[j]
                            text = res if isinstance(res, str) else res.get("text", "")
                            score = 0.5 if isinstance(res, str) else res.get("score", 0.5)
                            if line_idx != -1 and ctx.stage2_candidates is not None:
                                ctx.stage2_candidates[line_idx].append({"text": text, "score": score})
                except Exception as e:
                    if self.log_callback:
                        self.log_callback("ERROR", f"Stage 2 Error: {e}")

            _process_recursive(texts_to_translate, page_line_map)

        def commit_stage2_page(ctx: PageContext):
            if ctx.stage2_candidates is not None:
                best_translations = []
                translated_texts = ctx.translated_texts or []
                for i, line_cands in enumerate(ctx.stage2_candidates):
                    if not line_cands:
                        best_translations.append(translated_texts[i] if i < len(translated_texts) else "")
                    else:
                        best_cands = sorted(line_cands, key=lambda x: x["score"], reverse=True)
                        best_translations.append(best_cands[0]["text"])
                ctx.translated_texts = best_translations
            ctx.trans_done.set()
            self.in_q.task_done()

        while True:
            try:
                ctx = self.in_q.get(timeout=0.5)
            except queue.Empty:
                continue
                
            if ctx is None:
                # Flush Stage 1
                while stage1_buffer:
                    process_stage1_window(stage1_buffer)
                    popped = stage1_buffer[:stride1]
                    stage1_buffer = stage1_buffer[stride1:]
                    for p in popped:
                        commit_stage1_page(p)
                        if self.editor_translator:
                            stage2_buffer.append(p)
                        else:
                            p.trans_done.set()
                            self.in_q.task_done()
                            
                # Flush Stage 2
                if self.editor_translator:
                    while stage2_buffer:
                        process_stage2_window(stage2_buffer)
                        popped = stage2_buffer[:stride2]
                        stage2_buffer = stage2_buffer[stride2:]
                        for p in popped:
                            commit_stage2_page(p)
                            
                self.in_q.task_done() # For the None token
                break
                
            stage1_buffer.append(ctx)
            if len(stage1_buffer) >= window_size1:
                process_stage1_window(stage1_buffer)
                popped = stage1_buffer[:stride1]
                stage1_buffer = stage1_buffer[stride1:]
                for p in popped:
                    commit_stage1_page(p)
                    if self.editor_translator:
                        stage2_buffer.append(p)
                        if len(stage2_buffer) >= window_size2:
                            process_stage2_window(stage2_buffer)
                            popped2 = stage2_buffer[:stride2]
                            stage2_buffer = stage2_buffer[stride2:]
                            for p2 in popped2:
                                commit_stage2_page(p2)
                    else:
                        p.trans_done.set()
                        self.in_q.task_done()
