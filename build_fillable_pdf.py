#!/usr/bin/env python3
"""
Creates a fillable PDF reproduction of the Panda Special Assistance Information Form.
Faithfully matches layout: PANDA header, title, body paragraphs, underline fields,
5-line description area, confidentiality notice, date & signature, footer.
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

PAGE_W, PAGE_H = letter   # 612 x 792 points
LM = 72                    # left margin
RM = 72                    # right margin
UW = PAGE_W - LM - RM     # usable width = 468 pt

OUTPUT = "/home/user/Various/Panda - Special Assistance Information Form - Fillable.pdf"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wrap_text(c, text, font_name, font_size, max_w):
    """Return list of strings that each fit within max_w points."""
    words = text.split()
    lines, line, line_w = [], [], 0.0
    sp_w = c.stringWidth(" ", font_name, font_size)
    for word in words:
        ww = c.stringWidth(word, font_name, font_size)
        add = ww if not line else sp_w + ww
        if line_w + add <= max_w:
            line.append(word)
            line_w += add
        else:
            if line:
                lines.append(" ".join(line))
            line, line_w = [word], ww
    if line:
        lines.append(" ".join(line))
    return lines


def draw_justified(c, text, x, y, font_name, font_size, width, last=False):
    """Justify text to `width`; left-align if it's the last line or single word."""
    c.setFont(font_name, font_size)
    words = text.split()
    if last or len(words) <= 1:
        c.drawString(x, y, text)
        return
    total_word_w = sum(c.stringWidth(w, font_name, font_size) for w in words)
    gap = (width - total_word_w) / (len(words) - 1)
    cx = x
    for w in words:
        c.drawString(cx, y, w)
        cx += c.stringWidth(w, font_name, font_size) + gap


def add_field(c, name, tooltip, x, y, w, h, multiline=False):
    """
    Add a transparent, no-border fillable text field.
    Canvas underlines drawn before calling this serve as visual guides.
    fillColor=None and borderColor=None make the widget background transparent.
    """
    c.acroForm.textfield(
        name=name,
        tooltip=tooltip,
        x=x, y=y,
        width=w, height=h,
        borderStyle='solid',
        borderColor=None,   # no border drawn (MK/BC omitted)
        fillColor=None,     # no fill drawn (MK/BG omitted) → transparent
        fontSize=11,
        fontName='Times-Roman',
        textColor=colors.black,
        fieldFlags='multiline' if multiline else '',
        forceBorder=False,
        relative=False,
    )


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def create_pdf():
    c = canvas.Canvas(OUTPUT, pagesize=letter)
    c.setTitle("Panda Condos Special Assistance Information Form")
    c.setAuthor("TSCC 2920 Panda Condos")
    c.setSubject("Persons Requiring Special Assistance Information Form")

    LH = 15   # standard line height (points)

    # -----------------------------------------------------------------------
    # HEADER – "PANDA" with letter-spacing  +  "CONDOMINIUMS" beneath
    # -----------------------------------------------------------------------
    panda_font, panda_sz = "Helvetica-Bold", 38
    c.setFont(panda_font, panda_sz)
    letters = list("PANDA")
    extra_gap = 10   # extra points between each letter
    lwidths = [c.stringWidth(ch, panda_font, panda_sz) for ch in letters]
    total_w = sum(lwidths) + extra_gap * (len(letters) - 1)
    px = (PAGE_W - total_w) / 2
    py = PAGE_H - 68
    for i, ch in enumerate(letters):
        c.drawString(px, py, ch)
        px += lwidths[i] + extra_gap

    c.setFont("Helvetica", 7.5)
    condo_str = "C O N D O M I N I U M S"
    condo_w = c.stringWidth(condo_str, "Helvetica", 7.5)
    c.drawString((PAGE_W - condo_w) / 2, PAGE_H - 83, condo_str)

    # -----------------------------------------------------------------------
    # TITLE – Times-Bold 13pt, centred, underlined
    # -----------------------------------------------------------------------
    title_str = "PERSONS REQUIRING SPECIAL ASSISTANCE INFORMATION FORM"
    c.setFont("Times-Bold", 13)
    title_w = c.stringWidth(title_str, "Times-Bold", 13)
    tx = (PAGE_W - title_w) / 2
    ty = PAGE_H - 120
    c.drawString(tx, ty, title_str)
    c.setLineWidth(0.75)
    c.line(tx, ty - 2, tx + title_w, ty - 2)

    # -----------------------------------------------------------------------
    # SUBTITLE – Times-Italic 10.5pt, centred
    # -----------------------------------------------------------------------
    sub_str = "[Please Complete and Return this Form to Property Management as soon as possible]"
    c.setFont("Times-Italic", 10.5)
    sub_w = c.stringWidth(sub_str, "Times-Italic", 10.5)
    c.drawString((PAGE_W - sub_w) / 2, PAGE_H - 144, sub_str)

    # -----------------------------------------------------------------------
    # PARAGRAPH 1 – mixed bold / regular, justified
    # Line 1: [BOLD prefix] + [regular words stretched to right margin]
    # Line 2: [regular, justified]
    # Line 3: [regular, last line – left-aligned]
    # -----------------------------------------------------------------------
    y = PAGE_H - 172

    bold_prefix = "As required in the condominium corporation’s Fire Safety Plan,"
    c.setFont("Times-Bold", 11)
    bpw = c.stringWidth(bold_prefix, "Times-Bold", 11)
    c.drawString(LM, y, bold_prefix)
    # Continue on same line with natural (non-stretched) regular text
    c.setFont("Times-Roman", 11)
    c.drawString(LM + bpw, y, " and in order to ensure the")

    y -= LH
    draw_justified(c,
        "safety of all residents during any emergency in the building, we are asking for your co-",
        LM, y, "Times-Roman", 11, UW, last=False)

    y -= LH
    c.setFont("Times-Roman", 11)
    c.drawString(LM, y, "operation.")

    # -----------------------------------------------------------------------
    # PARAGRAPH 2 – Times-Roman 11pt, justified
    # -----------------------------------------------------------------------
    y -= LH * 1.7
    para2 = ("If you have any person residing in your unit who would require special assistance during "
             "evacuation or any emergency, please fill in the information on this form below.")
    p2_lines = wrap_text(c, para2, "Times-Roman", 11, UW)
    for i, ln in enumerate(p2_lines):
        draw_justified(c, ln, LM, y, "Times-Roman", 11, UW, last=(i == len(p2_lines) - 1))
        y -= LH

    # -----------------------------------------------------------------------
    # LABELLED FIELDS – FULL NAME / UNIT # / TELEPHONE #
    # Block indented to x=130; underlines extend to right margin.
    # -----------------------------------------------------------------------
    FI       = 130           # left edge of label block
    FE       = PAGE_W - RM   # right edge of field underlines (540 pt)
    FIELD_H  = 15            # height of each single-line widget
    FIELD_ROW = 26           # vertical step between field rows

    y -= 32   # gap before the block

    def labelled_field(label, name, tooltip, yy):
        c.setFont("Times-Bold", 11)
        lw = c.stringWidth(label, "Times-Bold", 11)
        c.drawString(FI, yy, label)
        fx = FI + lw + 8
        fw = FE - fx
        # canvas underline
        c.setLineWidth(0.5)
        c.line(fx, yy - 2, fx + fw, yy - 2)
        # invisible (transparent) fillable field above the underline
        add_field(c, name, tooltip, fx, yy - FIELD_H, fw, FIELD_H)

    labelled_field("FULL NAME:",   "FullName",   "Full Name",        y)
    y -= FIELD_ROW
    labelled_field("UNIT #:",      "UnitNumber", "Unit Number",      y)
    y -= FIELD_ROW
    labelled_field("TELEPHONE #:", "Telephone",  "Telephone Number", y)

    # -----------------------------------------------------------------------
    # BRIEF DESCRIPTION label (mixed bold/regular) + 5 ruled lines
    # -----------------------------------------------------------------------
    y -= 32

    c.setFont("Times-Bold", 11)
    bd_lbl = "Brief description"
    bd_lw = c.stringWidth(bd_lbl, "Times-Bold", 11)
    c.drawString(LM, y, bd_lbl)
    c.setFont("Times-Roman", 11)
    c.drawString(LM + bd_lw, y,
        " (i.e., difficulty walking, wheelchair, special breathing apparatus, bedridden,")

    y -= LH
    c.setFont("Times-Roman", 11)
    c.drawString(LM, y, "sprains/fractures, hearing or visually impaired).")

    # Five ruled lines
    y -= 22
    DESC_GAP = 27           # spacing between ruled lines
    desc_top_y = y          # y of the first rule

    c.setLineWidth(0.8)
    for i in range(5):
        c.line(LM, y, PAGE_W - RM, y)
        if i < 4:
            y -= DESC_GAP

    desc_bot_y = y          # y of the last rule

    # One transparent multiline field spanning all five rules
    desc_h = desc_top_y - desc_bot_y + 20
    add_field(c, "BriefDescription", "Brief description of assistance needs",
              LM, desc_bot_y - 8, UW, desc_h, multiline=True)

    y -= 36   # clear the last rule

    # -----------------------------------------------------------------------
    # CONFIDENTIALITY STATEMENT – Times-Italic 11pt, justified
    # -----------------------------------------------------------------------
    conf = ("All information received is kept in strict confidence and used only by authorized "
            "persons in case of an emergency.")
    conf_lines = wrap_text(c, conf, "Times-Italic", 11, UW)
    y -= 5
    for i, ln in enumerate(conf_lines):
        draw_justified(c, ln, LM, y, "Times-Italic", 11, UW, last=(i == len(conf_lines) - 1))
        y -= LH

    # -----------------------------------------------------------------------
    # DATE COMPLETED
    # -----------------------------------------------------------------------
    y -= 22
    c.setFont("Times-Roman", 11)
    dc_lbl = "Date Completed:"
    dc_lw  = c.stringWidth(dc_lbl, "Times-Roman", 11)
    c.drawString(LM, y, dc_lbl)
    dc_fx = LM + dc_lw + 8
    dc_fw = 230
    c.setLineWidth(0.5)
    c.line(dc_fx, y - 2, dc_fx + dc_fw, y - 2)
    add_field(c, "DateCompleted", "Date Completed", dc_fx, y - FIELD_H, dc_fw, FIELD_H)

    # -----------------------------------------------------------------------
    # RESIDENT SIGNATURE
    # -----------------------------------------------------------------------
    y -= 27
    c.setFont("Times-Roman", 11)
    rs_lbl = "Resident Signature:"
    rs_lw  = c.stringWidth(rs_lbl, "Times-Roman", 11)
    c.drawString(LM, y, rs_lbl)
    rs_fx = LM + rs_lw + 8
    rs_fw = 218
    c.setLineWidth(0.5)
    c.line(rs_fx, y - 2, rs_fx + rs_fw, y - 2)
    add_field(c, "ResidentSignature", "Resident Signature", rs_fx, y - FIELD_H, rs_fw, FIELD_H)

    # -----------------------------------------------------------------------
    # FOOTER – Times-Italic 10pt, centred
    # -----------------------------------------------------------------------
    footer = "TSCC 2920 Panda Condos Special Assistance Information Form"
    c.setFont("Times-Italic", 10)
    footer_w = c.stringWidth(footer, "Times-Italic", 10)
    c.drawString((PAGE_W - footer_w) / 2, 44, footer)

    c.save()
    return OUTPUT


if __name__ == "__main__":
    import os
    path = create_pdf()
    size_kb = os.path.getsize(path) / 1024
    print(f"Created : {path}")
    print(f"Size    : {size_kb:.1f} KB")
    print("Fields  : FullName, UnitNumber, Telephone, BriefDescription (multiline),")
    print("          DateCompleted, ResidentSignature")
