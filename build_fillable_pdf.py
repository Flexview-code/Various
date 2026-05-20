#!/usr/bin/env python3
"""
Creates a fillable PDF reproduction of the Panda Special Assistance Information Form.

Fixes applied vs. original script:
  1. Fields are positioned with their BOTTOM at the underline y-coordinate so
     typed text appears ABOVE (not under) the line — matching how you'd write
     on paper.
  2. ResidentSignature uses a proper PDF /Sig widget so Adobe Acrobat / any
     standard viewer will prompt for a digital signature instead of a text entry.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import pdfrw

PAGE_W, PAGE_H = letter   # 612 x 792 points
LM = 72                    # left margin
RM = 72                    # right margin
UW = PAGE_W - LM - RM     # usable width = 468 pt

OUTPUT = "/home/user/Various/Panda - Special Assistance Information Form - Fillable.pdf"
_TEMP   = "/home/user/Various/_panda_form_base.pdf"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wrap_text(c, text, font_name, font_size, max_w):
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


def add_text_field(c, name, tooltip, x, line_y, w, field_h=16, multiline=False):
    """
    Add a transparent fillable text field.

    `line_y` is the y-coordinate of the canvas underline.  The field is
    positioned so its BOTTOM sits at `line_y`, meaning the text input area
    extends UPWARD from the underline — the same as writing above a ruled line.
    """
    c.acroForm.textfield(
        name=name,
        tooltip=tooltip,
        x=x,
        y=line_y,          # bottom of widget = underline position → text above line
        width=w,
        height=field_h,
        borderStyle='solid',
        borderColor=None,   # no visible border (canvas underline is the visual guide)
        fillColor=None,     # transparent background
        fontSize=11,
        fontName='Times-Roman',
        textColor=colors.black,
        fieldFlags='multiline' if multiline else '',
        forceBorder=False,
        relative=False,
    )


# ---------------------------------------------------------------------------
# Phase 1 – build visual PDF + all text fields (signature field excluded)
# ---------------------------------------------------------------------------

def _build_base_pdf():
    """
    Draws everything except the signature widget.
    Returns the (x, y_line, x2, y_top) rectangle for the signature field so
    the pdfrw post-processing step can place it precisely.
    """
    c = canvas.Canvas(_TEMP, pagesize=letter)
    c.setTitle("Panda Condos Special Assistance Information Form")
    c.setAuthor("TSCC 2920 Panda Condos")
    c.setSubject("Persons Requiring Special Assistance Information Form")

    LH = 15   # body line height
    FIELD_H = 16

    # -----------------------------------------------------------------------
    # HEADER
    # -----------------------------------------------------------------------
    panda_font, panda_sz = "Times-Bold", 40
    c.setFont(panda_font, panda_sz)
    letters = list("PANDA")
    extra_gap = 7
    lwidths = [c.stringWidth(ch, panda_font, panda_sz) for ch in letters]
    total_w = sum(lwidths) + extra_gap * (len(letters) - 1)
    px = (PAGE_W - total_w) / 2
    py = PAGE_H - 68
    for i, ch in enumerate(letters):
        c.drawString(px, py, ch)
        px += lwidths[i] + extra_gap

    c.setFont("Times-Roman", 7.5)
    condo_str = "C O N D O M I N I U M S"
    condo_w = c.stringWidth(condo_str, "Times-Roman", 7.5)
    c.drawString((PAGE_W - condo_w) / 2, PAGE_H - 83, condo_str)

    # -----------------------------------------------------------------------
    # TITLE
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
    # SUBTITLE
    # -----------------------------------------------------------------------
    sub_str = "[Please Complete and Return this Form to Property Management as soon as possible]"
    c.setFont("Times-Italic", 10.5)
    sub_w = c.stringWidth(sub_str, "Times-Italic", 10.5)
    c.drawString((PAGE_W - sub_w) / 2, PAGE_H - 144, sub_str)

    # -----------------------------------------------------------------------
    # PARAGRAPH 1
    # -----------------------------------------------------------------------
    y = PAGE_H - 172

    bold_prefix = "As required in the condominium corporation's Fire Safety Plan,"
    c.setFont("Times-Bold", 11)
    bpw = c.stringWidth(bold_prefix, "Times-Bold", 11)
    c.drawString(LM, y, bold_prefix)
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
    # PARAGRAPH 2
    # -----------------------------------------------------------------------
    y -= LH * 1.7
    para2 = ("If you have any person residing in your unit who would require special assistance during "
             "evacuation or any emergency, please fill in the information on this form below.")
    p2_lines = wrap_text(c, para2, "Times-Roman", 11, UW)
    for i, ln in enumerate(p2_lines):
        draw_justified(c, ln, LM, y, "Times-Roman", 11, UW, last=(i == len(p2_lines) - 1))
        y -= LH

    # -----------------------------------------------------------------------
    # LABELLED FIELDS  (FULL NAME / UNIT # / TELEPHONE #)
    # The field bottom is placed at the underline y so text appears ABOVE the line.
    # -----------------------------------------------------------------------
    FI       = 130
    FE       = PAGE_W - RM
    FIELD_ROW = 26

    y -= 32

    def labelled_field(label, name, tooltip, yy):
        c.setFont("Times-Bold", 11)
        lw = c.stringWidth(label, "Times-Bold", 11)
        c.drawString(FI, yy, label)
        fx  = FI + lw + 8
        fw  = FE - fx
        line_y = yy - 2            # underline position
        c.setLineWidth(0.5)
        c.line(fx, line_y, fx + fw, line_y)
        # field bottom = line_y  →  typed text rises above the line
        add_text_field(c, name, tooltip, fx, line_y, fw, FIELD_H)

    labelled_field("FULL NAME:",   "FullName",   "Full Name",        y)
    y -= FIELD_ROW
    labelled_field("UNIT #:",      "UnitNumber", "Unit Number",      y)
    y -= FIELD_ROW
    labelled_field("TELEPHONE #:", "Telephone",  "Telephone Number", y)

    # -----------------------------------------------------------------------
    # BRIEF DESCRIPTION
    # -----------------------------------------------------------------------
    y -= 32

    c.setFont("Times-Bold", 11)
    bd_lbl = "Brief description"
    bd_lw  = c.stringWidth(bd_lbl, "Times-Bold", 11)
    c.drawString(LM, y, bd_lbl)
    c.setFont("Times-Roman", 11)
    c.drawString(LM + bd_lw, y,
        " (i.e., difficulty walking, wheelchair, special breathing apparatus, bedridden,")

    y -= LH
    c.setFont("Times-Roman", 11)
    c.drawString(LM, y, "sprains/fractures, hearing or visually impaired).")

    y -= 22
    DESC_GAP  = 27
    desc_top_y = y

    c.setLineWidth(0.8)
    for i in range(5):
        c.line(LM, y, PAGE_W - RM, y)
        if i < 4:
            y -= DESC_GAP

    desc_bot_y = y

    # Multiline field – bottom at the last ruled line, top above the first
    desc_field_h = desc_top_y - desc_bot_y + 20
    add_text_field(c, "BriefDescription",
                   "Brief description of assistance needs",
                   LM, desc_bot_y, UW, desc_field_h, multiline=True)

    y -= 36

    # -----------------------------------------------------------------------
    # CONFIDENTIALITY STATEMENT
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
    dc_fx    = LM + dc_lw + 8
    dc_fw    = 230
    dc_line_y = y - 2
    c.setLineWidth(0.5)
    c.line(dc_fx, dc_line_y, dc_fx + dc_fw, dc_line_y)
    # field bottom = line y → text above line
    add_text_field(c, "DateCompleted", "Date Completed",
                   dc_fx, dc_line_y, dc_fw, FIELD_H)

    # -----------------------------------------------------------------------
    # RESIDENT SIGNATURE  – underline drawn here; widget added in Phase 2
    # -----------------------------------------------------------------------
    y -= 27
    c.setFont("Times-Roman", 11)
    rs_lbl = "Resident Signature:"
    rs_lw  = c.stringWidth(rs_lbl, "Times-Roman", 11)
    c.drawString(LM, y, rs_lbl)
    rs_fx    = LM + rs_lw + 8
    rs_fw    = 218
    rs_line_y = y - 2
    c.setLineWidth(0.5)
    c.line(rs_fx, rs_line_y, rs_fx + rs_fw, rs_line_y)
    # NO text field here – a /Sig widget is injected in Phase 2

    # -----------------------------------------------------------------------
    # FOOTER
    # -----------------------------------------------------------------------
    footer = "TSCC 2920 Panda Condos Special Assistance Information Form"
    c.setFont("Times-Italic", 10)
    footer_w = c.stringWidth(footer, "Times-Italic", 10)
    c.drawString((PAGE_W - footer_w) / 2, 44, footer)

    c.save()

    # Return the rect for the signature widget:
    #   [x_left, y_bottom, x_right, y_top]
    sig_rect = [rs_fx, rs_line_y, rs_fx + rs_fw, rs_line_y + FIELD_H + 4]
    return sig_rect


# ---------------------------------------------------------------------------
# Phase 2 – inject a proper PDF /Sig widget via pdfrw
# ---------------------------------------------------------------------------

def _inject_signature_widget(sig_rect):
    """
    Read the base PDF, add a digital-signature widget (/FT /Sig) at sig_rect,
    and write the final PDF.  Also sets AcroForm /SigFlags so viewers know
    the form contains a signature field.
    """
    reader = pdfrw.PdfReader(_TEMP)
    page   = reader.pages[0]

    # Build the signature widget annotation
    sig_widget = pdfrw.PdfDict(
        Type    = pdfrw.PdfName('Annot'),
        Subtype = pdfrw.PdfName('Widget'),
        FT      = pdfrw.PdfName('Sig'),
        T       = pdfrw.PdfString.encode('ResidentSignature'),
        TU      = pdfrw.PdfString.encode('Resident Signature - Click here to sign digitally'),
        Rect    = pdfrw.PdfArray([round(v, 2) for v in sig_rect]),
        F       = pdfrw.PdfObject('4'),          # Print flag
        P       = page,                           # page reference
        BS      = pdfrw.PdfDict(
                      W = pdfrw.PdfObject('0.5'),
                      S = pdfrw.PdfName('S'),
                  ),
        MK      = pdfrw.PdfDict(
                      BC = pdfrw.PdfArray([pdfrw.PdfObject('0'),
                                           pdfrw.PdfObject('0'),
                                           pdfrw.PdfObject('0')]),
                  ),
    )
    sig_widget.indirect = True

    # Append to page /Annots
    if page.Annots is None:
        page.Annots = pdfrw.PdfArray()
    page.Annots.append(sig_widget)

    # Append to AcroForm /Fields
    acro = reader.Root.AcroForm
    if acro is None:
        acro = pdfrw.PdfDict(Fields=pdfrw.PdfArray())
        reader.Root.AcroForm = acro
    if acro.Fields is None:
        acro.Fields = pdfrw.PdfArray()
    acro.Fields.append(sig_widget)

    # SigFlags = 3  (SignaturesExist | AppendOnly hint for Acrobat)
    acro.SigFlags = pdfrw.PdfObject('3')

    pdfrw.PdfWriter().write(OUTPUT, reader)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def create_pdf():
    sig_rect = _build_base_pdf()
    _inject_signature_widget(sig_rect)
    os.remove(_TEMP)
    return OUTPUT


if __name__ == "__main__":
    path = create_pdf()
    size_kb = os.path.getsize(path) / 1024
    print(f"Created : {path}")
    print(f"Size    : {size_kb:.1f} KB")
    print("Fields  : FullName, UnitNumber, Telephone, BriefDescription (multiline),")
    print("          DateCompleted, ResidentSignature (/Sig – digital signature)")
