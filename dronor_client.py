"""
Dronor Expert Client — вызывает экспертов Digital Smarty через API.
Каждый метод = один Dronor эксперт.

Архитектура:
  Bot → DronorClient → HTTP POST → Dronor API → Expert → Result

Эксперты:
  ds_url_resolver      — определяет тип источника (YouTube/Drive/файл)
  ds_audio_extractor   — извлекает аудио из любого источника
  ds_transcriber       — транскрипция через Deepgram Nova-2
  ds_topic_extractor   — извлечение тем, решений, задач (GPT-4o)
  ds_expert_analyzer   — экспертный анализ с SWOT (GPT-4o)
  ds_report_generator  — генерация PDF/HTML/TXT/JSON отчётов
  ds_context_manager   — сохранение контекста пользователя
  ds_session_memory    — загрузка истории для continuity
"""
import requests
import json
import logging

logger = logging.getLogger("dronor_client")


class DronorClient:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip("/")
        self.timeout = 300  # 5 min default

    def _call_expert(self, expert_name: str, params: dict = None, timeout: int = None) -> dict:
        """Universal expert caller via Dronor API"""
        url = f"{self.api_url}/api/expert/run/{expert_name}"
        payload = {"params": params or {}}
        try:
            resp = requests.post(url, json=payload, timeout=timeout or self.timeout)
            resp.raise_for_status()
            data = resp.json()
            # Parse nested JSON result if string
            if isinstance(data.get("result"), str):
                try:
                    data["result"] = json.loads(data["result"])
                except (json.JSONDecodeError, TypeError):
                    pass
            return data
        except requests.Timeout:
            logger.error(f"Expert {expert_name} timed out after {timeout or self.timeout}s")
            return {"status": "error", "error": "timeout"}
        except Exception as e:
            logger.error(f"Expert {expert_name} failed: {e}")
            return {"status": "error", "error": str(e)}

    def _call_pipeline(self, pipeline_id: str, params: dict = None) -> dict:
        """Call full Dronor pipeline"""
        url = f"{self.api_url}/api/pipeline/run/{pipeline_id}"
        payload = {"params": params or {}}
        try:
            resp = requests.post(url, json=payload, timeout=600)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} failed: {e}")
            return {"status": "error", "error": str(e)}

    def _safe_result(self, response: dict, key: str = None, default=None):
        """Safely extract result from expert response"""
        result = response.get("result", {})
        if not isinstance(result, dict):
            return default if key else result
        return result.get(key, default) if key else result

    # ═══════════════════════════════════════════════
    # STEP 1: URL RESOLVE
    # ═══════════════════════════════════════════════
    def resolve_url(self, url: str, file_type: str = "") -> dict:
        """
        ds_url_resolver — определяет тип источника.
        
        Returns: {source_type, resolved_url, metadata}
        source_type: youtube | google_drive | dropbox | yandex_disk | 
                     vimeo | loom | direct_media | telegram
        """
        return self._call_expert("ds_url_resolver", {
            "url": url, "file_type": file_type
        })

    # ═══════════════════════════════════════════════
    # STEP 2: AUDIO EXTRACTION
    # ═══════════════════════════════════════════════
    def extract_audio(self, url: str = "", source_type: str = "",
                      file_path: str = "", platform: str = "") -> dict:
        """
        ds_audio_extractor — извлекает аудио из любого источника.
        Uses: yt-dlp + ffmpeg → WAV 16kHz mono
        
        Returns: {audio_path, duration, source_info}
        """
        return self._call_expert("ds_audio_extractor", {
            "url": url, "source_type": source_type,
            "file_path": file_path, "platform": platform
        }, timeout=600)

    # ═══════════════════════════════════════════════
    # STEP 3: TRANSCRIPTION
    # ═══════════════════════════════════════════════
    def transcribe(self, audio_path: str, language: str = "auto") -> dict:
        """
        ds_transcriber — транскрипция через Deepgram Nova-2.
        Features: smart formatting, punctuation, diarization, language detection.
        
        Returns: {transcription, segments, confidence, language, word_count}
        """
        return self._call_expert("ds_transcriber", {
            "audio_path": audio_path, "language": language
        }, timeout=600)

    # ═══════════════════════════════════════════════
    # STEP 4: TOPIC EXTRACTION
    # ═══════════════════════════════════════════════
    def extract_topics(self, transcription: str, segments: str = "") -> dict:
        """
        ds_topic_extractor — извлечение тем, решений, задач.
        
        Returns: {domain, meeting_type, topics[], decisions[], 
                  action_items[], open_questions[], conflicts[], 
                  risks[], key_quotes[], executive_summary}
        
        Принцип: НЕ ВЫДУМЫВАТЬ — только то, что реально есть в аудио.
        """
        return self._call_expert("ds_topic_extractor", {
            "transcription": transcription, "segments": segments
        })

    # ═══════════════════════════════════════════════
    # STEP 5: EXPERT ANALYSIS
    # ═══════════════════════════════════════════════
    def analyze_expert(self, transcription: str, topic_analysis: str) -> dict:
        """
        ds_expert_analyzer — главный мозг Цифрового Умника.
        
        Авто-определяет домен и становится экспертом:
        - business_strategy → Бизнес-консультант
        - product → Product Manager  
        - marketing → Маркетолог
        - sales → Sales-эксперт
        - tech → Solution Architect
        - hr → HR-консультант
        - finance → Финансовый аналитик
        - legal → Юрист
        - medical → Медицинский консультант
        - education → Педагог
        - ... любой другой домен
        
        Returns: {domain, expert_role, assessment{SWOT}, 
                  recommendations[], missed_topics[], 
                  next_steps[], quality_scores}
        """
        return self._call_expert("ds_expert_analyzer", {
            "transcription": transcription,
            "topic_analysis": topic_analysis
        })

    # ═══════════════════════════════════════════════
    # STEP 6: REPORT GENERATION
    # ═══════════════════════════════════════════════
    def generate_report(self, transcription: str, topic_analysis: str,
                        expert_analysis: str, fmt: str = "html_dark") -> dict:
        """
        ds_report_generator — генерация финального отчёта.
        
        Formats: pdf, html_dark, html_light, txt, json
        Returns: {file_path, format, file_size}
        """
        return self._call_expert("ds_report_generator", {
            "transcription": transcription,
            "topic_analysis": topic_analysis,
            "expert_analysis": expert_analysis,
            "format": fmt
        })

    # ═══════════════════════════════════════════════
    # CONTEXT & MEMORY
    # ═══════════════════════════════════════════════
    def load_context(self, user_id: str) -> dict:
        """ds_session_memory — загрузка контекста пользователя для continuity"""
        return self._call_expert("ds_session_memory", {
            "user_id": user_id,
            "task_text": "",
            "include_full_history": "false"
        })

    def save_context(self, user_id: str, session_data: str) -> dict:
        """ds_context_manager — сохранение контекста после анализа"""
        return self._call_expert("ds_context_manager", {
            "action": "save_context",
            "user_id": user_id,
            "session_data": session_data
        })

    def get_user_history(self, user_id: str) -> dict:
        """ds_context_manager — получить историю сессий пользователя"""
        return self._call_expert("ds_context_manager", {
            "action": "list_sessions",
            "user_id": user_id
        })

    # ═══════════════════════════════════════════════
    # FULL PIPELINE (one-shot)
    # ═══════════════════════════════════════════════
    def run_full_pipeline(self, url: str = "", user_id: str = "") -> dict:
        """
        Запуск полного пайплайна pipeline_27 (Digital Smarty v4.1).
        URL → Audio → Transcribe → Topics → Expert → Report
        + Context Memory
        """
        return self._call_pipeline("pipeline_27_digital_smarty_v4.1", {
            "INPUT": url, "USER_ID": user_id
        })
