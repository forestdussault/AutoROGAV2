# begin-doc-include

from pylatex.utils import italic, bold
from datetime import datetime
import extract_report_data
import pylatex as pl
import click
import os


# TODO: Add LSTS ID.
# TODO: Add rMLST, MLST
# TODO: GDCS + GenomeQAML combined metric. Everything must pass in order to be listed as 'PASS'.


lab_info = {
    'GTA-CFIA': ('2301 Midland Ave., Scarborough, ON, M1P 4R7', '(416) 973-0798'),
    'OLF-CFIA': ('3851 Fallowfield Rd., Ottawa, ON, K2H 8P9', '(343) 212-0416')
}


def redmine_roga():
    dummy_list = ('2017-SEQ-0725', '2017-SEQ-0726', '2017-SEQ-0727')  # Tuple this to keep the order
    genus = 'Salmonella'
    lab = 'GTA-CFIA'

    validated_list = extract_report_data.generate_validated_list(seq_list=dummy_list,
                                             genus=genus)
    if len(validated_list) == 0:
        print('ERROR: No samples provided matched the expected genus {}. Quitting.'.format(genus.upper()))
        quit()

    # GENERATE REPORT
    generate_roga(seq_list=validated_list,
                  genus=genus,
                  lab=lab)
    print('Generated ROGA successfully.')


def generate_roga(seq_list, genus, lab):

    # Grab combinedMetadata dataframes for each requested Seq ID
    metadata_reports = extract_report_data.get_combined_metadata(seq_list)

    # Grab GDCS data for each requested Seq ID
    gdcs_reports = extract_report_data.get_gdcs(seq_list)
    gdcs_dict = extract_report_data.generate_gdcs_dict(gdcs_reports)

    # Page setup
    geometry_options = {"tmargin": "2cm",
                        "lmargin": "1.8cm",
                        "rmargin": "1.8cm",
                        "headsep": "1cm"}

    doc = pl.Document(page_numbers=False,
                      geometry_options=geometry_options)

    header = produce_header_footer()

    doc.preamble.append(header)
    doc.change_document_style("header")

    # DOCUMENT BODY/CREATION
    with doc.create(pl.Section('Report of Genomic Analysis', numbering=False)):
        # LAB SUMMARY
        with doc.create(pl.Tabu('lcr', booktabs=True)) as table:
            table.add_row(bold('Laboratory'),
                          bold('Address'),
                          bold('Tel #'))
            table.add_row(lab, lab_info[lab][0], lab_info[lab][1])

        # TEXT SUMMARY
        with doc.create(pl.Subsection('Identification Summary', numbering=False)) as summary:
            summary.append('The following strains are confirmed to be ')
            summary.append(italic(genus))
            summary.append('.')

        # ESCHERICHIA TABLE
        if genus == 'Escherichia':
            genesippr_table_columns = (bold('LSTS ID'),  # TODO: Convert to LSTS
                                       bold('Genus'),
                                       bold('VT1'),
                                       bold('VT2'),
                                       bold('VT2f'),
                                       bold('uidA'),
                                       bold('eae'))

            with doc.create(pl.Subsection('GeneSippr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabularx('|c|c|c|c|c|c|c|')) as table:
                    # Header
                    table.add_hline()
                    table.add_row(genesippr_table_columns)

                    # Rows
                    for sample_id, df in metadata_reports.items():
                        table.add_hline()
                        genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]

                        # Getting marker status. There is certainly a nicer way to do this.
                        marker_list =  df.loc[df['SeqID'] == sample_id]['GeneSeekr_Profile'].values[0]
                        (vt1, vt2, vt2f, uida, eae) = '-', '-', '-', '-', '-'
                        if 'VT1' in marker_list: vt1 = '+'
                        if 'VT2' in marker_list: vt2 = '+'
                        if 'VT2f' in marker_list: vt2f = '+'
                        if 'uidA' in marker_list: uida = '+'
                        if 'eae' in marker_list: eae = '+'
                        table.add_row((sample_id, genus, vt1, vt2, vt2f, uida, eae))
                    table.add_hline()

                create_caption(genesippr_section, 'i', 'caption')
                create_caption(genesippr_section, 'ii', 'another caption')

        # LISTERIA TABLE
        if genus == 'Listeria':
            genesippr_table_columns = (bold('LSTS ID'),  # TODO: Convert to LSTS
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

                        # Genus
                        genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]

                        # Serotype # TODO: grab this value
                        serotype = 'temp'

                        # Markers
                        marker_list =  df.loc[df['SeqID'] == sample_id]['GeneSeekr_Profile'].values[0]
                        (igs, hlya, inlj) = '-', '-', '-'
                        if 'IGS' in marker_list: igs = '+'
                        if 'hlyA' in marker_list: hlya = '+'
                        if 'inlJ' in marker_list: inlj = '+'

                        table.add_row((sample_id, genus, serotype, igs, hlya, inlj))
                    table.add_hline()

                create_caption(genesippr_section, 'i', 'caption')
                create_caption(genesippr_section, 'ii', 'another caption')

        # SALMONELLA TABLE
        if genus == 'Salmonella':
            genesippr_table_columns = (bold('LSTS ID'),  # TODO: Convert to LSTS
                                       bold('Genus'),
                                       bold('Serovar'),
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

                        # Genus
                        genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]

                        # Serovar
                        serovar = df.loc[df['SeqID'] == sample_id]['SISTR_serovar'].values[0]

                        # Markers
                        marker_list = df.loc[df['SeqID'] == sample_id]['GeneSeekr_Profile'].values[0]
                        (inva, stn) = '-', '-'
                        if 'invA' in marker_list: inva = '+'
                        if 'stn' in marker_list: stn = '+'

                        table.add_row((sample_id, genus, serovar, inva, stn))
                    table.add_hline()

                create_caption(genesippr_section, 'i', 'caption')
                create_caption(genesippr_section, 'ii', 'another caption')

        #########################
        #########################

        # SEQUENCE DATA QUALITY
        sequence_quality_columns = (bold('Seq ID'),
                                    bold('Total Length'),
                                    bold('Coverage'),
                                    bold('# of Contigs'),
                                    bold('GDCS Matches'),
                                    bold('Pass/Fail')
                                    )

        # Create the sequence table
        with doc.create(pl.Subsection('Sequence Data Quality', numbering=False)) as sequence_section:
            with doc.create(pl.Tabular('|c|c|c|c|c|c|')) as table:
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
                    matches = gdcs_dict[sample_id][0]
                    passfail = gdcs_dict[sample_id][1]

                    # Add row
                    table.add_row((sample_id, total_length, average_coverage_depth, num_contigs, matches, passfail))
                table.add_hline()
        create_caption(sequence_section, 'i', 'Total length refers to the total number of base pairs in the assembly')

        # Pipeline metadata table
        pipeline_metadata_columns = (bold('Seq ID'),
                                     bold('Pipeline Version'))  # TODO: Parse in database version once it's ready

        with doc.create(pl.Subsection('Pipeline Metadata', numbering=False)) as sequence_section:
            with doc.create(pl.Tabular('|c|c|')) as table:
                # Header
                table.add_hline()
                table.add_row(pipeline_metadata_columns)

                # Rows
                for sample_id, df in metadata_reports.items():
                    table.add_hline()

                    # Grab values
                    pipeline_version = df.loc[df['SeqID'] == sample_id]['PipelineVersion'].values[0]
                    # database_version = df.loc[df['SeqID'] == sample_id]['DatabaseVersion'].values[0]

                    # Add row
                    table.add_row((sample_id, pipeline_version))

                table.add_hline()
        create_caption(sequence_section, 'i', 'text.')

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


if __name__ == '__main__':
    redmine_roga()
