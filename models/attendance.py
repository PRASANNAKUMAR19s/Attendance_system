from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.now().date)
    time = db.Column(db.Time, default=datetime.now().time)
    status = db.Column(db.String(20), default='present')  # present, late, absent
    marked_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    student = db.relationship('Student', backref='attendances')
    marked_by_user = db.relationship('User', backref='marked_attendances')
    
    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.date}>'