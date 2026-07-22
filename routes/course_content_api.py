#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
from services.course_content_service import CourseContentService

course_content_bp = Blueprint('course_content', __name__, url_prefix='/api/course')
@course_content_bp.route('/<int:course_id>/chapters')
def get_chapters(course_id): return jsonify(CourseContentService.get_course_chapters(course_id))
@course_content_bp.route('/chapters/<int:chapter_id>/sessions')
def get_sessions(chapter_id): return jsonify(CourseContentService.get_chapter_sessions(chapter_id))
@course_content_bp.route('/enrollment/<int:enrollment_id>/detail')
def get_course_detail(enrollment_id): return jsonify(CourseContentService.get_student_course_detail(enrollment_id))
@course_content_bp.route('/attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    result = CourseContentService.mark_attendance(data.get('session_id'), data.get('enrollment_id'), data.get('attended', True))
    return jsonify(result)
@course_content_bp.route('/enrollment/<int:enrollment_id>/progress')
def get_progress(enrollment_id): return jsonify(CourseContentService.get_student_progress(enrollment_id))
