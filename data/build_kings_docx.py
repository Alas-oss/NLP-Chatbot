from docx import Document

doc = Document()
doc.add_heading("King's College London - General Information", level=0)
doc.add_paragraph(
    "This is a sample information document assembled for demonstrating a "
    "retrieval-augmented chatbot prototype. It is not an official King's College "
    "London publication."
)

doc.add_heading("History and Founding", level=1)
doc.add_paragraph(
    "King's College London (KCL) was founded in 1829 by King George IV and the "
    "Duke of Wellington, making it one of the oldest universities in England. It "
    "was established, in part, as a Church of England response to the founding of "
    "the secular University College London a few years earlier. King's became one "
    "of the two founding constituent colleges of the University of London in 1836. "
    "The university's motto is 'Sancte et Sapienter' - 'With Holiness and Wisdom'."
)
doc.add_paragraph(
    "King's grew substantially through mergers in the twentieth century, "
    "including with Queen Elizabeth College and Chelsea College of Science and "
    "Technology in 1985, the Institute of Psychiatry in 1997, and the medical and "
    "dental schools of Guy's and St Thomas' Hospitals in 1998. King's gained the "
    "power to award its own degrees independently of the University of London in "
    "2007."
)

doc.add_heading("Campuses", level=1)
doc.add_paragraph(
    "King's operates across five main campuses in central London: the Strand "
    "Campus (the historic main site, home to arts and humanities, informatics, "
    "and law), Guy's Campus (near London Bridge, focused on health and life "
    "sciences), St Thomas' Campus (opposite the Houses of Parliament, home to "
    "nursing and midwifery), Waterloo Campus (social sciences, public policy, "
    "computer science, and natural sciences), and Denmark Hill Campus (south "
    "London, focused on medical, dental, and psychiatric research alongside "
    "King's College Hospital)."
)

doc.add_heading("Faculties and Schools", level=1)
doc.add_paragraph(
    "King's is organised into nine faculties: the Faculty of Arts & Humanities; "
    "King's Business School; the Faculty of Dentistry, Oral & Craniofacial "
    "Sciences; The Dickson Poon School of Law; the Faculty of Life Sciences & "
    "Medicine; the Faculty of Natural, Mathematical & Engineering Sciences; the "
    "Florence Nightingale Faculty of Nursing, Midwifery & Palliative Care; the "
    "Institute of Psychiatry, Psychology & Neuroscience (IoPPN); and the Faculty "
    "of Social Science & Public Policy."
)

doc.add_heading("Governance and Leadership", level=1)
doc.add_paragraph(
    "The Chancellor of the University of London, and by extension of King's, is "
    "Anne, the Princess Royal. King's is led day-to-day by its President & "
    "Principal, a role held by Professor Shitij Kapur. King's is a self-governing "
    "institution within the federal University of London, with its own Council "
    "responsible for institutional governance."
)

doc.add_heading("King's Health Partners", level=1)
doc.add_paragraph(
    "King's is a founding member of King's Health Partners, one of a small "
    "number of Academic Health Sciences Centres in the UK. The partnership "
    "brings together King's College London with Guy's and St Thomas', King's "
    "College Hospital, and South London and Maudsley NHS Foundation Trusts, "
    "combining research, education, and clinical care across south London's "
    "teaching hospitals."
)

doc.add_heading("Notable History and Contributions", level=1)
doc.add_paragraph(
    "King's has a strong historical connection to major scientific and medical "
    "milestones. Florence Nightingale founded the world's first official nursing "
    "school at King's in 1860, a legacy continued today through the Florence "
    "Nightingale Faculty of Nursing, Midwifery & Palliative Care. Researchers at "
    "King's, including Rosalind Franklin and Maurice Wilkins, produced X-ray "
    "diffraction images central to discovering the double-helix structure of DNA "
    "in the 1950s; Wilkins shared the 1962 Nobel Prize in Physiology or Medicine "
    "for this work."
)

doc.add_heading("Notable Alumni and Nobel Laureates", level=1)
doc.add_paragraph(
    "King's counts fourteen Nobel laureates among its alumni and former staff, "
    "spanning physics, chemistry, medicine, and peace. These include physicist "
    "Peter Higgs, who studied for his bachelor's, master's, and doctorate at "
    "King's in the 1950s and proposed the mechanism behind the Higgs boson "
    "(Physics, 2013); Sir Michael Houghton, recognised for his research into "
    "Hepatitis C (Medicine, 2020); and Michael Levitt, recognised for his work on "
    "computational modelling of chemical processes (Chemistry, 2013). Archbishop "
    "Desmond Tutu, who studied theology at King's in the 1960s, later received "
    "the Nobel Peace Prize in 1984 for his work against apartheid in South "
    "Africa."
)
doc.add_paragraph(
    "Beyond the sciences, King's alumni include prominent figures in politics, "
    "law, literature, and the arts. Sir Keir Starmer, the current UK Prime "
    "Minister, studied at King's. In literature, alumni include author and "
    "children's writer Sir Michael Morpurgo and writer and philosopher Alain de "
    "Botton. In music, Queen bassist John Deacon studied electronics at Chelsea "
    "College, which later merged into King's. Olympic medallists Dame Katherine "
    "Grainger (rowing) and Dina Asher-Smith (sprinting) also studied at the "
    "university."
)

doc.add_heading("Scale and Student Body", level=1)
doc.add_paragraph(
    "King's is one of the largest universities in the UK by enrolment. As of the "
    "2024/25 academic year, King's reported a total student population of "
    "around 40,900, made up of roughly 23,200 undergraduates and 17,700 "
    "postgraduates, with a substantial international student population "
    "reflecting London's global character."
)

doc.add_heading("Rankings and Research Strength", level=1)
doc.add_paragraph(
    "King's is a member of the Russell Group of research-intensive UK "
    "universities and is consistently ranked among the top universities "
    "globally and among the top handful in the UK, particularly strong in "
    "medicine, dentistry, law, nursing, psychology, and the humanities. In "
    "2024/25, King's reported a total income of around 1.38 billion pounds, of "
    "which roughly 260 million pounds came from research grants and contracts, "
    "and it holds the fourth-largest endowment of any UK university."
)

doc.add_heading("Golden Triangle and London Context", level=1)
doc.add_paragraph(
    "King's is often described as part of the UK's 'Golden Triangle' of leading "
    "research universities, a term referring to institutions concentrated in and "
    "around London, Oxford, and Cambridge, alongside institutions such as UCL, "
    "Imperial College London, and the London School of Economics. Its location "
    "gives it close ties to London's legal, financial, medical, and cultural "
    "institutions."
)

doc.add_heading("Notable Buildings", level=1)
doc.add_paragraph(
    "The Strand Campus is built around King's original 1829 building next to "
    "Somerset House; The Dickson Poon School of Law is based in Somerset House's "
    "East Wing. The Maughan Library on Chancery Lane, King's largest library, "
    "occupies the former Public Record Office building. King's Chapel on the "
    "Strand Campus has served the college community for over 150 years."
)

doc.add_heading("Student Life", level=1)
doc.add_paragraph(
    "King's College London Students' Union (KCLSU) runs student societies, "
    "sports clubs, and campus events across all five campuses. The university "
    "has a large international student population and offers halls of "
    "residence across multiple London locations."
)

doc.add_heading("Sports and Athletics", level=1)
doc.add_paragraph(
    "King's fields a large number of student sports clubs under King's Sport "
    "and KCLSU, competing mainly through British Universities and Colleges "
    "Sport (BUCS), the main governing body for university sport in the UK. Clubs "
    "range from competitive teams playing in structured BUCS leagues to "
    "recreational and social clubs aimed at fitness and skill-building rather "
    "than competition."
)
doc.add_paragraph(
    "The centrepiece of King's sporting calendar is the London Varsity Series, "
    "an annual set of matches against University College London (UCL), King's "
    "closest historical rival. The rivalry between the two institutions dates "
    "back to their founding in the 1820s; the modern Varsity began as a single "
    "rugby match and has since grown into a week-long, multi-sport series "
    "contested for the Jeremy George Cup. A related fixture, the Macadam Cup, "
    "pits King's teams against Guy's, King's and St Thomas' School of Medicine "
    "(GKT) teams."
)
doc.add_paragraph(
    "King's College London Rugby Football Club, founded in 1869, is one of the "
    "university's oldest sports clubs, was among the founding member clubs of "
    "the Rugby Football Union, and competes in BUCS leagues, playing its home "
    "matches at New Malden Sports Ground."
)

doc.add_heading("Computer Science, Informatics, and Artificial Intelligence", level=1)
doc.add_paragraph(
    "Computer science and AI research and teaching at King's is centred in the "
    "Department of Informatics, part of the Faculty of Natural, Mathematical & "
    "Engineering Sciences. The department offers undergraduate and postgraduate "
    "taught degrees alongside MPhil and PhD research degrees, and maintains an "
    "active research profile with externally funded projects and links to "
    "industry, government, and other academic institutions."
)
doc.add_paragraph(
    "King's has a dedicated King's Institute for Artificial Intelligence, which "
    "coordinates AI-related research and events across the university. Research "
    "within the department spans areas such as machine learning, autonomous "
    "systems, robotics, and the application of AI to fields including "
    "healthcare, finance, and smart cities, alongside a strong emphasis on AI "
    "safety and trustworthiness."
)

doc.save("data/kings_college_london.docx")
print("Created data/kings_college_london.docx")
