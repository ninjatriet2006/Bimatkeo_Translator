import os
import sys
import json
import subprocess

class Pipeline:
    """Decoupled UI-side Pipeline client that runs the backend in a separate subprocess."""

    def __init__(self, app, python_executable, temp_dir):
        self.app = app
        self.python_executable = python_executable
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        self.process = None
        self._stopped_by_user = False

    def _get_subprocess_env(self, project_base_dir):
        env = os.environ.copy()
        keys_path = os.path.join(project_base_dir, ".config", "configs", "keys.yaml")
        if os.path.exists(keys_path):
            try:
                import yaml
                with open(keys_path, 'r', encoding='utf-8') as f:
                    keys_data = yaml.safe_load(f)
                if isinstance(keys_data, dict):
                    for k, v in keys_data.items():
                        if k and v is not None:
                            env[str(k)] = str(v)
            except Exception as e:
                print(f"[Pipeline] Failed to load keys.yaml into process env: {e}")
        return env

    def run(self, job, output_path, config_dict, log_callback, is_verbose=False, output_format='png'):
        self._stopped_by_user = False
        
        # Write arguments to temp file to avoid command line length limits
        config_file_path = os.path.join(self.temp_dir, f"task_{job['id']}.json")
        task_data = {
            "job": job,
            "output_path": output_path,
            "config": config_dict,
            "output_format": output_format
        }
        try:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=4)
        except Exception as e:
            log_callback("ERROR", f"Failed to write temp task config: {e}")
            return False
            
        project_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cmd = [self.python_executable, "-m", "app.core.pipeline", "--task-config", config_file_path]
        
        try:
            env = self._get_subprocess_env(project_base_dir)
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=project_base_dir,
                encoding='utf-8',
                env=env
            )
            
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("[LOG:"):
                    try:
                        right_bracket = line.find("]")
                        prefix = line[5:right_bracket]
                        msg = line[right_bracket+2:]
                        log_callback(prefix, msg)
                    except Exception:
                        log_callback("INFO", line)
                elif line == "[FINISHED:SUCCESS]":
                    pass
                elif line == "[FINISHED:FAILED]":
                    pass
                else:
                    log_callback("RAW", line)
                    
            self.process.wait()
            success = (self.process.returncode == 0)
            
            try:
                os.remove(config_file_path)
            except Exception:
                pass
                
            return success and not self._stopped_by_user
        except Exception as e:
            log_callback("ERROR", f"Failed to run backend subprocess: {e}")
            try:
                os.remove(config_file_path)
            except Exception:
                pass
            return False

    def run_single_image_test(self, test_image_path, output_path, config_dict, log_callback, is_verbose=False):
        self._stopped_by_user = False
        
        # Write arguments to temp file
        config_file_path = os.path.join(self.temp_dir, "task_visual_test.json")
        task_data = {
            "job": {"id": "visual_test"},
            "output_path": output_path,
            "config": config_dict
        }
        try:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=4)
        except Exception as e:
            log_callback("ERROR", f"Failed to write temp task config: {e}")
            return False
            
        project_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cmd = [self.python_executable, "-m", "app.core.pipeline", "--task-config", config_file_path, "--test-image", test_image_path]
        
        try:
            env = self._get_subprocess_env(project_base_dir)
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=project_base_dir,
                encoding='utf-8',
                env=env
            )
            
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("[LOG:"):
                    try:
                        right_bracket = line.find("]")
                        prefix = line[5:right_bracket]
                        msg = line[right_bracket+2:]
                        log_callback(prefix, msg)
                    except Exception:
                        log_callback("INFO", line)
                elif line == "[FINISHED:SUCCESS]":
                    pass
                elif line == "[FINISHED:FAILED]":
                    pass
                else:
                    log_callback("RAW", line)
                    
            self.process.wait()
            success = (self.process.returncode == 0)
            
            try:
                os.remove(config_file_path)
            except Exception:
                pass
                
            return success and not self._stopped_by_user
        except Exception as e:
            log_callback("ERROR", f"Failed to run backend subprocess: {e}")
            try:
                os.remove(config_file_path)
            except Exception:
                pass
            return False

    def stop(self, log_callback):
        self._stopped_by_user = True
        if self.process and self.process.poll() is None:
            log_callback("PIPELINE", "Killing backend subprocess...")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        log_callback("PIPELINE", "Mock pipeline stopped by user.")
        return True

