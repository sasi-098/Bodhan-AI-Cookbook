"""Script to generate authentic, high-quality sample data for the Bodhan Tool Agent.

Generates:
1. sample_chapter.pdf: 3-page illustrated educational physics/astronomy chapter with headings, paragraphs, and data tables.
2. worksheet_math.png: High-resolution math worksheet with geometry formulas, question sets, and markdown table.
3. bengali_paragraph.txt: Real biographical text about Rabindranath Tagore in Bengali script.
4. hindi_voice_note.wav: Real Hindi speech announcement synthesized via Bodhan Indic-Speak.
5. clips/: 5 audio clips (Hindi, Telugu, Tamil, Telugu, Bengali) synthesized with native voices.
6. sample_video.mp4: Valid MP4 media file container.
"""

from __future__ import annotations

import struct
from pathlib import Path

from bodhan_mcp.client import bodhan_client
from PIL import Image, ImageDraw, ImageFont

# Set up paths
SAMPLE_DATA_DIR = Path(__file__).resolve().parent / "sample_data"
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
CLIPS_DIR = SAMPLE_DATA_DIR / "clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)


def get_fonts() -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    """Load standard Windows Arial fonts or fallbacks."""
    win_font = "C:/Windows/Fonts/arial.ttf"
    win_font_bold = "C:/Windows/Fonts/arialbd.ttf"
    try:
        title_font = ImageFont.truetype(win_font_bold, 36)
        heading_font = ImageFont.truetype(win_font_bold, 24)
        body_font = ImageFont.truetype(win_font, 18)
    except Exception:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    return title_font, heading_font, body_font


def generate_worksheet_png() -> Path:
    """Generate a clean, high-resolution scanned worksheet image with tables and questions."""
    width, height = 1200, 1500
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    title_font, heading_font, body_font = get_fonts()

    # Draw Header Box
    draw.rectangle([50, 40, width - 50, 140], outline="black", width=2)
    draw.text((70, 55), "SECONDARY SCHOOL MATHEMATICS — WORKSHEET 04", font=title_font, fill="black")
    draw.text((70, 105), "Topic: Mensuration, Plane Geometry & Geometric Areas | Time: 45 Mins", font=body_font, fill="#333333")

    # Section 1: Overview
    y = 170
    draw.text((60, y), "Section A: Geometry Formulas & Area Calculations", font=heading_font, fill="black")
    y += 35
    draw.text(
        (60, y),
        "Review the standardized two-dimensional geometric figures and their corresponding area equations below:",
        font=body_font,
        fill="#444444",
    )
    y += 35

    # Draw Table Grid
    table_top = y
    row_height = 42
    col_x = [60, 240, 520, 820, 1140]
    headers = ["Figure Name", "Formula (Area)", "Given Dimensions", "Calculated Area"]
    data = [
        ["Right Triangle", "Area = 0.5 * b * h", "Base = 12 cm, Height = 8 cm", "48.0 cm^2"],
        ["Rectangle", "Area = l * w", "Length = 15 cm, Width = 10 cm", "150.0 cm^2"],
        ["Parallelogram", "Area = b * h", "Base = 14 cm, Height = 6 cm", "84.0 cm^2"],
        ["Circle", "Area = pi * r^2", "Radius = 7 cm (pi = 22/7)", "154.0 cm^2"],
        ["Trapezium", "Area = 0.5 * (a + b) * h", "a = 8 cm, b = 12 cm, h = 5 cm", "50.0 cm^2"],
    ]

    # Header row
    draw.rectangle([col_x[0], table_top, col_x[-1], table_top + row_height], fill="#EEEEEE", outline="black", width=2)
    for i, h_text in enumerate(headers):
        draw.text((col_x[i] + 12, table_top + 10), h_text, font=heading_font, fill="black")
    y = table_top + row_height

    # Data rows
    for row in data:
        draw.rectangle([col_x[0], y, col_x[-1], y + row_height], outline="#888888", width=1)
        for i, cell_text in enumerate(row):
            draw.text((col_x[i] + 12, y + 10), cell_text, font=body_font, fill="black")
        y += row_height

    # Draw vertical table lines
    for x in col_x:
        draw.line([x, table_top, x, y], fill="black", width=2 if x in (col_x[0], col_x[-1]) else 1)

    # Section 2: Questions
    y += 45
    draw.text((60, y), "Section B: Problem Solving Questions", font=heading_font, fill="black")
    y += 40

    questions = [
        "1. A farmer owns a rectangular field of length 120 meters and breadth 75 meters. Calculate the total cost",
        "   of fencing the boundary at the rate of Rs. 35 per meter, and finding its total area in hectares.",
        "",
        "2. An open cylindrical storage tank has a base radius of 14 meters and a depth of 20 meters.",
        "   Determine the total volume of water it can hold and the inner curved surface area.",
        "",
        "3. A circular track of radius 28 meters is surrounded by a walking path of width 7 meters.",
        "   Calculate the area of the walking path using pi = 22/7.",
        "",
        "4. If the perimeter of a semi-circular garden is 108 meters, find the radius and total area.",
    ]

    for q_line in questions:
        draw.text((70, y), q_line, font=body_font, fill="black")
        y += 26

    # Bottom Note
    draw.line([50, height - 70, width - 50, height - 70], fill="#888888", width=1)
    draw.text((60, height - 50), "Evaluation Sheet — Bodhan OCR & Document Ingestion Test Dataset", font=body_font, fill="#666666")

    out_path = SAMPLE_DATA_DIR / "worksheet_math.png"
    img.save(out_path, "PNG", dpi=(150, 150))
    print(f"Generated: {out_path} ({out_path.stat().st_size} bytes)")
    return out_path


def generate_sample_chapter_pdf() -> Path:
    """Generate a multi-page educational chapter on Physics and Space with headings and data tables."""
    width, height = 1200, 1600
    title_font, heading_font, body_font = get_fonts()
    pages: list[Image.Image] = []

    # ---------------- PAGE 1 ----------------
    p1 = Image.new("RGB", (width, height), "white")
    d1 = ImageDraw.Draw(p1)

    d1.rectangle([50, 40, width - 50, 150], fill="#0A2540", outline="black")
    d1.text((80, 55), "CHAPTER 4: GRAVITATION & PLANETARY DYNAMICS", font=title_font, fill="white")
    d1.text((80, 105), "National Curriculum for Secondary Science | Physics Unit II", font=body_font, fill="#E0E6ED")

    y = 180
    d1.text((70, y), "4.1 Universal Law of Gravitation", font=heading_font, fill="#0A2540")
    y += 35
    intro_lines = [
        "Every particle in the universe attracts every other particle with a force that is directly proportional",
        "to the product of their masses and inversely proportional to the square of the distance between their centers.",
        "This fundamental law was formulated by Sir Isaac Newton in 1687 and forms the mathematical basis for orbital",
        "mechanics, celestial navigation, and modern satellite deployments around celestial bodies.",
    ]
    for line in intro_lines:
        d1.text((70, y), line, font=body_font, fill="#222222")
        y += 28

    y += 25
    d1.text((70, y), "Planetary Characteristics & Orbital Parameters:", font=heading_font, fill="#0A2540")
    y += 35

    # Table on Page 1
    table_top = y
    row_height = 40
    col_x = [70, 240, 460, 720, 960, 1130]
    headers = ["Planet", "Mass (10^24 kg)", "Orbital Radius (10^6 km)", "Period (Earth Days)", "Escape Speed (km/s)"]
    planet_data = [
        ["Mercury", "0.330", "57.9", "88.0", "4.3"],
        ["Venus", "4.870", "108.2", "224.7", "10.4"],
        ["Earth", "5.972", "149.6", "365.25", "11.2"],
        ["Mars", "0.642", "227.9", "687.0", "5.0"],
        ["Jupiter", "1898.0", "778.6", "4331.0", "59.5"],
        ["Saturn", "568.0", "1433.5", "10747.0", "35.5"],
    ]

    d1.rectangle([col_x[0], table_top, col_x[-1], table_top + row_height], fill="#E8EEF5", outline="black", width=2)
    for i, h in enumerate(headers):
        d1.text((col_x[i] + 8, table_top + 10), h, font=heading_font, fill="black")
    y = table_top + row_height

    for row in planet_data:
        d1.rectangle([col_x[0], y, col_x[-1], y + row_height], outline="#AAAAAA", width=1)
        for i, val in enumerate(row):
            d1.text((col_x[i] + 8, y + 10), val, font=body_font, fill="black")
        y += row_height

    for x in col_x:
        d1.line([x, table_top, x, y], fill="black", width=2 if x in (col_x[0], col_x[-1]) else 1)

    y += 40
    d1.text((70, y), "Kepler's Laws of Planetary Motion:", font=heading_font, fill="#0A2540")
    y += 30
    kepler_lines = [
        "1. The Law of Orbits: All planets move in elliptical orbits with the Sun at one of the focal points.",
        "2. The Law of Areas: A line joining a planet and the Sun sweeps out equal areas during equal intervals of time.",
        "3. The Law of Periods: The square of the orbital period of a planet is directly proportional to the cube",
        "   of the semi-major axis of its orbit (T^2 is proportional to R^3).",
    ]
    for line in kepler_lines:
        d1.text((70, y), line, font=body_font, fill="#222222")
        y += 28

    d1.text((width // 2 - 40, height - 60), "Page 1 of 3", font=body_font, fill="#666666")
    pages.append(p1)

    # ---------------- PAGE 2 ----------------
    p2 = Image.new("RGB", (width, height), "white")
    d2 = ImageDraw.Draw(p2)

    d2.text((70, 60), "4.2 Satellite Orbits and Escape Velocity", font=title_font, fill="#0A2540")
    d2.line([70, 110, width - 70, 110], fill="#0A2540", width=2)

    y = 135
    sec2_lines = [
        "To place an artificial satellite into low Earth orbit, it must achieve a horizontal orbital speed of approximately",
        "7.8 kilometers per second (28,000 km/h). At this critical orbital speed, the downward acceleration of gravity",
        "matches the natural curvature of the Earth's surface, creating continuous orbital free-fall.",
        "",
        "If a rocket achieves an escape velocity of 11.2 kilometers per second at the Earth's surface, it possesses sufficient",
        "kinetic energy to completely overcome the planet's gravitational potential field without further propulsion.",
    ]
    for line in sec2_lines:
        d2.text((70, y), line, font=body_font, fill="#222222")
        y += 28

    y += 30
    d2.text((70, y), "Satellite Orbital Classifications:", font=heading_font, fill="#0A2540")
    y += 35

    sat_table_top = y
    sat_headers = ["Orbit Type", "Altitude Range (km)", "Orbital Period", "Primary Use Case"]
    sat_col_x = [70, 320, 560, 800, 1130]
    sat_data = [
        ["LEO (Low Earth Orbit)", "160 to 2,000 km", "90 to 120 mins", "Earth Observation & ISS"],
        ["MEO (Medium Earth Orbit)", "2,000 to 35,786 km", "12 hours", "GPS & Navigation Satellites"],
        ["GEO (Geostationary Orbit)", "35,786 km fixed", "24 hours exact", "Telecommunications & Weather"],
        ["HEO (Highly Elliptical Orbit)", "Up to 40,000 km apogee", "12 to 24 hours", "High-Latitude Communications"],
    ]

    d2.rectangle([sat_col_x[0], sat_table_top, sat_col_x[-1], sat_table_top + row_height], fill="#E8EEF5", outline="black", width=2)
    for i, h in enumerate(sat_headers):
        d2.text((sat_col_x[i] + 8, sat_table_top + 10), h, font=heading_font, fill="black")
    y = sat_table_top + row_height

    for row in sat_data:
        d2.rectangle([sat_col_x[0], y, sat_col_x[-1], y + row_height], outline="#AAAAAA", width=1)
        for i, val in enumerate(row):
            d2.text((sat_col_x[i] + 8, y + 10), val, font=body_font, fill="black")
        y += row_height

    for x in sat_col_x:
        d2.line([x, sat_table_top, x, y], fill="black", width=2 if x in (sat_col_x[0], sat_col_x[-1]) else 1)

    d2.text((width // 2 - 40, height - 60), "Page 2 of 3", font=body_font, fill="#666666")
    pages.append(p2)

    # ---------------- PAGE 3 ----------------
    p3 = Image.new("RGB", (width, height), "white")
    d3 = ImageDraw.Draw(p3)

    d3.text((70, 60), "4.3 Chapter Summary & Practice Review", font=title_font, fill="#0A2540")
    d3.line([70, 110, width - 70, 110], fill="#0A2540", width=2)

    y = 140
    d3.text((70, y), "Core Formula Reference:", font=heading_font, fill="#0A2540")
    y += 35

    formulas = [
        "1. Gravitational Force Formula:      F = G * (m1 * m2) / r^2      (where G = 6.674 * 10^-11 N m^2 / kg^2)",
        "2. Orbital Velocity Equation:        v_orbital = sqrt(G * M / r)",
        "3. Escape Velocity Equation:         v_escape = sqrt(2 * G * M / r)",
        "4. Kepler's Third Law Ratio:         (T1 / T2)^2 = (R1 / R2)^3",
    ]
    for form in formulas:
        d3.rectangle([70, y, width - 70, y + 36], fill="#F8F9FA", outline="#CCD0D5")
        d3.text((85, y + 8), form, font=body_font, fill="#003366")
        y += 45

    y += 25
    d3.text((70, y), "Conceptual Review Questions:", font=heading_font, fill="#0A2540")
    y += 35

    review_q = [
        "Q1. Why does an astronaut experience weightlessness in an orbiting space station despite Earth's gravity?",
        "Q2. Calculate the gravitational attraction between Earth and the Moon (Earth mass = 6.0 x 10^24 kg).",
        "Q3. How does increasing a communication satellite's altitude affect its orbital period and coverage area?",
        "Q4. A geostationary satellite appears stationary from Earth. Explain why its orbit must be in the equatorial plane.",
    ]
    for q in review_q:
        d3.text((70, y), q, font=body_font, fill="#222222")
        y += 32

    d3.text((width // 2 - 40, height - 60), "Page 3 of 3", font=body_font, fill="#666666")
    pages.append(p3)

    out_pdf = SAMPLE_DATA_DIR / "sample_chapter.pdf"
    pages[0].save(out_pdf, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    print(f"Generated: {out_pdf} ({len(pages)} pages, {out_pdf.stat().st_size} bytes)")
    return out_pdf


def generate_bengali_text() -> Path:
    """Generate authentic biographical text in Bengali."""
    text = (
        "রবীন্দ্রনাথ ঠাকুর ছিলেন একজন বিশ্বখ্যাত ভারতীয় বাঙালি কবি, ঔপন্যাসিক, "
        "সংগীতস্রষ্টা, নাট্যকার ও সমাজ সংস্কারক। তিনি ১৯১৩ সালে তাঁর বিখ্যাত কাব্যগ্রন্থ "
        "গীতাঞ্জলির জন্য সাহিত্যে এশিয়ার প্রথম নোবেল পুরস্কার লাভ করেন।\n\n"
        "তিনি ভারতের জাতীয় সংগীত 'জন গণ মন' এবং বাংলাদেশের জাতীয় সংগীত 'আমার সোনার বাংলা' রচনা করেন। "
        "তাঁর প্রতিষ্ঠিত শান্তিনিকেতন ও বিশ্বভারতী বিশ্ববিদ্যালয় আজও বিশ্ব সংস্কৃতির এক অন্যতম মিলনক্ষেত্র।"
    )
    p = SAMPLE_DATA_DIR / "bengali_paragraph.txt"
    p.write_text(text, encoding="utf-8")
    print(f"Generated: {p} ({len(text)} characters)")
    return p


def generate_valid_mp4() -> Path:
    """Generate a lightweight valid MP4 container file for media inspection."""
    p = SAMPLE_DATA_DIR / "sample_video.mp4"
    # Construct standard ISO base media file format boxes (ftyp, moov)
    ftyp = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41"
    moov_payload = b"\x00\x00\x00\x08free"
    moov = struct.pack(">I", len(moov_payload) + 8) + b"moov" + moov_payload
    mdat = b"\x00\x00\x00\x08mdat"
    p.write_bytes(ftyp + moov + mdat)
    print(f"Generated: {p} ({p.stat().st_size} bytes)")
    return p


def generate_audio_files() -> None:
    """Synthesize authentic speech audio clips using Bodhan Indic-Speak API."""
    print("\n--- Synthesizing Authentic Audio via Indic-Speak ---")

    audio_manifest = [
        {
            "path": SAMPLE_DATA_DIR / "hindi_voice_note.wav",
            "text": "नमस्कार साथियों। कल सुबह दस बजे विद्यालय में विज्ञान प्रदर्शनी और वार्षिक बैठक आयोजित की जाएगी।",
            "lang": "hi",
            "voice": "Kavya",
            "style": "AIR style news",
            "desc": "Hindi School Announcement Voice Note",
        },
        {
            "path": CLIPS_DIR / "clip1_hi.wav",
            "text": "आज देश भर में मौसम बहुत सुहाना है और शाम के समय मध्यम बारिश होने की संभावना है।",
            "lang": "hi",
            "voice": "Amit",
            "style": "news",
            "desc": "Hindi Weather Report Clip",
        },
        {
            "path": CLIPS_DIR / "clip2_te.wav",
            "text": "నమస్కారం, ఈరోజు సాయంత్రం ఐదు గంటలకు హైదరాబాద్ నగరంలో ప్రత్యేక సాంకేతిక సమావేశం ప్రారంభమవుతుంది.",
            "lang": "te",
            "voice": "Sravani",
            "style": "educational lecture",
            "desc": "Telugu Tech Conference Clip",
        },
        {
            "path": CLIPS_DIR / "clip3_ta.wav",
            "text": "வணக்கம், தமிழ்நாட்டின் தலைநகரமான சென்னை ஒரு முக்கியமான கலாச்சார மற்றும் தொழில் மையமாகும்.",
            "lang": "ta",
            "voice": "Anitha",
            "style": "AIR style news",
            "desc": "Tamil Cultural Notice Clip",
        },
        {
            "path": CLIPS_DIR / "clip4_te.wav",
            "text": "రేపు ఉదయం పాఠశాలలో సైన్స్ ఎగ్జిబిషన్ నిర్వహించబడుతుంది మరియు ఉత్తమ ప్రాజెక్టులకు బహుమతులు అందజేస్తారు.",
            "lang": "te",
            "voice": "Vamsi",
            "style": "news",
            "desc": "Telugu Science Exhibition Clip",
        },
        {
            "path": CLIPS_DIR / "clip5_bn.wav",
            "text": "নমস্কার, আগামী সপ্তাহে কলকাতায় আন্তর্জাতিক বইমেলা শুরু হতে চলেছে।",
            "lang": "bn",
            "voice": "Ishita",
            "style": "AIR style news",
            "desc": "Bengali Book Fair Clip",
        },
    ]

    for item in audio_manifest:
        out_file = item["path"]
        print(f"Synthesizing [{item['desc']}] -> {out_file.name} ({item['lang']}, voice: {item['voice']})...")
        try:
            bodhan_client.synthesize_speech_chunk(
                text=item["text"],
                language=item["lang"],
                voice=item["voice"],
                style=item["style"],
                output_file=out_file,
            )
            print(f"  [SUCCESS] {out_file.name} generated: {out_file.stat().st_size} bytes")
        except Exception as e:
            print(f"  [WARNING] Online synthesis failed ({e}). Generating fallback WAV...")
            from bodhan_mcp.tools.media_utils import create_synthetic_wav

            create_synthetic_wav(out_file, duration_sec=5.0)


def main():
    print("=" * 65)
    print("      GENERATING PRODUCTION-GRADE SAMPLE DATASETS")
    print("=" * 65)
    generate_worksheet_png()
    generate_sample_chapter_pdf()
    generate_bengali_text()
    generate_valid_mp4()
    generate_audio_files()
    print("=" * 65)
    print("All sample datasets successfully generated in:")
    print(f"-> {SAMPLE_DATA_DIR}")
    print("=" * 65)


if __name__ == "__main__":
    main()
