#!/usr/bin/env python3
from models.database import db
from datetime import datetime
from typing import List, Dict, Any, Optional

class CourseContentService:
    @staticmethod
    def get_course_chapters(course_id: int) -> List[Dict[str, Any]]:
        rows = db.fetch_all("SELECT * FROM chapters WHERE course_id = ? ORDER BY order_index", (course_id,))
        return [dict(row) for row in rows]
    @staticmethod
    def get_chapter_sessions(chapter_id: int) -> List[Dict[str, Any]]:
        rows = db.fetch_all("SELECT * FROM sessions WHERE chapter_id = ? ORDER BY day_of_week, start_time", (chapter_id,))
        return [dict(row) for row in rows]
    @staticmethod
    def mark_attendance(session_id: int, enrollment_id: int, attended: bool = True) -> Dict[str, Any]:
        existing = db.fetch_one("SELECT id FROM session_attendance WHERE session_id = ? AND enrollment_id = ?", (session_id, enrollment_id))
        if existing:
            db.execute("UPDATE session_attendance SET attended = ?, attended_at = ? WHERE id = ?", (attended, datetime.now().isoformat(), existing['id']))
        else:
            db.execute("INSERT INTO session_attendance (session_id, enrollment_id, attended, attended_at) VALUES (?, ?, ?, ?)", (session_id, enrollment_id, attended, datetime.now().isoformat()))
        return {'success': True}
    @staticmethod
    def get_student_progress(enrollment_id: int) -> Dict[str, Any]:
        total = db.fetch_one("SELECT COUNT(*) as total FROM sessions s JOIN chapters ch ON s.chapter_id = ch.id JOIN enrollments e ON e.course_id = ch.course_id WHERE e.id = ?", (enrollment_id,))
        total_sessions = total['total'] if total else 0
        attended = db.fetch_one("SELECT COUNT(*) as attended FROM session_attendance sa JOIN sessions s ON sa.session_id = s.id JOIN chapters ch ON s.chapter_id = ch.id JOIN enrollments e ON e.course_id = ch.course_id WHERE e.id = ? AND sa.attended = 1", (enrollment_id,))
        attended_sessions = attended['attended'] if attended else 0
        progress = round((attended_sessions / total_sessions * 100) if total_sessions > 0 else 0, 2)
        return {'total_sessions': total_sessions, 'attended_sessions': attended_sessions, 'progress_percentage': progress}
    @staticmethod
    def get_student_course_detail(enrollment_id: int) -> Dict[str, Any]:
        enrollment = db.fetch_one("SELECT e.*, c.title as course_title, c.description as course_description FROM enrollments e JOIN courses c ON e.course_id = c.id WHERE e.id = ?", (enrollment_id,))
        if not enrollment: return {'error': 'Inscription non trouvée'}
        chapters = CourseContentService.get_course_chapters(enrollment['course_id'])
        for ch in chapters:
            ch['sessions'] = CourseContentService.get_chapter_sessions(ch['id'])
            for s in ch['sessions']:
                att = db.fetch_one("SELECT attended FROM session_attendance WHERE session_id = ? AND enrollment_id = ?", (s['id'], enrollment_id))
                s['attended'] = att['attended'] if att else False
        progress = CourseContentService.get_student_progress(enrollment_id)
        return {'enrollment': dict(enrollment), 'chapters': chapters, 'progress': progress}
