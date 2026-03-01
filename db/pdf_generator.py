"""
PDF Report Generator
Generates student progress reports with personal details, academics, and attendance
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
from db.supabase import get_supabase

def generate_student_report(register_number):
    """
    Generate a comprehensive PDF report for a student
    
    Args:
        register_number: Student's register number
    
    Returns:
        BytesIO object containing the PDF, or None if student not found
    """
    try:
        supabase = get_supabase()
        
        # Fetch student data
        student_result = supabase.table('students').select('*').eq('register_number', register_number).execute()
        if not student_result.data:
            return None
        student = student_result.data[0]
        
        # Fetch academic data
        academic_result = supabase.table('academic').select('*').eq('register_number', register_number).execute()
        academic = academic_result.data[0] if academic_result.data else None
        
        # Fetch attendance data
        attendance_result = supabase.table('attendance').select('*').eq('register_number', register_number).execute()
        attendance = attendance_result.data[0] if attendance_result.data else None
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#05043e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#05043e'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Title
        title = Paragraph("STUDENT PROGRESS REPORT", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Report metadata
        report_date = Paragraph(
            f"<para alignment='right'><font size=10>Generated on: {datetime.now().strftime('%B %d, %Y')}</font></para>",
            styles['Normal']
        )
        elements.append(report_date)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Personal Information Section
        personal_heading = Paragraph("Personal Information", heading_style)
        elements.append(personal_heading)
        
        personal_data = [
            ['Register Number:', student.get('register_number', 'N/A')],
            ['Student Name:', student.get('student_name', 'N/A')],
            ['Department:', student.get('department', 'N/A')],
            ['Date of Birth:', student.get('dob', 'N/A')],
            ['Gender:', student.get('gender', 'N/A')],
            ['Blood Group:', student.get('blood_group', 'N/A')],
            ['Father\'s Name:', student.get('father_name', 'N/A')],
            ['Mother\'s Name:', student.get('mother_name', 'N/A')],
            ['Phone Number:', student.get('student_phone', 'N/A')],
            ['Email:', student.get('gmail_id', 'N/A')],
            ['Address:', student.get('address', 'N/A')]
        ]
        
        personal_table = Table(personal_data, colWidths=[2.5 * inch, 4 * inch])
        personal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(personal_table)
        elements.append(Spacer(1, 0.4 * inch))
        
        # Academic Performance Section
        academic_heading = Paragraph("Academic Performance", heading_style)
        elements.append(academic_heading)
        
        if academic:
            academic_data = [['Semester', 'CGPA', 'Backlogs']]
            total_backlogs = 0
            cgpa_sum = 0
            cgpa_count = 0
            
            for i in range(1, 9):
                cgpa = academic.get(f'sem{i}_cgpa', 0.0)
                backlogs = academic.get(f'sem{i}_backlogs', 0)
                
                if cgpa and cgpa > 0:
                    cgpa_count += 1
                    cgpa_sum += float(cgpa)
                
                total_backlogs += int(backlogs)
                
                academic_data.append([
                    f'Semester {i}',
                    f'{cgpa:.2f}' if cgpa else 'N/A',
                    str(backlogs)
                ])
            
            # Add summary row
            overall_cgpa = (cgpa_sum / cgpa_count) if cgpa_count > 0 else 0
            academic_data.append([
                'Overall',
                f'{overall_cgpa:.2f}',
                str(total_backlogs)
            ])
            
            academic_table = Table(academic_data, colWidths=[2.5 * inch, 2 * inch, 2 * inch])
            academic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#05043e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(academic_table)
        else:
            elements.append(Paragraph("No academic data available.", styles['Normal']))
        
        elements.append(Spacer(1, 0.4 * inch))
        
        # Attendance Section
        attendance_heading = Paragraph("Attendance Records", heading_style)
        elements.append(attendance_heading)
        
        if attendance:
            attendance_data = [['Semester', 'Attendance (%)']]
            total_attendance = 0
            
            for i in range(1, 9):
                att = attendance.get(f'sem{i}_attendance', 100)
                total_attendance += float(att)
                
                attendance_data.append([
                    f'Semester {i}',
                    f'{att:.1f}%'
                ])
            
            # Add average
            avg_attendance = total_attendance / 8
            attendance_data.append([
                'Average',
                f'{avg_attendance:.1f}%'
            ])
            
            attendance_table = Table(attendance_data, colWidths=[3 * inch, 3.5 * inch])
            attendance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#05043e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(attendance_table)
        else:
            elements.append(Paragraph("No attendance data available.", styles['Normal']))
        
        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        footer = Paragraph(
            "<para alignment='center'><font size=8 color='grey'>This is a computer-generated report. No signature required.</font></para>",
            styles['Normal']
        )
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        return BytesIO(pdf)
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return None
