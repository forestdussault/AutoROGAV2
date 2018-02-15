# begin-doc-include
# from pylatex import Document, Section, Subsection, Tabular, Math, TikZ, Axis, \
#     Plot, Figure, Matrix, Alignat
from pylatex.utils import italic, bold, verbatim
from datetime import datetime

import extract_reports

import pylatex as pl

import numpy as np
import pandas as pd
import os


def generate_roga(seq_list):

    metadata_reports = extract_reports.get_combined_metadata(seq_list)
    gdcs_reports = extract_reports.get_gdcs(seq_list)

    geometry_options = {"tmargin": "2cm",
                        "lmargin": "1.7cm",
                        "headsep": "1cm"}

    doc = pl.Document(page_numbers=False,
                      geometry_options=geometry_options)

    header = produce_header_footer()

    doc.preamble.append(header)
    doc.change_document_style("header")

    # DOCUMENT BODY/CREATION
    with doc.create(pl.Section('Report of Genomic Analysis', numbering=False)):

        # TEXT SUMMARY
        with doc.create(pl.Subsection('Identification Summary', numbering=False)) as summary:
            summary.append('Some regular text and some ')
            summary.append(italic('italic text. '))
            summary.append('\nAt vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium '
                           'voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati '
                           'cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id '
                           'est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. ')

        # ESCHERICHIA TABLE

        # LISTERIA TABLE


        # SALMONELLA TABLE
        genesippr_table_columns = (bold('Sample ID'),
                                   bold('Genus'),
                                   bold('Serotype'),
                                   bold('invA'),
                                   bold('stn'))

        with doc.create(pl.Subsection('GeneSippr Analysis', numbering=False)) as genesippr_section:
            with doc.create(pl.Tabular('|r|c|c|c|c|')) as table:
                # Header
                table.add_hline()
                table.add_row(genesippr_table_columns)

                # Rows
                for sample_id, df in metadata_reports.items():
                    table.add_hline()
                    genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]
                    table.add_row((sample_id, genus, 'N/A', '+', '-' ))
                table.add_hline()

            create_caption(genesippr_section, 'i', 'caption')
            create_caption(genesippr_section, 'ii', 'another caption')

        ######################

        # GDCS TABLE
        gdcs_table_columns = (bold('Sample ID'),
                              bold('Genus'),
                              bold('Matches'),
                              bold('Mean Coverage'),
                              bold('Pass/Fail'))
        with doc.create(pl.Subsection('GDCS', numbering=False)) as gdcs_section:
            with doc.create(pl.Tabular('|r|c|c|c|c|')) as table:
                # Header
                table.add_hline()
                table.add_row(gdcs_table_columns)

                # Rows
                for sample_id, df in gdcs_reports.items():
                    table.add_hline()

                    # Grab values
                    genus = df.loc[df['Strain'] == sample_id]['Genus'].values[0]
                    matches = df.loc[df['Strain'] == sample_id]['Matches'].values[0]
                    mean_coverage = df.loc[df['Strain'] == sample_id]['MeanCoverage'].values[0]
                    passfail = df.loc[df['Strain'] == sample_id]['Pass/Fail'].values[0]

                    # Add row
                    table.add_row((sample_id, genus, matches, mean_coverage, passfail ))
                table.add_hline()


        # SEQUENCE DATA QUALITY
        sequence_quality_columns = (bold('Sample ID'),
                                    bold('Total Length'),
                                    bold('Coverage'),
                                    bold('Number of Contigs')
                                    )

        with doc.create(pl.Subsection('Sequence Data Quality', numbering=False)) as sequence_section:
            with doc.create(pl.Tabular('|r|c|c|c|')) as table:
                # Header
                table.add_hline()
                table.add_row(sequence_quality_columns)

                # Rows
                for sample_id, df in metadata_reports.items():
                    table.add_hline()

                    # Grab values
                    total_length = df.loc[df['SeqID'] == sample_id]['TotalLength'].values[0]
                    average_coverage_depth = df.loc[df['SeqID'] == sample_id]['AverageCoverageDepth'].values[0]
                    num_contigs = df.loc[df['SeqID'] == sample_id]['NumContigs'].values[0]

                    # Add row
                    table.add_row((sample_id, total_length, average_coverage_depth, num_contigs ))
                table.add_hline()



    doc.generate_pdf('full', clean_tex=False)


def produce_header_footer():
    header = pl.PageStyle("header", header_thickness=0.1)

    image_filename = get_image()
    with header.create(pl.Head("L")) as logo:
        logo.append(pl.StandAloneGraphic(image_options="width=110px", filename=image_filename))

    # Date
    with header.create(pl.Head("R")):
        header.append("Date: " + datetime.today().strftime('%Y-%m-%d'))

    with header.create(pl.Foot("C")):
        with header.create(pl.Tabular('lcr')) as table:
            table.add_row(('+ : Pass', '? : Indeterminate', '- : Fail'))

            # header.append('+ : Pass\t\t\t? : Indeterminate\t\t\t- : Fail')

    return header


def create_caption(section, superscript, text):
    section.append('\n')
    section.append(bold(pl.NoEscape(r'\textsuperscript{' + superscript + '}')))
    section.append(italic(text))


def get_image():
    image_filename = os.path.join(os.path.dirname(__file__), 'CFIA_logo.png')
    return image_filename


if __name__ == '__main__':

    dummy_list = ['2017-SEQ-0725', '2017-SEQ-0726', '2017-SEQ-0727']

    generate_roga(seq_list=dummy_list)

