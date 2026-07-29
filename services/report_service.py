import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

class ReportService:
    """Service for generating downloadable PDF, CSV, and Excel reports."""

    @staticmethod
    def generate_candidate_pdf(candidate_data: dict, interview_data: list = None) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=15
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#2563EB'),
            spaceBefore=12,
            spaceAfter=8
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155')
        )

        # Header
        story.append(Paragraph("InterviewAI - Technical Assessment Report", title_style))
        story.append(Paragraph("Enterprise Candidate Resume & AI Interview Performance Summary", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#CBD5E1"), spaceAfter=15))

        # Candidate Details Table
        summary_table_data = [
            [Paragraph("<b>Candidate Name:</b>", body_style), Paragraph(candidate_data.get("name", "N/A"), body_style),
             Paragraph("<b>Target Role:</b>", body_style), Paragraph(candidate_data.get("target_role", "Python Developer"), body_style)],
            [Paragraph("<b>Email:</b>", body_style), Paragraph(candidate_data.get("email", "N/A"), body_style),
             Paragraph("<b>Resume Score:</b>", body_style), Paragraph(f"<b>{candidate_data.get('resume_score', 0)}/100</b>", body_style)],
            [Paragraph("<b>Experience:</b>", body_style), Paragraph(f"{candidate_data.get('experience_years', 0)} Years", body_style),
             Paragraph("<b>Education:</b>", body_style), Paragraph(candidate_data.get("education", "B.S. CS"), body_style)]
        ]

        t = Table(summary_table_data, colWidths=[110, 160, 100, 170])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

        # Skills & Analysis
        story.append(Paragraph("Parsed Technical Skills", section_heading))
        skills_text = ", ".join(candidate_data.get("parsed_skills", [])) or "None detected"
        story.append(Paragraph(skills_text, body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("Skill Gap & Missing Skills", section_heading))
        missing_text = ", ".join(candidate_data.get("missing_skills", [])) or "No major gaps identified"
        story.append(Paragraph(missing_text, body_style))
        story.append(Spacer(1, 15))

        # Interview Session Scores
        if interview_data:
            story.append(Paragraph("Recent AI Mock Interview Performance", section_heading))
            session_headers = [Paragraph("<b>Date</b>", body_style), Paragraph("<b>Role / Topic</b>", body_style), Paragraph("<b>Score</b>", body_style), Paragraph("<b>Status</b>", body_style)]
            session_rows = [session_headers]
            for sess in interview_data:
                session_rows.append([
                    Paragraph(str(sess.get("created_at", "")[:10]), body_style),
                    Paragraph(str(sess.get("role_title", "")), body_style),
                    Paragraph(f"{sess.get('overall_score', 0)}%", body_style),
                    Paragraph(str(sess.get("status", "")).capitalize(), body_style)
                ])
            st = Table(session_rows, colWidths=[100, 240, 100, 100])
            st.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EFF6FF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(st)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def export_candidates_csv(candidates: list) -> str:
        df = pd.DataFrame(candidates)
        return df.to_csv(index=False)

    @staticmethod
    def export_candidates_excel(candidates: list) -> bytes:
        df = pd.DataFrame(candidates)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Candidates')
        output.seek(0)
        return output.getvalue()
