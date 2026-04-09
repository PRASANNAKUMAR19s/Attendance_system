from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
import cv2
import numpy as np
import sqlite3
import logging

from database import get_db

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

# ... rest of the file stays the same, but replace:
# from models.attendance import Attendance
# With direct SQL queries instead
# Global variables for camera
camera = None
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

@monitoring_bp.route('/dashboard')
@login_required
def monitoring_dashboard():
    """Display live monitoring dashboard"""
    if current_user.role not in ['admin', 'tutor', 'hod']:
        return "Access Denied", 403
    
    students = Student.query.all()
    return render_template('monitoring_dashboard.html', students=students)

@monitoring_bp.route('/api/camera-feed')
@login_required
def camera_feed():
    """Stream camera feed for attendance"""
    def generate():
        global camera
        camera = cv2.VideoCapture(0)
        
        while True:
            success, frame = camera.read()
            if not success:
                break
            
            # Detect faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # Draw rectangles around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    return generate(), 200, {
        'Content-Type': 'multipart/x-mixed-replace; boundary=frame',
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
    }

@monitoring_bp.route('/api/attendance/mark', methods=['POST'])
@login_required
def mark_attendance():
    """Mark attendance for a student"""
    data = request.json
    student_id = data.get('student_id')
    status = data.get('status', 'present')  # present, late, absent
    
    try:
        attendance = Attendance(
            student_id=student_id,
            date=datetime.now().date(),
            time=datetime.now().time(),
            status=status,
            marked_by=current_user.id
        )
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked: {status}'
        }), 200
    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@monitoring_bp.route('/api/today-attendance')
@login_required
def today_attendance():
    """Get today's attendance records"""
    today = datetime.now().date()
    attendance = Attendance.query.filter_by(date=today).all()
    
    data = [{
        'student_id': a.student_id,
        'student_name': a.student.name,
        'time': str(a.time),
        'status': a.status
    } for a in attendance]
    
    return jsonify(data), 200

@monitoring_bp.route('/api/live-stats')
@login_required
def live_stats():
    """Get live attendance statistics"""
    today = datetime.now().date()
    total_students = Student.query.count()
    present = Attendance.query.filter_by(date=today, status='present').count()
    late = Attendance.query.filter_by(date=today, status='late').count()
    absent = total_students - present - late
    
    return jsonify({
        'total': total_students,
        'present': present,
        'late': late,
        'absent': absent,
        'percentage': round((present / total_students * 100), 2) if total_students > 0 else 0
    }), 200

@monitoring_bp.route('/stop-camera', methods=['POST'])
@login_required
def stop_camera():
    """Stop camera stream"""
    global camera
    if camera:
        camera.release()
        camera = None
    return jsonify({'success': True}), 200