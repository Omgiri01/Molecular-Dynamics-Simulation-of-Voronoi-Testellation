from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, ListStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, ListFlowable, ListItem, Frame, PageTemplate)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas
import os
import datetime
import re

# Enhanced color scheme
COLORS = {
    'primary': '#1e40af',      # Rich blue
    'secondary': '#3b82f6',    # Bright blue
    'accent': '#60a5fa',       # Light blue
    'text': '#1f2937',         # Dark gray
    'light': '#f8fafc',        # Off-white
    'success': '#059669',      # Emerald
    'warning': '#d97706',      # Amber
    'danger': '#dc2626',       # Red
    'gray': '#6b7280',         # Medium gray
    'highlight': '#dbeafe',    # Light blue highlight
    'border': '#e5e7eb'        # Light gray border
}

# Helper to read markdown files and process them
def read_markdown_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Remove "Next Steps" sections
        content = re.sub(r'## Next Steps.*?(?=##|\Z)', '', content, flags=re.DOTALL)
        
        # Convert markdown headings to bold text
        content = re.sub(r'^#+\s+(.+)$', r'<b>\1</b>', content, flags=re.MULTILINE)
        
        # Remove asterisks from text
        content = re.sub(r'\*', '', content)
        
        # --- Robust table detection and splitting ---
        lines = content.split('\n')
        processed_content = []
        table_lines = []
        in_table = False
        for line in lines:
            # Detect start of a markdown table (header row)
            if re.match(r'^\|?\s*[-\w ]+\s*\|', line) and '|' in line and not in_table:
                in_table = True
                table_lines = [line]
            elif in_table:
                if '|' in line:
                    table_lines.append(line)
                else:
                    # End of table
                    if len(table_lines) > 1:
                        processed_content.append(process_markdown_table(table_lines))
                    table_lines = []
                    in_table = False
                    if line.strip():
                        processed_content.append(line)
            else:
                if line.strip():
                    processed_content.append(line)
        # If file ends with a table
        if in_table and len(table_lines) > 1:
            processed_content.append(process_markdown_table(table_lines))

        return processed_content
    except Exception as e:
        return f"[Could not read {filepath}: {e}]"

def process_markdown_table(table_lines):
    """Process markdown table into a visually appealing ReportLab table."""
    # Remove header separator line
    table_lines = [line for line in table_lines if not line.startswith('|-')]

    # Process each line
    data = []
    for line in table_lines:
        cells = [cell.strip().replace('*', '') for cell in line.strip('|').split('|')]
        cells = [cell.strip() for cell in cells]
        if len(cells) > 1:
            cells[1] = cells[1].replace(' ', '')
        data.append(cells)

    # Set larger, proportional column widths
    col_widths = [100, 160, 110]  # Timestep, Displacement, Phase
    table = Table(data, colWidths=col_widths)

    # Define styles
    styles = [
        # Header style
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primary'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),

        # Grid lines
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(COLORS['primary'])),

        # Cell padding
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),

        # Column alignments
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Timestep
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Displacement
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Phase

        # Font settings for data
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
    ]

    # Add alternating row colors for readability
    for i in range(1, len(data)):
        if i % 2 == 1:
            styles.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(COLORS['light'])))
        else:
            styles.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor(COLORS['light'])))

    # Add phase-based highlight (optional, can be commented out if not needed)
    for i, row in enumerate(data[1:], 1):
        phase = row[2].strip().lower()
        if phase == 'initial':
            styles.append(('TEXTCOLOR', (2, i), (2, i), colors.HexColor(COLORS['secondary'])))
        elif phase == 'transition':
            styles.append(('TEXTCOLOR', (2, i), (2, i), colors.HexColor(COLORS['warning'])))
        elif phase == 'final':
            styles.append(('TEXTCOLOR', (2, i), (2, i), colors.HexColor(COLORS['success'])))

    table.setStyle(TableStyle(styles))
    return table

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Voronoi2 Project Report   |   Page {page_num}"
    canvas.setFont('Helvetica-Bold', 11)
    canvas.setFillColor(colors.HexColor(COLORS['primary']))
    canvas.drawRightString(7.5*inch, 0.65*inch, text)

def make_toc_entry(text, level=0):
    return Paragraph(
        f'<font size="15" color="{COLORS["primary"]}"><b>{text}</b></font>',
        ParagraphStyle(
            'TOCEntry',
            leftIndent=level*20,
            spaceAfter=14,
            spaceBefore=6,
            fontName='Helvetica-Bold'
        )
    )

def create_project_report():
    try:
        print("Building PDF...")
        if not os.path.exists("results"):
            os.makedirs("results")
        output_path = "results/project_report.pdf"

        # Enhanced styles with optimized spacing
        styles = getSampleStyleSheet()
        
        # Cover page styles
        styles.add(ParagraphStyle(
            name='CoverTitle',
            fontSize=44,
            leading=48,
            alignment=TA_CENTER,
            spaceAfter=24,
            textColor=colors.HexColor(COLORS['primary']),
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='CoverSub',
            fontSize=26,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor(COLORS['secondary']),
            fontName='Helvetica'
        ))
        
        styles.add(ParagraphStyle(
            name='CoverMeta',
            fontSize=15,
            alignment=TA_CENTER,
            spaceAfter=8,
            textColor=colors.HexColor(COLORS['gray']),
            fontName='Helvetica'
        ))

        # Section styles
        styles.add(ParagraphStyle(
            name='SectionHeading',
            fontSize=30,
            leading=34,
            spaceAfter=20,
            spaceBefore=24,
            textColor=colors.HexColor(COLORS['primary']),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='SubHeading',
            fontSize=20,
            leading=24,
            spaceAfter=12,
            spaceBefore=16,
            textColor=colors.HexColor(COLORS['secondary']),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))

        # Body text styles
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            leading=16,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            textColor=colors.HexColor(COLORS['text'])
        ))

        # Table styles
        styles.add(ParagraphStyle(
            name='TableHeader',
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.white,
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='TableCell',
            fontSize=12,
            alignment=TA_LEFT,
            spaceAfter=6,
            spaceBefore=6,
            fontName='Helvetica'
        ))

        # Image caption style
        styles.add(ParagraphStyle(
            name='ImageCaption',
            fontSize=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor(COLORS['gray']),
            spaceAfter=16,
            spaceBefore=6,
            fontName='Helvetica-Oblique'
        ))

        # List style
        styles.add(ListStyle(
            name='BulletList',
            leftIndent=24,
            bulletIndent=16,
            bulletFontName='Helvetica',
            bulletFontSize=16,
            spaceAfter=8
        ))

        # Document setup with compact margins
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=48,
            bottomMargin=48
        )

        def on_page(canvas, doc):
            add_page_number(canvas, doc)
            
            canvas.setStrokeColor(colors.HexColor(COLORS['accent']))
            canvas.setLineWidth(2)
            canvas.line(36, 750, 550, 750)
            
            canvas.setFillColor(colors.HexColor(COLORS['highlight']))
            canvas.rect(36, 750, 514, 16, fill=1, stroke=0)

        story = []

        # --- COVER PAGE ---
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("Voronoi Polycrystal Molecular Dynamics Simulation", styles['CoverTitle']))
        story.append(Paragraph("Comprehensive Project Report", styles['CoverSub']))
        story.append(Spacer(1, 0.75*inch))
        story.append(Paragraph(f"Author: <b>Your Name</b>", styles['CoverMeta']))
        story.append(Paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}", styles['CoverMeta']))
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("<i>Generated automatically using Python and ReportLab</i>", styles['CoverMeta']))
        story.append(PageBreak())

        # --- TABLE OF CONTENTS ---
        story.append(Paragraph("Table of Contents", styles['SectionHeading']))
        story.append(Spacer(1, 0.5*inch))
        
        toc_entries = [
            ("Project Overview", 0),
            ("Software and Tools Used", 0),
            ("Project Structure", 0),
            ("Results and Visualizations", 0),
            ("Dislocation Evolution Report", 0),
            ("Dislocation Study Report", 0),
            ("Deformation Report", 0)
        ]
        
        for entry, level in toc_entries:
            story.append(make_toc_entry(entry, level))
        
        story.append(PageBreak())

        # --- PROJECT OVERVIEW ---
        story.append(Paragraph("Project Overview", styles['SectionHeading']))
        story.append(Paragraph(
            "This project focuses on generating a Voronoi polycrystal structure, simulating its deformation using LAMMPS, "
            "and analyzing the evolution of dislocations and grain structure. The project combines molecular dynamics "
            "simulation with advanced analysis techniques to study material behavior under deformation.",
            styles['CustomBody']
        ))
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph("<hr width='100%' color='#60a5fa'/>", styles['CustomBody']))

        # --- SOFTWARE AND TOOLS ---
        story.append(Paragraph("Software and Tools Used", styles['SectionHeading']))
        software_list = [
            ["Software", "Purpose", "Version"],
            ["Atomsk", "Structure Generation", "Latest"],
            ["LAMMPS", "Molecular Dynamics Simulation", "Latest"],
            ["OVITO/VMD", "Visualization", "Latest"],
            ["Python", "Analysis and Scripting", "3.x"],
            ["NumPy", "Numerical Computing", "≥1.21.0"],
            ["SciPy", "Scientific Computing", "≥1.7.0"],
            ["Matplotlib", "Data Visualization", "≥3.4.0"],
            ["ASE", "Atomic Simulation Environment", "Latest"]
        ]
        
        t = Table(software_list, colWidths=[2*inch, 3*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(COLORS['light'])),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(COLORS['text'])),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(COLORS['primary'])),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(COLORS['highlight'])]),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8)
        ]))
        
        story.append(t)
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph("<hr width='100%' color='#60a5fa'/>", styles['CustomBody']))

        # --- PROJECT STRUCTURE ---
        story.append(Paragraph("Project Structure", styles['SectionHeading']))
        structure_list = [
            ["Directory", "Purpose"],
            ["scripts/", "Python scripts for structure generation and analysis"],
            ["inputs/", "LAMMPS input files and potential files"],
            ["outputs/", "Raw simulation outputs and initial data"],
            ["results/", "Final analysis outputs and visualizations"],
            ["studies/", "Supplementary analysis files"],
            ["bin/", "Executable files (e.g., Atomsk)"]
        ]
        t = Table(structure_list, colWidths=[2*inch, 4.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 13),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(COLORS['light'])),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(COLORS['text'])),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(COLORS['primary'])),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(COLORS['light'])])
        ]))
        story.append(t)
        story.append(Spacer(1, 12))
        story.append(Paragraph("<hr width='100%' color='#60a5fa'/>", styles['CustomBody']))

        # --- RESULTS AND VISUALIZATIONS ---
        story.append(PageBreak())
        story.append(Paragraph("Results and Visualizations", styles['SectionHeading']))
        image_files = [
            ("Stress-Strain Curve", "results/stress_strain_curve.png", 
             "The stress-strain curve shows the material's response to applied deformation, including elastic and plastic regions."),
            ("Dislocation Evolution", "results/dislocation_evolution.png",
             "Evolution of dislocation density and distribution over time during deformation."),
            ("Strain-Dislocation Correlation", "results/strain_dislocation_correlation.png",
             "Correlation between applied strain and dislocation density, showing work hardening behavior."),
            ("Voronoi Structure with Dislocations", "results/voronoi_dislocations.png",
             "Visualization of the Voronoi polycrystal structure with identified dislocations."),
            ("CSP Distribution", "results/csp_distribution.png",
             "Distribution of Centro-Symmetry Parameter (CSP) values indicating defect regions.")
        ]
        for caption, img_path, description in image_files:
            if os.path.exists(img_path):
                story.append(Spacer(1, 18))
                story.append(Image(img_path, width=6*inch, height=4*inch))
                story.append(Paragraph(f"<b>{caption}</b>", styles['ImageCaption']))
                story.append(Paragraph(description, styles['CustomBody']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<hr width='100%' color='#60a5fa'/>", styles['CustomBody']))

        # --- STUDIES AND RESULTS (MARKDOWN) ---
        md_files = [
            ("Dislocation Evolution Report", "results/dislocation_evolution_report.md"),
            ("Dislocation Study Report", "results/dislocation_study_report.md"),
            ("Deformation Report", "results/deformation_report.md")
        ]
        for section_title, md_path in md_files:
            story.append(PageBreak())
            story.append(Paragraph(section_title, styles['SectionHeading']))
            md_content = read_markdown_file(md_path)
            if isinstance(md_content, list):
                for item in md_content:
                    if isinstance(item, Table):
                        story.append(item)
                        story.append(Spacer(1, 18))
                    else:
                        for para in item.split('\n\n'):
                            if para.strip():
                                story.append(Paragraph(para.replace('\n', '<br/>'), styles['CustomBody']))
                                story.append(Spacer(1, 8))
            else:
                for para in md_content.split('\n\n'):
                    if para.strip():
                        story.append(Paragraph(para.replace('\n', '<br/>'), styles['CustomBody']))
                        story.append(Spacer(1, 8))
            story.append(Spacer(1, 16))

        print("Building PDF...")
        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
        print(f"PDF successfully generated at: {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise

if __name__ == "__main__":
    create_project_report() 