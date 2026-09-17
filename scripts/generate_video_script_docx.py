"""
Generates a clean, professional Word document (.docx) for the
Multimodal HCI Demonstration Video Plan and Voiceover Script.
Strictly adheres to:
- Standard 1-inch margins
- Clean typography (Calibri body, clean headings)
- Formatted overview table with slate headers
- Distinct callout styling for Visual Cues and Voiceover Scripts
- Zero emojis or artificial fluff
"""

from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls


def set_cell_background(cell, fill_hex: str):
    """Sets background fill color for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    """Sets cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def set_table_borders(table, color="CBD5E1", sz="4"):
    """Sets subtle light-grey borders for clean professional tables."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def add_voiceover_box(doc, script_text: str):
    """Adds a callout box for the spoken voiceover text."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:left w:val="single" w:sz="16" w:space="0" w:color="2563EB"/>'
        f'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

    p_lbl = cell.paragraphs[0]
    p_lbl.paragraph_format.space_before = Pt(0)
    p_lbl.paragraph_format.space_after = Pt(3)
    r_lbl = p_lbl.add_run("Spoken Voiceover Script:")
    r_lbl.font.name = "Calibri"
    r_lbl.font.size = Pt(9.5)
    r_lbl.font.bold = True
    r_lbl.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)

    p_txt = cell.add_paragraph()
    p_txt.paragraph_format.space_before = Pt(0)
    p_txt.paragraph_format.space_after = Pt(2)
    p_txt.paragraph_format.line_spacing = 1.15
    r_txt = p_txt.add_run(f'"{script_text}"')
    r_txt.font.name = "Calibri"
    r_txt.font.size = Pt(10)
    r_txt.font.italic = True
    r_txt.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(4)


def add_heading_1(doc, text: str):
    """Adds a Level 1 heading."""
    h = doc.add_heading(level=1)
    h.paragraph_format.space_before = Pt(16)
    h.paragraph_format.space_after = Pt(4)
    run = h.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(13.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    return h


def add_heading_2(doc, text: str):
    """Adds a Level 2 heading."""
    h = doc.add_heading(level=2)
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(3)
    run = h.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    return h


def add_heading_3(doc, text: str):
    """Adds a Level 3 heading."""
    h = doc.add_heading(level=3)
    h.paragraph_format.space_before = Pt(8)
    h.paragraph_format.space_after = Pt(2)
    run = h.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(10.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    return h


def build_video_script_document():
    doc = Document()

    # 1. Page Margins (Standard 1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Base Styles
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    # =========================================================================
    # HEADER / TITLE BLOCK
    # =========================================================================
    p_proj = doc.add_paragraph()
    p_proj.paragraph_format.space_before = Pt(0)
    p_proj.paragraph_format.space_after = Pt(2)
    r_proj = p_proj.add_run("Self-Evaluating Adaptive Multimodal Decision & Assessment Architecture")
    r_proj.font.name = "Calibri"
    r_proj.font.size = Pt(16)
    r_proj.font.bold = True
    r_proj.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p_subm = doc.add_paragraph()
    p_subm.paragraph_format.space_before = Pt(0)
    p_subm.paragraph_format.space_after = Pt(8)
    r_subm = p_subm.add_run("Submitted By \u2013 Gowshick S (23BCE1200)")
    r_subm.font.name = "Calibri"
    r_subm.font.size = Pt(11.5)
    r_subm.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    p_doc_title = doc.add_paragraph()
    p_doc_title.paragraph_format.space_before = Pt(0)
    p_doc_title.paragraph_format.space_after = Pt(10)
    r_doc_title = p_doc_title.add_run("Demonstration Video Plan and Spoken Voiceover Script")
    r_doc_title.font.name = "Calibri"
    r_doc_title.font.size = Pt(13)
    r_doc_title.font.bold = True
    r_doc_title.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)

    # Metadata Panel
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    col_widths = [Inches(3.25), Inches(3.25)]

    meta_data = [
        [("Target Duration", "4 Minutes to 4 Minutes 30 Seconds"),
         ("Recording Format", "Full-Screen Display Capture + Microphone Voiceover")],
        [("Evaluation Scope", "Profile Calibration + 8 Testbench Interaction States"),
         ("Prerequisites", "Single Standard USB RGB Webcam, Test Bench Suite running at localhost:8080")]
    ]

    for r_idx, row in enumerate(meta_data):
        for c_idx, (label, val) in enumerate(row):
            cell = meta_table.cell(r_idx, c_idx)
            cell.width = col_widths[c_idx]
            set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r_lbl = p.add_run(f"{label}: ")
            r_lbl.font.bold = True
            r_lbl.font.size = Pt(9.5)
            r_lbl.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
            r_val = p.add_run(val)
            r_val.font.size = Pt(9.5)
            r_val.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    set_table_borders(meta_table, color="E2E8F0", sz="4")

    doc.add_paragraph().paragraph_format.space_before = Pt(6)

    # =========================================================================
    # SECTION 1: VIDEO STRUCTURE OVERVIEW
    # =========================================================================
    add_heading_1(doc, "1. Video Structure and Scene Timeline Overview")

    doc.add_paragraph(
        "The presentation is organized into five chronological segments designed for fluid pacing and complete technical coverage:"
    )

    t_headers = ["Scene", "Section Title", "Timestamp", "Visual Cue / Screen Display", "Core Presentation Objective"]
    t_rows = [
        ["Scene 1", "Introduction & Identification", "0:00 - 0:20 (20s)", "Title slide or IDE showing Project Title & Name", "Establish identity, credentials, and project title."],
        ["Scene 2", "Problem Statement & Proposed Solution", "0:20 - 0:50 (30s)", "Six-layer architectural flow diagram", "Concise 30s elevator pitch addressing Midas Touch & OS safety."],
        ["Scene 3", "User Profile Creation & Calibration", "0:50 - 1:30 (40s)", "Fullscreen 9-Point Desktop Calibration GUI", "Demonstrate personalized eye-gaze and head pose calibration."],
        ["Scene 4", "Interactive Test Bench (All 8 States)", "1:30 - 3:45 (135s)", "Live Test Bench Suite (localhost:8080)", "Step-by-step verification of all 8 target interaction scenarios."],
        ["Scene 5", "Quantitative Benchmarks & Conclusion", "3:45 - 4:15 (30s)", "Benchmark tables (PROJECT_RESULTS...docx)", "Present 15.27 ms latency, 65.5 FPS, and 94/94 test pass rate."]
    ]

    table_overview = doc.add_table(rows=len(t_rows) + 1, cols=len(t_headers))
    table_overview.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_overview.autofit = False

    t_widths = [Inches(0.8), Inches(1.7), Inches(1.1), Inches(1.7), Inches(1.7)]

    for c_idx, h_text in enumerate(t_headers):
        cell = table_overview.cell(0, c_idx)
        cell.width = t_widths[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=100, bottom=100, left=80, right=80)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(h_text)
        run.font.bold = True
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row_vals in enumerate(t_rows):
        is_even = (r_idx % 2 == 0)
        bg_color = "FFFFFF" if is_even else "F8FAFC"
        for c_idx, val in enumerate(row_vals):
            cell = table_overview.cell(r_idx + 1, c_idx)
            cell.width = t_widths[c_idx]
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(val)
            run.font.size = Pt(8.5)
            if c_idx == 0:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
            else:
                run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    set_table_borders(table_overview, color="CBD5E1", sz="4")

    # =========================================================================
    # SECTION 2: DETAILED SCENE-BY-SCENE SCRIPT
    # =========================================================================
    add_heading_1(doc, "2. Detailed Scene-by-Scene Script and Execution Instructions")

    # Scene 1
    add_heading_2(doc, "Scene 1: Introduction & Identification (0:00 - 0:20)")
    p_vis = doc.add_paragraph()
    r_vlbl = p_vis.add_run("On-Screen Visual Action: ")
    r_vlbl.font.bold = True
    p_vis.add_run("Display the title slide or clean header in your presentation window showing: Project Title, Gowshick S, and 23BCE1200.")
    add_voiceover_box(
        doc,
        "Hello everyone. My name is Gowshick S, registration number 23BCE1200. Today, I am presenting my project: "
        "the Self-Evaluating Adaptive Multimodal Decision and Assessment Architecture for Human-Computer Interaction."
    )

    # Scene 2
    add_heading_2(doc, "Scene 2: Problem Statement & Proposed Solution (0:20 - 0:50)")
    p_vis = doc.add_paragraph()
    r_vlbl = p_vis.add_run("On-Screen Visual Action: ")
    r_vlbl.font.bold = True
    p_vis.add_run("Display the six-layer architectural flow diagram illustrating Eye Gaze, Head Orientation, and Hand Kinematics fusing into the Modality Arbiter and Command Composer.")
    add_voiceover_box(
        doc,
        "Traditional hands-free computing suffers from three major limitations: first, the Midas Touch problem, where natural eye gaze "
        "accidentally clicks everything you look at; second, ocular micro-jitter that causes target instability; and third, the safety hazard "
        "of raw computer vision directly hijacking the operating system mouse cursor.\n\n"
        "To solve this, I designed a closed-loop multimodal architecture. It uses a single standard webcam to track eye gaze, head orientation, "
        "and hand kinematics simultaneously. Actions are only executed when an eye-gaze target anchor is confirmed by a discrete physical gesture, "
        "like an index pinch. Furthermore, all evaluations run safely inside a dedicated, sandboxed browser testbench, completely eliminating "
        "operating system hijacking."
    )

    # Scene 3
    add_heading_2(doc, "Scene 3: User Profile Creation & Calibration Wizard (0:50 - 1:30)")
    p_vis = doc.add_paragraph()
    r_vlbl = p_vis.add_run("On-Screen Visual Action: ")
    r_vlbl.font.bold = True
    p_vis.add_run("In the PowerShell terminal, execute: python -m src.calibration.calibration_wizard default_user. Show the fullscreen 9-point calibration grid with animated pacing dots, followed by the verification pass.")
    add_voiceover_box(
        doc,
        "The first step in our workflow is User Profile Creation and Calibration.\n\n"
        "Every user possesses unique eye geometry, interpupillary distance, and resting head angles. By launching our desktop calibration wizard, "
        "the system guides the user through a paced 9-point fixation grid, followed by a 5-point verification pass.\n\n"
        "In the background, our solver computes a coupled affine transformation matrix and estimates the resting head pose covariance. Once completed, "
        "it stores these parameters directly into the user's isolated JSON profile under data/profiles, achieving an average gaze error of just 18 pixels on a full HD screen."
    )

    # Scene 4
    add_heading_2(doc, "Scene 4: Interactive Test Bench Demonstration - All 8 States (1:30 - 3:45)")
    p_vis = doc.add_paragraph()
    r_vlbl = p_vis.add_run("On-Screen Visual Action: ")
    r_vlbl.font.bold = True
    p_vis.add_run("In terminal, run: python scripts/run_testbench.py --user default_user. The browser automatically opens http://127.0.0.1:8080 showing the dark Test Bench Suite with the top telemetry bar and the responsive 8-card grid. Point out the live eye-gaze reticle.")

    # State 1
    add_heading_3(doc, "State 1: Primary Click & Discrete Counter (TC-TB-01) [1:30 - 1:45]")
    p_vis = doc.add_paragraph()
    p_vis.add_run("Action: ").font.bold = True
    p_vis.add_run("Focus gaze on Card 01 (Primary Click Target). Perform an index pinch. Show badge incrementing from 0 to 1, then 2. Deliberately perform a middle or ring pinch to demonstrate the yellow status bar rejection warning.")
    add_voiceover_box(
        doc,
        "Now, we enter the live interactive testbench. Notice the green gaze reticle tracking my eye fixations at 60 frames per second. "
        "In Scenario 1, we verify primary click selection. I focus my gaze on the primary click target and execute an index pinch. "
        "The badge counter immediately increments by one. Notice our strict cross-finger disambiguation: if I accidentally pinch with my middle "
        "or ring finger, the system ignores it and alerts that Scenario 1 strictly requires an index pinch. This completely eliminates accidental traversal noise."
    )

    # State 2
    add_heading_3(doc, "State 2: Gaze Dwell Intentionality Trigger (TC-TB-02) [1:45 - 2:00]")
    p_vis = doc.add_paragraph()
    p_vis.add_run("Action: ").font.bold = True
    p_vis.add_run("Fixate gaze on Card 02 (Dwell Intentionality Target) with hands resting. Circular progress ring smoothly sweeps 360 degrees over 500 ms, pulses green, and confirms intent.")
    add_voiceover_box(
        doc,
        "In Scenario 2, we test hands-free dwell intentionality. Without using any hand gestures, I fixate my gaze on the circular target. "
        "A circular progress ring smoothly sweeps 360 degrees, confirming user intent after exactly 500 milliseconds. This enables entirely "
        "hands-free interaction for accessibility."
    )

    # State 3
    add_heading_3(doc, "State 3: Context Menu Secondary Click (TC-TB-03) [2:00 - 2:15]")
    p_vis = doc.add_paragraph()
    p_vis.add_run("Action: ").font.bold = True
    p_vis.add_run("Look at Card 03 (Context Menu Target). Perform a middle-finger pinch (PINCH_MIDDLE). The contextual popup menu immediately appears anchored to the gaze reticle.")
    add_voiceover_box(
        doc,
        "Scenario 3 validates secondary click functionality. I anchor my gaze on Target 3 and perform a middle-finger pinch. "
        "The system maps this token to a secondary right-click, instantly spawning a context menu precisely at my gaze coordinates."
    )

    # State 4
    add_heading_3(doc, "State 4: Text Input & Keyboard Handoff (TC-TB-04) [2:15 - 2:35]")
    p_vis = doc.add_paragraph()
    p_vis.add_run("Action: ").font.bold = True
    p_vis.add_run("Look at the text input field in Card 04 (Text Input & Keyboard Handoff). Perform an index pinch to focus the input. The yellow badge 'KEYBOARD ACTIVE [TYPING MODE]' appears. Type a few characters on your physical keyboard (e.g., 'Multimodal Test'). Point out the status bar showing multimodal clicks paused while typing. Defocus the input or perform a THUMBS_UP gesture to release handoff.")
    add_voiceover_box(
        doc,
        "In Scenario 4, we test Text Input and Keyboard Handoff. I look at the input field and perform an index pinch to focus it. "
        "The interface immediately activates typing mode, displaying the yellow keyboard active badge. While I type on my physical keyboard, "
        "all multimodal gaze clicks and gesture executions are temporarily paused to prevent interference. As soon as I finish typing and defocus "
        "or perform a thumbs-up gesture, multimodal tracking seamlessly resumes."
    )

    # State 5
    add_heading_3(doc, "State 5: Dropdown Option Selector (TC-TB-05) [2:35 - 2:50]")
    p_vis = doc.add_paragraph()
    p_vis.add_run("Action: ").font.bold = True
    p_vis.add_run("Look at dropdown header in Card 05 and pinch to expand. Look down at 'High Sensitivity Profile' (which highlights blue under gaze) and pinch. Dropdown collapses and updates label.")
    add_voiceover_box(
        doc,
        "Scenario 5 evaluates hierarchical dropdown selection. I fixate on the dropdown header and pinch to expand the list. I then shift my gaze "
        "down to select the High Sensitivity Profile, which highlights under visual fixation, and execute a confirmation pinch. The dropdown collapses with the updated selection."
    )

    # State 6
    add_heading_3(doc, "State 6: Continuous Kinetic Scroll Viewport (TC-TB-06) [2:50 - 3:10]")
    p_vis = doc.add_paragraph()
    p_vis.add_run("Action: ").font.bold = True
    p_vis.add_run("Gaze at Card 06 (Kinetic Scroll Viewport). With an open hand facing camera, perform a brisk downward flick (SWIPE_DOWN) to scroll down. Perform a brisk upward flick (SWIPE_UP) to scroll back up.")
    add_voiceover_box(
        doc,
        "Scenario 6 demonstrates kinetic viewport scrolling. While maintaining visual focus on Card 6, I perform a brisk downward hand flick. "
        "The wrist velocity exceeds our 1.2 units-per-second threshold, triggering a downward kinetic scroll. Flicking my hand upward smoothly "
        "scrolls the content back up. Dynamic velocity takes priority over static hover, making scrolling natural and responsive."
    )

    # State 7
    add_heading_3(doc, "State 7: Tier-2 High-Consequence Action Confirmation (TC-TB-07) [3:10 - 3:30]")
    p_vis = doc.add_paragraph()
    p_vis.add_run("Action: ").font.bold = True
    p_vis.add_run("Fixate gaze on Card 07 (Danger Reset Target). Show dwell ring filling. Look away early at 200 ms: show the ring aborting and resetting. Re-fixate and maintain gaze for full 600 ms: reset confirms.")
    add_voiceover_box(
        doc,
        "Scenario 7 demonstrates high-consequence safety protection for critical actions like system resets. When I look at the reset target, "
        "a 600-millisecond confirmation ring begins filling. If my gaze glances away early, the action aborts immediately, preventing catastrophic "
        "accidental triggers. Only when I maintain deliberate fixation through the full 360-degree sweep does the reset execute."
    )

    # State 8
    add_heading_3(doc, "State 8: Physical Mouse Takeover Override (TC-TB-08) [3:30 - 3:45]")
    p_vis = doc.add_paragraph()
    p_vis.add_run("Action: ").font.bold = True
    p_vis.add_run("Move your physical hardware mouse on your desk. Point out Card 08 (Physical Mouse Takeover Override) immediately activating with 'PHYSICAL MOUSE TAKEOVER ACTIVE' and the status updating to 'Hardware mouse moved -> Gaze yielded to mouse'.")
    add_voiceover_box(
        doc,
        "Finally, Scenario 8 demonstrates instantaneous physical mouse takeover. The moment I touch and nudge my physical hardware mouse, "
        "the arbiter immediately yields priority to the physical device. The interface updates to show mouse takeover active, guaranteeing "
        "that the user always maintains absolute, zero-latency manual override authority whenever desired."
    )

    # Scene 5
    add_heading_2(doc, "Scene 5: Quantitative Benchmarks & Conclusion (3:45 - 4:15)")
    p_vis = doc.add_paragraph()
    r_vlbl = p_vis.add_run("On-Screen Visual Action: ")
    r_vlbl.font.bold = True
    p_vis.add_run("Switch to the Evaluation Report document, showing Table 1 (15.27 ms end-to-end latency) and Table 4 (ISO 9241-411 comparison).")
    add_voiceover_box(
        doc,
        "To conclude, our architecture has been thoroughly verified through formal benchmarks.\n\n"
        "The total end-to-end pipeline latency is just 15.27 milliseconds, enabling sustained execution at 65.5 frames per second on standard "
        "commodity webcams without any expensive infrared hardware. Across 94 automated tests covering unit logic, integration flows, and microsecond "
        "benchmarks, our system achieved a 100% pass rate.\n\n"
        "By combining spatial gaze anchoring, discrete gesture confirmation, and a sandboxed browser testbed, we have achieved robust, hands-free "
        "multimodal interaction that completely eliminates Midas Touch errors and operating system hijacking.\n\n"
        "Thank you for your time and evaluation."
    )

    # =========================================================================
    # SECTION 3: PRACTICAL RECORDING CHECKLIST
    # =========================================================================
    add_heading_1(doc, "3. Practical Recording Checklist")

    checklist = [
        ("Camera Alignment: ", "Position your webcam directly at eye level, approximately 50 to 70 cm away in consistent, diffuse lighting."),
        ("One-Key Recenter: ", "If the gaze reticle feels offset at any time during live recording, simply press the key 'C' on your physical keyboard to re-zero the eye offset instantly."),
        ("Display Resolution: ", "Keep your browser display scaling at 100% on a 1920x1080 monitor so that all eight scenario cards fit cleanly without page scrolling."),
        ("Pacing: ", "Maintain a calm, conversational cadence of approximately 130 to 140 words per minute. Pause for half a second before each scenario gesture so viewers can observe your reticle fixating on the card.")
    ]
    for b_title, b_desc in checklist:
        bp = doc.add_paragraph(style="List Bullet")
        bp.paragraph_format.space_before = Pt(0)
        bp.paragraph_format.space_after = Pt(2)
        r_bt = bp.add_run(b_title)
        r_bt.font.bold = True
        bp.add_run(b_desc)

    out_path = Path("docs") / "presentation_video_plan_and_script.docx"
    try:
        doc.save(str(out_path))
        print(f"Successfully generated video script docx at: {out_path.resolve()}")
    except PermissionError:
        alt_path = Path("docs") / "presentation_video_plan_and_script_UPDATED.docx"
        doc.save(str(alt_path))
        print(f"File locked. Saved to: {alt_path.resolve()}")


if __name__ == "__main__":
    build_video_script_document()
