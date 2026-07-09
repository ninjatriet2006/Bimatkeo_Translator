"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.translator.edit
- RESPONSIBILITY: Handles Stage 2 (Proofreading / Double check) of the translation process.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.interfaces.BaseTranslator
- IN = OUT: Receives PageContext from q_edit, calls trans_done.set() when complete.
=============================================================================
"""
import threading
import queue
from app.core.dto import PageContext

class EditWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, editor_translator, log_callback=None, max_request_length=-1, context_window=10, stride_window=5):
        super().__init__()
        self.in_q = in_q
        self.editor_translator = editor_translator
        self.log_callback = log_callback
        self.max_request_length = max_request_length
        self.context_window = max(1, context_window)
        self.stride_window = max(1, stride_window)
        self.daemon = True

    def run(self):
        stage2_buffer = []
        window_size2 = self.context_window
        stride2 = self.stride_window

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
                # Flush Stage 2
                while stage2_buffer:
                    process_stage2_window(stage2_buffer)
                    popped = stage2_buffer[:stride2]
                    stage2_buffer = stage2_buffer[stride2:]
                    for p in popped:
                        commit_stage2_page(p)
                        
                self.in_q.task_done() # For the None token
                break
                
            stage2_buffer.append(ctx)
            if len(stage2_buffer) >= window_size2:
                process_stage2_window(stage2_buffer)
                popped = stage2_buffer[:stride2]
                stage2_buffer = stage2_buffer[stride2:]
                for p in popped:
                    commit_stage2_page(p)
