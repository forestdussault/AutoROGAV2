# begin-doc-include

from pylatex.utils import italic, bold
from datetime import datetime
import extract_report_data
import pylatex as pl
import click
import os
import re


# TODO: GDCS + GenomeQAML combined metric. Everything must pass in order to be listed as 'PASS'
# TODO: Port for Redmine usage


"""
A note on Sample IDs:

LSTS ID should be parsed from SampleSheet.csv by the COWBAT pipeline, and available within the combinedMetadata.csv
file that is central to this script's extraction of data. The LSTS ID is available under the SampleName column in
combinedMetadata.csv.O
"""


# TODO: Finish populating this dictionary
lab_info = {
    'GTA-CFIA': ('2301 Midland Ave., Scarborough, ON, M1P 4R7', '(416) 973-0798'),
    'BUR-CFIA': ('3155 Willington Green, Burnaby, BC, V5G 4P2', '(604) 292-6028'),
    'DAR-CFIA': ('1992 Agency Dr., Dartmouth, NS, B2Y 3Z7', '(902) 536-1046'),
    'OLC-CFIA': ('960 Carling Ave, Ottawa, ON, K1A 0Y9', '(613) 759-1220'),
    'OLF-CFIA': ('3851 Fallowfield Rd., Ottawa, ON, K2H 8P9', '(343) 212-0416')
}


def generate_roga(seq_list, genus, lab, source):
    """
    Generates PDF ROGA
    :param seq_list: List of OLC Seq IDs
    :param genus: Expected Genus for samples (Salmonella, Listeria, or Escherichia)
    :param lab: ID for lab report is being generated for
    :param source: string input for source that strains were derived from, i.e. 'ground beef'
    """

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

    # SECOND VALIDATION SCREEN
    if genus == 'Escherichia':
        validated_ecoli_dict = extract_report_data.validate_ecoli(seq_list, metadata_reports)
        vt_list = []
        uida_list = []

        for key, value in validated_ecoli_dict.items():
            ecoli_uida_present = validated_ecoli_dict[key][0]
            ecoli_vt_present = validated_ecoli_dict[key][1]

            uida_list.append(ecoli_uida_present)
            vt_list.append(ecoli_vt_present)

            if not ecoli_uida_present:
                print('WARNING: uidA not present for {}. Cannot confirm E. coli.'.format(key))
            if not ecoli_vt_present:
                print('WARNING: vt marker not detected for {}. Cannot confirm strain is verotoxigenic.'.format(key))

        all_uida = False
        if False not in uida_list:
            all_uida = True

        all_vt = False
        if False not in vt_list:
            all_vt = True

    elif genus == 'Listeria':
        validated_listeria_dict = extract_report_data.validate_mash(seq_list,
                                                                    metadata_reports,
                                                                    'Listeria monocytogenes')
        mono_list = []
        for key, value in validated_listeria_dict.items():
            mono_list.append(value)

        if False not in mono_list:
            all_mono = True
        else:
            all_mono = False

    elif genus == 'Salmonella':
        validated_salmonella_dict = extract_report_data.validate_mash(seq_list,
                                                                      metadata_reports,
                                                                      'Salmonella enterica')
        enterica_list = []
        for key, value in validated_salmonella_dict.items():
            enterica_list.append(value)

        if False not in enterica_list:
            all_enterica = True
        else:
            all_enterica = False

    # DOCUMENT BODY/CREATION
    with doc.create(pl.Section('Report of Genomic Analysis', numbering=False)):
        # LAB SUMMARY
        with doc.create(pl.Tabular('lcr', booktabs=True)) as table:
            table.add_row(bold('Laboratory'),
                          bold('Address'),
                          bold('Tel #'))
            table.add_row(lab, lab_info[lab][0], lab_info[lab][1])

        # TEXT SUMMARY
        with doc.create(pl.Subsection(genus + ' Identification Summary', numbering=False)) as summary:
            if len(metadata_reports) == 1:
                summary.append('Whole-genome sequencing analysis was conducted on {}'
                               ' strain isolated from {}. '.format(len(metadata_reports), source))
            else:
                summary.append('Whole-genome sequencing analysis was conducted on {}'
                               ' strains isolated from {}. '.format(len(metadata_reports), source))

            if genus == 'Escherichia':
                if all_uida:
                    summary.append('All of the following strains are confirmed as ')
                    summary.append(italic('Escherichia coli '))
                    summary.append('based on 16S sequence and the presence of marker gene ')
                    summary.append(italic('uidA. '))
                elif not all_uida:
                    summary.append('Some of the following strains could not be confirmed to be ')
                    summary.append(italic('Escherichia coli '))
                    summary.append('as the ')
                    summary.append(italic('uidA '))
                    summary.append('marker gene was not detected. ')

                if all_vt:
                    summary.append('All strains are confirmed to be verotoxigenic based on presence of the ')
                    summary.append(italic('vt '))
                    summary.append('marker.')

            elif genus == 'Listeria':
                if all_mono:
                    summary.append('All of the following strains are confirmed to be ')
                    summary.append(italic('Listeria monocytogenes '))
                    summary.append('based on GeneSeekr analysis. ')
                else:
                    summary.append('Some of the following strains could not be confirmed to be ')
                    summary.append(italic('Listeria monocytogenes.'))

            elif genus == 'Salmonella':
                if all_enterica:
                    summary.append('All of the following strains are confirmed to be ')
                    summary.append(italic('Salmonella enterica '))
                    summary.append('based on GeneSeekr analysis. ')
                else:
                    summary.append('Some of the following strains could not be confirmed to be ')
                    summary.append(italic('Salmonella enterica.'))

        # ESCHERICHIA TABLE
        if genus == 'Escherichia':
            genesippr_table_columns = (bold('LSTS ID'),
                                       bold(pl.NoEscape(r'uidA{\footnotesize \textsuperscript {a}}')),
                                       bold(pl.NoEscape(r'Serotype')),
                                       bold(pl.NoEscape(r'Verotoxin Profile')),
                                       bold(pl.NoEscape(r'eae{\footnotesize \textsuperscript {a}}')),
                                       bold(pl.NoEscape(r'MLST')),
                                       bold(pl.NoEscape(r'rMLST')),
                                       )

            with doc.create(pl.Subsection('GeneSeekr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabular('|c|c|c|c|c|c|c|')) as table:
                    # Header
                    table.add_hline()
                    table.add_row(genesippr_table_columns)

                    # Rows
                    for sample_id, df in metadata_reports.items():
                        table.add_hline()

                        # ID
                        lsts_id = df.loc[df['SeqID'] == sample_id]['SampleName'].values[0]

                        # Genus (pulled from 16S)
                        genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]

                        # Serotype
                        serotype = df.loc[df['SeqID'] == sample_id]['E_coli_Serotype'].values[0]

                        # Remove % identity
                        fixed_serotype = remove_bracketed_values(serotype)

                        # Verotoxin
                        verotoxin = df.loc[df['SeqID'] == sample_id]['Vtyper_Profile'].values[0]

                        # MLST/rMLST
                        mlst = df.loc[df['SeqID'] == sample_id]['MLST_Result'].values[0]
                        rmlst = df.loc[df['SeqID'] == sample_id]['rMLST_Result'].values[0].replace('-','New')

                        marker_list = df.loc[df['SeqID'] == sample_id]['GeneSeekr_Profile'].values[0]

                        (uida, eae) = '-', '-'
                        if 'uidA' in marker_list:
                            uida = '+'
                        if 'eae' in marker_list:
                            eae = '+'

                        table.add_row((lsts_id, uida, fixed_serotype, verotoxin, eae, mlst, rmlst))
                    table.add_hline()

                create_caption(genesippr_section, 'a', "'+' indicates marker presence : "
                                                       "'-' indicates marker was not detected")

        # LISTERIA TABLE
        if genus == 'Listeria':
            genesippr_table_columns = (bold('LSTS ID'),
                                       bold(pl.NoEscape(r'IGS{\footnotesize \textsuperscript {a}}')),
                                       bold(pl.NoEscape(r'hlyA{\footnotesize \textsuperscript {a}}')),
                                       bold(pl.NoEscape(r'inlJ{\footnotesize \textsuperscript {a}}')),
                                       bold(pl.NoEscape(r'MLST')),
                                       bold(pl.NoEscape(r'rMLST')),
                                       )

            with doc.create(pl.Subsection('GeneSeekr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabular('|c|c|c|c|c|c|')) as table:
                    # Header
                    table.add_hline()
                    table.add_row(genesippr_table_columns)

                    # Rows
                    for sample_id, df in metadata_reports.items():
                        table.add_hline()

                        # ID
                        lsts_id = df.loc[df['SeqID'] == sample_id]['SampleName'].values[0]

                        # Genus
                        genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]

                        # MLST/rMLST
                        mlst = df.loc[df['SeqID'] == sample_id]['MLST_Result'].values[0]
                        rmlst = df.loc[df['SeqID'] == sample_id]['rMLST_Result'].values[0].replace('-','New')

                        # Markers
                        marker_list = df.loc[df['SeqID'] == sample_id]['GeneSeekr_Profile'].values[0]
                        (igs, hlya, inlj) = '-', '-', '-'
                        if 'IGS' in marker_list:
                            igs = '+'
                        if 'hlyA' in marker_list:
                            hlya = '+'
                        if 'inlJ' in marker_list:
                            inlj = '+'

                        table.add_row((lsts_id, igs, hlya, inlj, mlst, rmlst))
                    table.add_hline()
                create_caption(genesippr_section, 'a', "'+' indicates marker presence : "
                                                       "'-' indicates marker was not detected")


        # SALMONELLA TABLE
        if genus == 'Salmonella':
            genesippr_table_columns = (bold('LSTS ID'),
                                       bold(pl.NoEscape(r'Serovar{\footnotesize \textsuperscript {a}}')),
                                       bold(pl.NoEscape(r'H1')),
                                       bold(pl.NoEscape(r'H2')),
                                       bold(pl.NoEscape(r'invA{\footnotesize \textsuperscript {b}}')),
                                       bold(pl.NoEscape(r'stn{\footnotesize \textsuperscript {b}}')),
                                       bold(pl.NoEscape(r'MLST')),
                                       bold(pl.NoEscape(r'rMLST')),
                                       )

            with doc.create(pl.Subsection('GeneSeekr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabular('|c|c|c|c|c|c|c|c|')) as table:
                    # Header
                    table.add_hline()
                    table.add_row(genesippr_table_columns)

                    # Rows
                    for sample_id, df in metadata_reports.items():
                        table.add_hline()

                        # ID
                        lsts_id = df.loc[df['SeqID'] == sample_id]['SampleName'].values[0]

                        # MLST/rMLST
                        mlst = df.loc[df['SeqID'] == sample_id]['MLST_Result'].values[0]
                        rmlst = df.loc[df['SeqID'] == sample_id]['rMLST_Result'].values[0].replace('-','New')

                        # Serovar
                        serovar = df.loc[df['SeqID'] == sample_id]['SISTR_serovar'].values[0]

                        # SISTR H1, H2
                        sistr_h1 = df.loc[df['SeqID'] == sample_id]['SISTR_h1'].values[0].strip(';')
                        sistr_h2 = df.loc[df['SeqID'] == sample_id]['SISTR_h2'].values[0].strip(';')

                        # Markers
                        marker_list = df.loc[df['SeqID'] == sample_id]['GeneSeekr_Profile'].values[0]
                        (inva, stn) = '-', '-'
                        if 'invA' in marker_list:
                            inva = '+'
                        if 'stn' in marker_list:
                            stn = '+'

                        table.add_row((lsts_id, serovar, sistr_h1, sistr_h2, inva, stn, mlst, rmlst))
                    table.add_hline()

                create_caption(genesippr_section, 'a', 'Serovar determined with SISTR v1.x')
                create_caption(genesippr_section, 'b', "'+' indicates marker presence : "
                                                       "'-' indicates marker was not detected")


        #########################

        # SEQUENCE QUALITY METRICS
        sequence_quality_columns = (bold('LSTS ID'),
                                    bold(pl.NoEscape(r'Total Length')),
                                    bold(pl.NoEscape(r'Coverage')),
                                    bold(pl.NoEscape(r'GDCS')),
                                    bold(pl.NoEscape(r'Pass/Fail')),
                                    )

        # Create the sequence table
        with doc.create(pl.Subsection('Sequence Quality Metrics', numbering=False)):
            with doc.create(pl.Tabular('|c|c|c|c|c|')) as table:
                # Header
                table.add_hline()
                table.add_row(sequence_quality_columns)

                # Rows
                for sample_id, df in metadata_reports.items():
                    table.add_hline()

                    # Grab values
                    lsts_id = df.loc[df['SeqID'] == sample_id]['SampleName'].values[0]
                    total_length = df.loc[df['SeqID'] == sample_id]['TotalLength'].values[0]
                    average_coverage_depth = df.loc[df['SeqID'] == sample_id]['AverageCoverageDepth'].values[0]

                    # Fix coverage
                    average_coverage_depth = format(float(average_coverage_depth.replace('X', '')), '.0f')
                    average_coverage_depth = str(average_coverage_depth) + 'X'

                    # Matches
                    matches = gdcs_dict[sample_id][0]

                    passfail = gdcs_dict[sample_id][1]
                    if passfail == '+':
                        passfail = 'Pass'
                    elif passfail == '-':
                        passfail = 'Fail'

                    # Add row
                    table.add_row((lsts_id, total_length, average_coverage_depth, matches, passfail))
                table.add_hline()

        # Pipeline metadata table
        pipeline_metadata_columns = (bold('LSTS ID'),
                                     bold('Seq ID'),
                                     bold('Pipeline Version'),
                                     bold('Database Version'))

        with doc.create(pl.Subsection('Pipeline Metadata', numbering=False)):
            with doc.create(pl.Tabular('|c|c|c|c|')) as table:
                # Header
                table.add_hline()
                table.add_row(pipeline_metadata_columns)

                # Rows
                for sample_id, df in metadata_reports.items():
                    table.add_hline()

                    # LSTS ID
                    lsts_id = df.loc[df['SeqID'] == sample_id]['SampleName'].values[0]

                    # Pipeline version
                    pipeline_version = df.loc[df['SeqID'] == sample_id]['PipelineVersion'].values[0]
                    database_version = pipeline_version  # These have been harmonized
                    # database_version = df.loc[df['SeqID'] == sample_id]['DatabaseVersion'].values[0]

                    # Add row
                    table.add_row((lsts_id, sample_id, pipeline_version, database_version))

                table.add_hline()

        # VERIFIED BY
        with doc.create(pl.Subsubsection('Verified by:', numbering=False)):
            with doc.create(Form()):
                doc.append(pl.Command('noindent'))
                doc.append(pl.Command('TextField',
                                      options=["name=multilinetextbox", "multiline=false", pl.NoEscape("bordercolor=0 0 0"),
                                               pl.NoEscape("width=2.5in"), "height=0.3in"],
                                      arguments=''))

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

    # Footer
    with header.create(pl.Foot("C")):
        with header.create(pl.Tabular('lcr')) as table:
            table.add_row('', bold('Data interpretation guidelines can be found in RDIMS document ID: 1040135'), '')
            table.add_row('', bold('This report was generated with OLC AutoROGA v0.0.1'), '')
    return header


def create_caption(section, superscript, text):
    """
    Adds a caption preceded by superscripted characters to a table
    :param section: LateX section object
    :param superscript: character(s) to superscript
    :param text: descriptive text
    """
    section.append('\n')

    # Superscript
    section.append(bold(pl.NoEscape(r'{\footnotesize \textsuperscript {' + superscript + '}}')))

    # Text
    section.append(italic(pl.NoEscape(r'{\footnotesize {' + text + '}}')))


def remove_bracketed_values(string):
    p = re.compile('\(.*?\)')  # Regex to remove bracketed terms
    new_string = re.sub(p, '', string).replace(' ', '')  # Remove bracketed terms and spaces
    return new_string


def get_image():
    """
    :return: full path to image file
    """
    image_filename = os.path.join(os.path.dirname(__file__), 'CFIA_logo.png')
    return image_filename


class Form(pl.base_classes.Environment):
    """A class to wrap hyperref's form environment."""

    _latex_name = 'Form'

    packages = [pl.Package('hyperref')]
    escape = False
    content_separator = "\n"


def redmine_roga():
    """
    Main method for generating a ROGA. Will eventually be ported over to support Redmine.
    :return:
    """
    # dummy_list = ('2017-SEQ-0725', '2017-SEQ-0724')  # Tuple this to keep the order
    # genus = 'Salmonella'
    #
    # dummy_list = ('2017-SEQ-0773', '2017-SEQ-0772')  # Tuple this to keep the order
    # genus = 'Escherichia'

    dummy_list = ('2017-SEQ-1222', '2017-SEQ-1223')  # Tuple this to keep the order
    genus = 'Listeria'

    lab = 'GTA-CFIA'
    source = 'flour'


    # Validate user input
    if lab not in lab_info:
        print('Input value "{}" not found in laboratory directory. '
              'Please specify a lab name from the following list:'.format(lab))
        for key, value in lab_info.items():
            print('\t' + key)
        quit()

    if genus not in ['Escherichia', 'Salmonella', 'Listeria']:
        print('Input genus {} does not match any of the acceptable values which include: '
              '"Escherichia", "Salmonella", "Listeria"'.format(genus))
        quit()

    # Validate Seq IDS
    validated_list = extract_report_data.generate_validated_list(seq_list=dummy_list,
                                                                 genus=genus)

    if len(validated_list) == 0:
        print('ERROR: No samples provided matched the expected genus. Quitting.'.format(genus.upper()))
        quit()

    # GENERATE REPORT
    generate_roga(seq_list=validated_list,
                  genus=genus,
                  lab=lab,
                  source=source)
    print('Generated ROGA successfully.')


if __name__ == '__main__':
    redmine_roga()
