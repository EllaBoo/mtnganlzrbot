"""
Dronor Expert Client — вызывает экспертов через API.
Каждый метод = один эксперт из Digital Smarty pipeline.
"""
import requests
import json
import logging

logger = logging.getLogger("dronor_client")

class DronorClient:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip("/")
        self.timeout = 300  # 5 min for long operations
    
    def _call_expert(self, expert_name: str, params: dict = None, timeout: int = None) -> dict:
        """Universal expert caller"""
        url = f"{self.api_url}/api/expert/run/{expert_name}"
        payload = {"params": params or {}}
        try:
            resp = requests.post(url, json=payload, timeout=timeout or self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data.get("result"), str):
                try:
                    data["result"] = json.loads(data["result"])
                except (json.JSONDecodeError, TypeError):
                    pass
            return data
        except Exception as e:
            logger.error(f"Expert {expert_name} failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _call_pipeline(self, pipeline_id: str, params: dict = None) -> dict:
        """Call full pipeline"""
        url = f"{self.api_url}/api/pipeline/run/{pipeline_id}"
        payload = {"params": params or {}}
        try:
            resp = requests.post(url, json=payload, timeout=600)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} failed: {e}")
            return {"status": "error", "error": str(e)}
    
    # === EXPERT METHODS ===
    
    def resolve_url(self, url: str, file_type: str = "") -> dict:
        """ds_url_resolver — определяет тип источника"""
        return self._call_expert("ds_url_resolver", {"url": url, "file_type": file_type})
    
    def extract_audio(self, url: str = "", source_type: str = "", file_path: str = "", platform: str = "") -> dict:
        """ds_audio_extractor — извлекает аудио из любого источника"""
        return self._call_expert("ds_audio_extractor", {
            "url": url, "source_type": source_type,
            "file_path": file_path, "platform": platform
        }, timeout=600)
    
    def transcribe(self, audio_path: str, language: str = "auto") -> dict:
        """ds_transcriber — транскрипция через Deepgram"""
        return self._call_expert("ds_transcriber", {
            "audio_path": audio_path, "language": language
        }, timeout=600)
    
    def extract_topics(self, transcription: str, segments: str = "") -> dict:
        """ds_topic_extractor — извлечение тем, решений, задач"""
        return self._call_expert("ds_topic_extractor", {
            "transcription": transcription, "segments": segments
        })
    
    def analyze_expert(self, transcription: str, topic_analysis: str) -> dict:
        """ds_expert_analyzer — экспертный анализ с SWOT"""
        return self._call_expert("ds_expert_analyzer", {
            "transcription": transcription, "topic_analysis": topic_analysis
        })
    
    def generate_report(self, transcription: str, topic_analysis: str, 
                       expert_analysis: str, fmt: str = "html_dark") -> dict:
        """ds_report_generator — генерация отчёта"""
        return self._call_expert("ds_report_generator", {
            "transcription": transcription, "topic_analysis": topic_analysis,
            "expert_analysis": expert_analysis, "format": fmt
        })
    
    def load_context(self, user_id: str) -> dict:
        """ds_session_memory — загрузка контекста пользователя"""
        return self._call_expert("ds_session_memory", {
            "user_id": user_id, "task_text": "", "include_full_history": "false"
        })
    
    def save_context(self, user_id: str, session_data: str) -> dict:
        """ds_context_manager — сохранение контекста"""
        return self._call_expert("ds_context_manager", {
            "action": "save_context", "user_id": user_id, "session_data": session_data
        })
    
    def run_full_pipeline(self, url: str = "", user_id: str = "") -> dict:
        """Запуск полного пайплайна v4.1"""
        return self._call_pipeline("pipeline_27_digital_smarty_v4.1", {
            "INPUT": url, "USER_ID": user_id
        })
