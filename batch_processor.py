"""Batch Processor - handles multiple files and combines results into one.

This is a NEW module that doesn't modify existing code.
It wraps the existing Processor class to handle multiple files.
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Callable, Optional
from config import Config
from processor import Processor


class BatchProcessor:
    """Processes multiple files and combines them into a single result."""
    
    MAX_FILES = 5
    
    def __init__(self):
        self.processor = Processor()
        self.temp_dir = Path(Config.TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_batch(
        self,
        file_paths: List[str],
        output_language: str = "ru",
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        Process multiple files and combine into single result.
        
        Args:
            file_paths: List of file paths to process (max 5)
            output_language: Output language code
            progress_callback: Async callback for status updates
            
        Returns:
            Combined result dict with single analysis and reports
        """
        
        if len(file_paths) > self.MAX_FILES:
            return {
                "success": False,
                "error": f"Maximum {self.MAX_FILES} files allowed"
            }
        
        if not file_paths:
            return {
                "success": False,
                "error": "No files provided"
            }
        
        try:
            all_transcripts = []
            total_files = len(file_paths)
            
            # Process each file individually for transcription
            for i, file_path in enumerate(file_paths, 1):
                if progress_callback:
                    await progress_callback(
                        f"Processing file {i}/{total_files}: {Path(file_path).name}..."
                    )
                
                # Prepare audio
                audio_path = await self.processor._prepare_audio(file_path)
                
                if progress_callback:
                    await progress_callback(
                        f"Transcribing file {i}/{total_files}..."
                    )
                
                # Transcribe
                transcript_data = await self.processor.transcriber.transcribe(
                    audio_path, output_language
                )
                
                # Add file info to transcript
                transcript_data["source_file"] = Path(file_path).name
                transcript_data["file_index"] = i
                all_transcripts.append(transcript_data)
                
                # Cleanup temp audio
                if audio_path != file_path:
                    try:
                        os.remove(audio_path)
                    except:
                        pass
            
            if progress_callback:
                await progress_callback("Combining transcripts...")
            
            # Combine all transcripts into one
            combined_transcript = self._combine_transcripts(all_transcripts)
            
            if progress_callback:
                await progress_callback("Analyzing combined content...")
            
            # Determine output language
            actual_output_lang = output_language
            if output_language == "auto":
                actual_output_lang = combined_transcript.get("detected_language", "ru")
            
            # Analyze combined transcript
            analysis = await self.processor.analyzer.analyze(
                combined_transcript, actual_output_lang
            )
            
            # Add batch info to analysis
            analysis["batch_info"] = {
                "total_files": total_files,
                "file_names": [Path(f).name for f in file_paths]
            }
            
            if progress_callback:
                await progress_callback("Generating combined reports...")
            
            # Generate reports
            safe_title = self.processor._sanitize_filename(
                analysis.get("title", "combined_meeting")
            )
            date_str = analysis.get("date_mentioned") or ""
            if date_str:
                date_str = date_str.replace(".", "-").replace("/", "-")
            
            base_name = f"{safe_title}_{date_str}_combined" if date_str else f"{safe_title}_combined"
            
            # Generate HTML
            html_content = self.processor.report_generator.generate_html(
                analysis, combined_transcript
            )
            html_path = self.temp_dir / f"{base_name}.html"
            
            import aiofiles
            async with aiofiles.open(html_path, "w", encoding="utf-8") as f:
                await f.write(html_content)
            
            # Generate PDF
            pdf_path = self.temp_dir / f"{base_name}.pdf"
            self.processor.report_generator.generate_pdf(html_content, str(pdf_path))
            
            # Generate transcript file
            transcript_path = self.temp_dir / f"{base_name}_transcript.txt"
            self._generate_combined_transcript_file(
                all_transcripts, str(transcript_path)
            )
            
            return {
                "success": True,
                "analysis": analysis,
                "transcript_data": combined_transcript,
                "html_path": str(html_path),
                "pdf_path": str(pdf_path),
                "transcript_path": str(transcript_path),
                "html_content": html_content,
                "files_processed": total_files
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _combine_transcripts(self, transcripts: List[dict]) -> dict:
        """
        Combine multiple transcripts into one.
        Preserves speaker info and adds file markers.
        """
        
        combined_text_parts = []
        combined_segments = []
        total_duration = 0
        time_offset = 0
        
        for t in transcripts:
            file_name = t.get("source_file", "Unknown")
            file_index = t.get("file_index", 0)
            
            # Add file separator in text
            combined_text_parts.append(f"\n\n=== FILE {file_index}: {file_name} ===\n\n")
            combined_text_parts.append(t.get("text", ""))
            
            # Adjust segment timestamps
            for segment in t.get("segments", []):
                adjusted_segment = segment.copy()
                adjusted_segment["start"] = segment.get("start", 0) + time_offset
                adjusted_segment["end"] = segment.get("end", 0) + time_offset
                adjusted_segment["source_file"] = file_name
                combined_segments.append(adjusted_segment)
            
            file_duration = t.get("duration", 0)
            time_offset += file_duration
            total_duration += file_duration
        
        return {
            "text": "".join(combined_text_parts),
            "segments": combined_segments,
            "duration": total_duration,
            "detected_language": transcripts[0].get("detected_language") if transcripts else None,
            "is_combined": True,
            "source_files": [t.get("source_file") for t in transcripts]
        }
    
    def _generate_combined_transcript_file(
        self, transcripts: List[dict], output_path: str
    ):
        """Generate a transcript file with clear file separators."""
        
        lines = []
        lines.append("=" * 60)
        lines.append("COMBINED TRANSCRIPT")
        lines.append(f"Total files: {len(transcripts)}")
        lines.append("=" * 60)
        lines.append("")
        
        for t in transcripts:
            file_name = t.get("source_file", "Unknown")
            file_index = t.get("file_index", 0)
            duration = t.get("duration", 0)
            
            lines.append("")
            lines.append("-" * 60)
            lines.append(f"FILE {file_index}: {file_name}")
            lines.append(f"Duration: {int(duration // 60)}m {int(duration % 60)}s")
            lines.append("-" * 60)
            lines.append("")
            lines.append(t.get("text", ""))
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("END OF COMBINED TRANSCRIPT")
        lines.append("=" * 60)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
