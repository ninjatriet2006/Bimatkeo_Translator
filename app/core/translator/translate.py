"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.translator.translate
- RESPONSIBILITY: Handles Stage 1 (Rough translation) of the translation process.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.interfaces.BaseTranslator
- IN = OUT: Receives PageContext from q_trans, pushes to q_edit (if Editor exists) or calls trans_done.set().
=============================================================================
"""
import threading
import queue
import fnmatch
import re
from app.core.shared.dto import PageContext

try:
    from langdetect import detect
except ImportError:
    detect = None

class TranslateWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, out_q: queue.Queue | None, translator_or_chain, src_lang: str, tgt_lang: str, log_callback=None, hitl_callback=None, skip_languages=None, filter_texts=None, no_text_lang_skip=False, max_request_length=-1, context_window=10, stride_window=5):
        super().__init__()
        self.in_q = in_q
        self.out_q = out_q
        
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

        # 2. Skip languages check
        if detect and self.skip_languages and not self.no_text_lang_skip:
            try:
                lang = detect(text)
                # Map to standard codes
                lang_map = {'zh-cn': 'ZHO', 'zh-tw': 'ZHO', 'ja': 'JPN', 'ko': 'KOR', 'en': 'ENG', 'vi': 'VIN'}
                detected_std = lang_map.get(lang.lower(), lang.upper())
                
                # We skip if:
                # a) The detected language is the target language (no need to translate)
                if detected_std == current_tgt_lang:
                    return True
                
                # b) The detected language is in the user's skip list
                for skip_lang, should_skip in self.skip_languages.items():
                    if should_skip and detected_std == skip_lang:
                        return True
            except Exception:
                pass
                
        return False

    def run(self):
        stage1_buffer = []
        window_size1 = self.context_window
        stride1 = self.stride_window
        
        step_translator, step_tgt_lang = self.chained_translators[-1] if self.chained_translators else (None, self.tgt_lang)

        def process_stage1_window(window: list[PageContext]):
            if not step_translator:
                return
                
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
                        if self.out_q:
                            self.out_q.put(p)
                        else:
                            p.trans_done.set()
                            self.in_q.task_done()
                            
                if self.out_q:
                    self.out_q.put(None)
                self.in_q.task_done()
                break
                
            stage1_buffer.append(ctx)
            if len(stage1_buffer) >= window_size1:
                process_stage1_window(stage1_buffer)
                popped = stage1_buffer[:stride1]
                stage1_buffer = stage1_buffer[stride1:]
                for p in popped:
                    commit_stage1_page(p)
                    if self.out_q:
                        self.out_q.put(p)
                    else:
                        p.trans_done.set()
                        self.in_q.task_done()
