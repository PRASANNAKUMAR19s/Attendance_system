"""
services/email_service.py — Email Notification Service
=====================================================
Handles sending email notifications for attendance alerts.
Uses SMTP (Gmail or other email providers).
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import config as _config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    def __init__(self) -> None:
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = _config.EMAIL_SENDER
        self.sender_password = _config.EMAIL_PASSWORD
        self.tutor_email = _config.TUTOR_EMAIL
        self.tutor_name = _config.TUTOR_NAME

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(
            self.sender_email
            and self.sender_password
            and self.sender_email != "your_email@gmail.com"
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of the email
            text_body: Plain text alternative (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("Email service not configured. Skipping email to %s", to_email)
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.tutor_name} <{self.sender_email}>"
            msg["To"] = to_email

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info("Email sent to %s: %s", to_email, subject)
            return True

        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc)
            return False

    def send_attendance_alert(
        self,
        to_email: str,
        student_name: str,
        reg_no: str,
        date: str,
        period: str,
        status: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Send attendance alert email to parent/guardian."""
        subject = f"Attendance Alert: {student_name} - {status} on {date}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #0066cc; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .details {{ background: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .details table {{ width: 100%; border-collapse: collapse; }}
                .details td {{ padding: 8px; border-bottom: 1px solid #eee; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .alert {{ padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .alert-danger {{ background: #f8d7da; color: #721c24; }}
                .alert-warning {{ background: #fff3cd; color: #856404; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Paavai Engineering College</h2>
                    <p>AI Attendance System</p>
                </div>
                <div class="content">
                    <p>Dear Parent/Guardian,</p>
                    <p>This is to inform you about your ward's attendance:</p>
                    
                    <div class="details">
                        <table>
                            <tr>
                                <td><strong>Student Name:</strong></td>
                                <td>{student_name}</td>
                            </tr>
                            <tr>
                                <td><strong>Register No:</strong></td>
                                <td>{reg_no}</td>
                            </tr>
                            <tr>
                                <td><strong>Date:</strong></td>
                                <td>{date}</td>
                            </tr>
                            <tr>
                                <td><strong>Period:</strong></td>
                                <td>{period}</td>
                            </tr>
                            <tr>
                                <td><strong>Status:</strong></td>
                                <td><span class="{'alert-danger' if status == 'Absent' else 'alert-warning'}">{status}</span></td>
                            </tr>
                            {f'<tr><td><strong>Reason:</strong></td><td>{reason}</td></tr>' if reason else ''}
                        </table>
                    </div>
                    
                    <p>Please ensure your ward maintains regular attendance for better academic performance.</p>
                    
                    <p>Regards,<br>{self.tutor_name}<br>Department of AI & Data Science<br>Paavai Engineering College</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from AI Attendance System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Paavai Engineering College - Attendance Alert
        
        Dear Parent/Guardian,
        
        Student: {student_name}
        Register No: {reg_no}
        Date: {date}
        Period: {period}
        Status: {status}
        {f'Reason: {reason}' if reason else ''}
        
        Regards,
        {self.tutor_name}
        Department of AI & Data Science
        """

        return self.send_email(to_email, subject, html_body, text_body)

    def send_daily_summary(
        self,
        to_email: str,
        date: str,
        present_count: int,
        late_count: int,
        absent_count: int,
        total_students: int,
        details: List[Dict],
    ) -> bool:
        """Send daily attendance summary email."""
        subject = f"Daily Attendance Summary - {date}"

        attendance_pct = (
            round((present_count + late_count) / total_students * 100, 1)
            if total_students > 0
            else 0
        )

        details_html = ""
        for d in details[:10]:
            details_html += f"""
            <tr>
                <td>{d.get('reg_no', '-')}</td>
                <td>{d.get('name', '-')}</td>
                <td>{d.get('status', '-')}</td>
            </tr>
            """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #0066cc; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 15px; background: white; border-radius: 5px; flex: 1; margin: 0 5px; }}
                .stat-box h3 {{ margin: 0; font-size: 2rem; }}
                .details table {{ width: 100%; border-collapse: collapse; background: white; }}
                .details th {{ background: #0066cc; color: white; padding: 10px; text-align: left; }}
                .details td {{ padding: 8px; border-bottom: 1px solid #eee; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Daily Attendance Summary</h2>
                    <p>{date}</p>
                </div>
                <div class="content">
                    <div class="stats">
                        <div class="stat-box">
                            <h3>{attendance_pct}%</h3>
                            <p>Attendance</p>
                        </div>
                        <div class="stat-box">
                            <h3>{present_count}</h3>
                            <p>Present</p>
                        </div>
                        <div class="stat-box">
                            <h3>{late_count}</h3>
                            <p>Late</p>
                        </div>
                        <div class="stat-box">
                            <h3>{absent_count}</h3>
                            <p>Absent</p>
                        </div>
                    </div>
                    
                    <h4>Attendance Details</h4>
                    <div class="details">
                        <table>
                            <thead>
                                <tr>
                                    <th>Reg No</th>
                                    <th>Name</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {details_html or '<tr><td colspan="3">No records</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="footer">
                    <p>Generated by AI Attendance System - Paavai Engineering College</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_body)

    def send_low_attendance_warning(
        self,
        to_email: str,
        student_name: str,
        reg_no: str,
        attendance_pct: float,
    ) -> bool:
        """Send warning for low attendance percentage."""
        subject = f"Attendance Warning: {student_name} - {attendance_pct}% Attendance"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .warning {{ background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0; text-align: center; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>⚠️ Attendance Warning</h2>
                </div>
                <div class="content">
                    <p>Dear Parent/Guardian,</p>
                    
                    <div class="warning">
                        <h3>Attendance: {attendance_pct}%</h3>
                    </div>
                    
                    <p><strong>Student:</strong> {student_name}</p>
                    <p><strong>Register No:</strong> {reg_no}</p>
                    
                    <p>Your ward's attendance has fallen below the required threshold. 
                    Students are required to maintain at least 75% attendance to be eligible for examinations.</p>
                    
                    <p>Please contact the department and ensure your ward attends classes regularly.</p>
                    
                    <p>Regards,<br>{self.tutor_name}<br>Department of AI & Data Science</p>
                </div>
                <div class="footer">
                    <p>This is an automated warning from AI Attendance System.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_body)

    def send_early_leave_alert(
        self,
        to_email: str,
        student_name: str,
        reg_no: str,
        reason: str,
        leave_time: str,
    ) -> bool:
        """Send immediate alert when student leaves early."""
        subject = f"URGENT: {student_name} ({reg_no}) - Early Leave Alert"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .alert-box {{ background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #dc3545; }}
                .details {{ background: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .details table {{ width: 100%; border-collapse: collapse; }}
                .details td {{ padding: 8px; border-bottom: 1px solid #eee; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Early Leave Alert</h2>
                    <p>Immediate Attention Required</p>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <strong>Student has left the campus early!</strong>
                    </div>
                    
                    <div class="details">
                        <table>
                            <tr>
                                <td><strong>Student Name:</strong></td>
                                <td>{student_name}</td>
                            </tr>
                            <tr>
                                <td><strong>Register No:</strong></td>
                                <td>{reg_no}</td>
                            </tr>
                            <tr>
                                <td><strong>Leave Time:</strong></td>
                                <td>{leave_time}</td>
                            </tr>
                            <tr>
                                <td><strong>Reason:</strong></td>
                                <td>{reason}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p><strong>Action Required:</strong> Please verify this early departure.</p>
                    
                    <p>Regards,<br>AI Attendance System<br>Paavai Engineering College</p>
                </div>
                <div class="footer">
                    <p>This is an automated alert from AI Attendance System.</p>
                    <p>Time: {leave_time}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, html_body)
