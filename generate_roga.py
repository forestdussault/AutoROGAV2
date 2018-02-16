# begin-doc-include

from pylatex.utils import italic, bold
from datetime import datetime
import extract_reports
import pylatex as pl
import os


# TODO: Add LSTS ID.
# TODO: Add rMLST, MLST


lab_info = {
    'GTA-CFIA':('2301 Midland Ave., Scarborough, ON, M1P 4R7', '(416) 973-0798'),
    'OLF-CFIA':('3851 Fallowfield Rd., Ottawa, ON, K2H 8P9', '(343) 212-0416')
}


def generate_roga(seq_list, genus, lab):

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
        # LAB SUMMARY
        with doc.create(pl.Tabular('|c|c|c|')) as table:
            table.add_hline()
            table.add_row(bold('Laboratory'),
                          bold('Address'),
                          bold('Tel #'))
            table.add_hline()
            table.add_row(lab, lab_info[lab][0], lab_info[lab][1])
            table.add_hline()

        # TEXT SUMMARY
        with doc.create(pl.Subsection('Identification Summary', numbering=False)) as summary:
            summary.append('Strains are confirmed to be ')
            summary.append(italic(genus))
            summary.append('.')

        # ESCHERICHIA TABLE
        if genus == 'Escherichia':
            genesippr_table_columns = (bold('LSTS ID'), # TODO: Convert to LSTS
                                       bold('Genus'),
                                       bold('VT1'),
                                       bold('VT2'),
                                       bold('VT2f'),
                                       bold('uidA'),
                                       bold('eae'))

            with doc.create(pl.Subsection('GeneSippr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabular('|c|c|c|c|c|c|c|')) as table:
                    # Header
                    table.add_hline()
                    table.add_row(genesippr_table_columns)

                    # Rows
                    for sample_id, df in metadata_reports.items():
                        table.add_hline()
                        genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]
                        table.add_row((sample_id, genus, 'temp', 'temp', 'temp', 'temp', 'temp' ))
                    table.add_hline()

                create_caption(genesippr_section, 'i', 'caption')
                create_caption(genesippr_section, 'ii', 'another caption')

        # LISTERIA TABLE
        if genus == 'Listeria':
            genesippr_table_columns = (bold('LSTS ID'), # TODO: Convert to LSTS
                                       bold('Genus'),
                                       bold('Serotype'),
                                       bold('IGS'),
                                       bold('hlyA'),
                                       bold('inlJ'))

            with doc.create(pl.Subsection('GeneSippr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabular('|c|c|c|c|c|c|')) as table:
                    # Header
                    table.add_hline()
                    table.add_row(genesippr_table_columns)

                    # Rows
                    for sample_id, df in metadata_reports.items():
                        table.add_hline()
                        genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]
                        table.add_row((sample_id, genus, 'temp', 'temp', 'temp', 'temp' ))
                    table.add_hline()

                create_caption(genesippr_section, 'i', 'caption')
                create_caption(genesippr_section, 'ii', 'another caption')

        # SALMONELLA TABLE
        if genus == 'Salmonella':
            genesippr_table_columns = (bold('LSTS ID'), # TODO: Convert to LSTS
                                       bold('Genus'),
                                       bold('Serotype'),
                                       bold('invA'),
                                       bold('stn'))

            with doc.create(pl.Subsection('GeneSippr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabular('|c|c|c|c|c|')) as table:
                    # Header
                    table.add_hline()
                    table.add_row(genesippr_table_columns)

                    # Rows
                    for sample_id, df in metadata_reports.items():
                        table.add_hline()
                        genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]
                        table.add_row((sample_id, genus, 'temp', 'temp', 'temp' ))
                    table.add_hline()

                create_caption(genesippr_section, 'i', 'caption')
                create_caption(genesippr_section, 'ii', 'another caption')

        ######################
        # GDCS TABLE
        gdcs_table_columns = (bold('LSTS ID'), # TODO: Convert to LSTS
                              bold('Genus'),
                              bold('Matches'),
                              bold('Pass/Fail'))
        with doc.create(pl.Subsection('GDCS', numbering=False)) as gdcs_section:
            with doc.create(pl.Tabular('|c|c|c|c|')) as table:
                # Header
                table.add_hline()
                table.add_row(gdcs_table_columns)

                # Rows
                for sample_id, df in gdcs_reports.items():
                    table.add_hline()

                    # Grab values
                    genus = df.loc[df['Strain'] == sample_id]['Genus'].values[0]
                    matches = df.loc[df['Strain'] == sample_id]['Matches'].values[0]
                    passfail = df.loc[df['Strain'] == sample_id]['Pass/Fail'].values[0]

                    # Add row
                    table.add_row((sample_id, genus, matches, passfail ))
                table.add_hline()
        create_caption(gdcs_section, 'i', 'Important text goes here')


        # SEQUENCE DATA QUALITY
        sequence_quality_columns = (bold('Seq ID'),
                                    bold('Total Length'),
                                    bold('Coverage'),
                                    bold('Number of Contigs')
                                    )

        with doc.create(pl.Subsection('Sequence Data Quality', numbering=False)) as sequence_section:
            with doc.create(pl.Tabular('|c|c|c|c|')) as table:
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
        create_caption(sequence_section, 'i', 'Total length refers to total number of base pairs in assembly.')



    doc.generate_pdf('ROGA_{}_{}'.format(datetime.today().strftime('%Y-%m-%d'), genus), clean_tex=False)


def produce_header_footer():
    """
    Adds a generic header/footer to the report. Includes the date and CFIA logo in the header, and legend in the footer.
    """
    header = pl.PageStyle("header", header_thickness=0.1)

    image_filename = get_image()
    with header.create(pl.Head("L")) as logo:
        logo.append(pl.StandAloneGraphic(image_options="width=110px", filename=image_filename))

    # Date
    with header.create(pl.Head("R")):
        header.append("Date Report Issued: " + datetime.today().strftime('%Y-%m-%d'))

    # Legend
    with header.create(pl.Foot("C")):
        with header.create(pl.Tabular('lcr')) as table:
            table.add_row(('+ : Pass', '? : Indeterminate', '- : Fail'))

    return header


def create_caption(section, superscript, text):
    """
    Adds a caption preceded by superscripted characters to a table
    :param section: LateX section object
    :param superscript: character(s) to superscript
    :param text: descriptive text
    """
    section.append('\n')
    section.append(bold(pl.NoEscape(r'\textsuperscript{' + superscript + '}')))
    section.append(italic(text))


def get_image():
    """
    :return: full path to image file
    """
    image_filename = os.path.join(os.path.dirname(__file__), 'CFIA_logo.png')
    return image_filename


def validate_genus(seq_list, genus, lab):
    """
    Validates whether or not the expected genus matches the observed genus parsed from combinedMetadata
    :param seq_list:
    :param genus:
    :param lab:
    :return:
    """
    metadata_reports = extract_reports.get_combined_metadata(seq_list)

    valid_status = {}

    for seqid in seq_list:
        df = metadata_reports[seqid]
        observed_genus = df.loc[df['SeqID'] == seqid]['Genus'].values[0]
        if observed_genus == genus:
            valid_status[seqid] = True  # Valid genus
        else:
            valid_status[seqid] = False  # Invalid genus

    return valid_status


def generate_validated_list(seq_list, genus, lab):
    # VALIDATION
    validated_list = []
    validated_dict = validate_genus(seq_list=seq_list, genus=genus, lab=lab)

    for seqid, valid_status in validated_dict.items():
        if validated_dict[seqid]:
            validated_list.append(seqid)
        else:
            print('WARNING: '
                  'Seq ID {} does not match the expected genus of {} and was ignored.'.format(seqid, genus.upper()))
    return validated_list


def parse_geneseekr_profile():
    # TODO: This function needs to parse values from the GeneSeekr_Profile column from combinedMetadata.csv
    pass


def main():
    dummy_list = ['2017-SEQ-0725', '2017-SEQ-0726', '2017-SEQ-0727']
    genus = 'Salmonella'
    lab = 'GTA-CFIA'

    validated_list = generate_validated_list(seq_list=dummy_list,
                                             genus=genus,
                                             lab=lab)

    # GENERATE REPORT
    generate_roga(seq_list=validated_list,
                  genus=genus,
                  lab=lab)

if __name__ == '__main__':
    main()


