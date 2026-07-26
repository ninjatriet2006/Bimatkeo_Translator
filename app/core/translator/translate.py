"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.translator.translate
- RESPONSIBILITY: Handles Stage 1 (Rough translation) of the translation process.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.translator.interfaces.BaseTranslator
- IN = OUT: Receives PageContext from q_trans, pushes to q_edit (if Editor exists) or calls trans_done.set().
=============================================================================
"""
import multiprocessing
import queue
import fnmatch
import re
from app.core.shared_context.dto import PageContext

try:
    from langdetect import detect
except ImportError:
    detect = None

class TranslateWorker(multiprocessing.Process):
    def __init__(self, in_q: multiprocessing.Queue, out_q: multiprocessing.Queue | None, config_dict: dict, log_queue: multiprocessing.Queue):
        super().__init__()
        self.in_q = in_q
        self.out_q = out_q
        self.config_dict = config_dict
        self.log_queue = log_queue
        
        self.src_lang = config_dict.get("translator", {}).get("source_lang", "JPN")
        self.tgt_lang = config_dict.get("translator", {}).get("target_lang", "VIN")
        
        self.skip_languages = config_dict.get("skip_languages", {})
        self.filter_texts = config_dict.get("filter_texts", [])
        self.no_text_lang_skip = config_dict.get("translator", {}).get("no_text_lang_skip", False)
        
        max_len = str(config_dict.get("translator", {}).get("max_request_length", 2000)).replace("none", "2000")
        self.max_request_length = int(max_len) if max_len else 2000
        
        c_win = str(config_dict.get("translator", {}).get("context_window", 10)).replace("none", "10")
        self.context_window = max(1, int(c_win) if c_win else 10)
        
        s_win = str(config_dict.get("translator", {}).get("stride_window", 5)).replace("none", "5")
        self.stride_window = max(1, int(s_win) if s_win else 5)
        
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
        def _log(level, msg):
            self.log_queue.put((level, f"[TRANSLATE_WORKER] {msg}"))
            
        _log("INFO", "Translate Worker Process Started.")
        
        # Initialize models INSIDE the new process
        from app.core.translator.initializer import TranslatorInitializer
        import os
        project_root = os.environ.get("PROJECT_ROOT") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        # We need the resolved API profiles
        api_profiles = self.config_dict.get("api_profiles_resolved", {})
        
        chained_translators, _ = TranslatorInitializer.initialize(self.config_dict, project_root, api_profiles, _log)
        self.chained_translators = chained_translators
        self.log_callback = _log
        
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
                    if self.log_callback is not None:
                        self.log_callback("TRANSLATE", f"Stage 1 payload ({total_chars} chars) exceeds limit. Splitting into 2 batches...")
                    mid = len(texts) // 2
                    _process_recursive(texts[:mid], mapping[:mid])
                    _process_recursive(texts[mid:], mapping[mid:])
                    return
                    
                try:
                    if self.log_callback is not None:
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
                    if self.log_callback is not None:
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
                            
                if self.out_q:
                    self.out_q.put(None)
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
