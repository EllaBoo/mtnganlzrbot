import os
import asyncio
import aiohttp
import aiofiles
import subprocess
from pathlib import Path
from config import Config
from transcriber import Transcriber
from analyzer import Analyzer
from report_generator import ReportGenerator

class Processor:
    def __init__(self):
        self.transcriber = Transcriber()
        self.analyzer = Analyzer()
        self.report_generator = ReportGenerator()
        self.temp_dir = Path(Config.TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def process(self, file_path: str, output_language: str = "ru", 
                      progress_callback=None) -> dict:
        try:
            if progress_callback:
                await progress_callback("Preparing file...")
            
            audio_path = await self._prepare_audio(file_path)
            
            if progress_callback:
                await progress_callback("Transcribing (this may take a few minutes)...")
            
            transcript_data = await self.transcriber.transcribe(audio_path, output_language)
            
            if progress_callback:
                await progress_callback("Analyzing content...")
            
            actual_output_lang = output_language
            if output_language == "auto":
                actual_output_lang = transcript_data.get("detected_language", "ru")
            
            analysis = await self.analyzer.analyze(transcript_data, actual_output_lang)
            
            if progress_callback:
                await progress_callback("Generating reports...")
            
            safe_title = self._sanitize_filename(analysis.get("title", "meeting"))
            date_str = analysis.get("date_mentioned") or ""
            if date_str:
                date_str = date_str.replace(".", "-").replace("/", "-")
            
            base_name = f"{safe_title}_{date_str}" if date_str else safe_title
            
            html_content = self.report_generator.generate_html(analysis, transcript_data)
            html_path = self.temp_dir / f"{base_name}.html"
            async with aiofiles.open(html_path, "w", encoding="utf-8") as f:
                await f.write(html_content)
            
            pdf_path = self.temp_dir / f"{base_name}.pdf"
            self.report_generator.generate_pdf(html_content, str(pdf_path))
            
            transcript_path = self.temp_dir / f"{base_name}_transcript.txt"
            self.report_generator.generate_transcript_file(transcript_data, str(transcript_path))
            
            return {
                "success": True,
                "analysis": analysis,
                "transcript_data": transcript_data,
                "html_path": str(html_path),
                "pdf_path": str(pdf_path),
                "transcript_path": str(transcript_path),
                "html_content": html_content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if 'audio_path' in locals() and audio_path != file_path:
                try:
                    os.remove(audio_path)
                except:
                    pass
    
    async def _prepare_audio(self, file_path: str) -> str:
        output_path = self.temp_dir / f"audio_{Path(file_path).stem}.mp3"
        
        cmd = [
            "ffmpeg", "-y", "-i", file_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-ab", "64k",
            "-ar", "16000",
            "-ac", "1",
            str(output_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.wait()
        
        if process.returncode != 0:
            return file_path
        
        return str(output_path)
    
    def _sanitize_filename(self, name: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "")
        return name[:50].strip()
    
    async def download_file(self, url: str, progress_callback=None) -> str:
        if progress_callback:
            await progress_callback("Downloading file...")
        
        filename = url.split("/")[-1].split("?")[0]
        if not filename:
            filename = "download.mp3"
        
        output_path = self.temp_dir / filename
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(output_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                else:
                    raise Exception(f"Failed to download: HTTP {response.status}")
        
        return str(output_path)
