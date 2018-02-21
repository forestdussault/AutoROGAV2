# begin-doc-include

from pylatex.utils import italic, bold
from datetime import datetime
import extract_report_data
import pylatex as pl
import click
import os
import re


# TODO: Add rMLST, MLST
# TODO: GDCS + GenomeQAML combined metric. Everything must pass in order to be listed as 'PASS'
# TODO: Make a companion document that desribes the metrics and how they were achieved in detail
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


def redmine_roga():
    """
    Main method for generating a ROGA. Will eventually be ported over to support Redmine.
    :return:
    """
    # dummy_list = ('2017-SEQ-0725',)  # Tuple this to keep the order
    # genus = 'Salmonella'

    dummy_list = ('2017-SEQ-0773',)  # Tuple this to keep the order
    genus = 'Escherichia'
    #
    # dummy_list = ('2017-SEQ-1222', '2017-SEQ-1223')  # Tuple this to keep the order
    # genus = 'Listeria'

    lab = 'GTA-CFIA'

    validated_list = extract_report_data.generate_validated_list(seq_list=dummy_list,
                                                                 genus=genus)
    if len(validated_list) == 0:
        print('ERROR: No samples provided matched the expected genus. Quitting.'.format(genus.upper()))
        quit()

    # GENERATE REPORT
    generate_roga(seq_list=validated_list,
                  genus=genus,
                  lab=lab)
    print('Generated ROGA successfully.')


def generate_roga(seq_list, genus, lab):
    """
    Generates PDF ROGA
    :param seq_list: List of OLC Seq IDs
    :param genus: Expected Genus for samples (Salmonella, Listeria, or Escherichia)
    :param lab: ID for lab report is being generated for
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

    # DOCUMENT BODY/CREATION
    with doc.create(pl.Section('Report of Genomic Analysis', numbering=False)):
        # LAB SUMMARY
        with doc.create(pl.Tabular('lcr', booktabs=True)) as table:
            table.add_row(bold('Laboratory'),
                          bold('Address'),
                          bold('Tel #'))
            table.add_row(lab, lab_info[lab][0], lab_info[lab][1])

        # TEXT SUMMARY
        with doc.create(pl.Subsection('Identification Summary', numbering=False)) as summary:
            summary.append('The following strains are confirmed to be ')
            summary.append(italic(genus + ' '))

            if genus == 'Escherichia':
                summary.append('based on 16S sequence and presence of marker gene ')
                summary.append(italic('uidA.'))
            else:
                summary.append('.')

        # ESCHERICHIA TABLE
        if genus == 'Escherichia':
            genesippr_table_columns = (bold('LSTS ID'),  # TODO: Convert to LSTS
                                       # bold(pl.NoEscape(r'VT1{\footnotesize \textsuperscript {b}}')),
                                       # bold(pl.NoEscape(r'VT2{\footnotesize \textsuperscript {b}}')),
                                       # bold(pl.NoEscape(r'VT2f{\footnotesize \textsuperscript {b}}')),
                                       bold(pl.NoEscape(r'Verotoxin Profile{\footnotesize \textsuperscript {a}}')),
                                       bold(pl.NoEscape(r'uidA{\footnotesize \textsuperscript {b}}')),
                                       bold(pl.NoEscape(r'eae{\footnotesize \textsuperscript {b}}')),
                                       bold(pl.NoEscape(r'Predicted Serotype{\footnotesize \textsuperscript {c}}')))

            with doc.create(pl.Subsection('GeneSeekr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabular('|c|c|c|c|c|')) as table:
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
                        vtyper = df.loc[df['SeqID'] == sample_id]['Vtyper_Profile'].values[0]

                        # Getting marker status. There is certainly a nicer way to do this.
                        marker_list = df.loc[df['SeqID'] == sample_id]['GeneSeekr_Profile'].values[0]
                        (vt1, vt2, vt2f, uida, eae) = '-', '-', '-', '-', '-'
                        # if 'VT1' in marker_list:
                        #     vt1 = '+'
                        # if 'VT2' in marker_list:
                        #     vt2 = '+'
                        # if 'VT2f' in marker_list:
                        #     vt2f = '+'
                        if 'uidA' in marker_list:
                            uida = '+'
                        if 'eae' in marker_list:
                            eae = '+'
                        table.add_row((lsts_id, vtyper, uida, eae, fixed_serotype))
                    table.add_hline()

                create_caption(genesippr_section, 'a', '"+" indicates marker presence, "-" indicates marker was not detected')
                create_caption(genesippr_section, 'b', 'Antigen determination based on databases available at the '
                                                         'Center for Genomic Epidemiology (https://cge.cbs.dtu.dk).'
                                                         '\nPercent Identity relative to serotype marker is '
                                                         'indicated in parentheses.')

        # LISTERIA TABLE
        if genus == 'Listeria':
            genesippr_table_columns = (bold('LSTS ID'),  # TODO: Convert to LSTS
                                       bold(pl.NoEscape(r'IGS{\footnotesize \textsuperscript {a}}')),
                                       bold(pl.NoEscape(r'hlyA{\footnotesize \textsuperscript {a}}')),
                                       bold(pl.NoEscape(r'inlJ{\footnotesize \textsuperscript {a}}')))

            with doc.create(pl.Subsection('GeneSippr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabular('|c|c|c|c|')) as table:
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

                        # # Serotype # TODO: grab this value
                        # serotype = 'temp'

                        # Markers
                        marker_list = df.loc[df['SeqID'] == sample_id]['GeneSeekr_Profile'].values[0]
                        (igs, hlya, inlj) = '-', '-', '-'
                        if 'IGS' in marker_list:
                            igs = '+'
                        if 'hlyA' in marker_list:
                            hlya = '+'
                        if 'inlJ' in marker_list:
                            inlj = '+'

                        table.add_row((lsts_id, igs, hlya, inlj))
                    table.add_hline()
                create_caption(genesippr_section, 'a', '"+" indicates marker presence, "-" indicates marker absence')


        # SALMONELLA TABLE
        if genus == 'Salmonella':
            genesippr_table_columns = (bold('LSTS ID'),  # TODO: Convert to LSTS
                                       bold(pl.NoEscape(r'Serovar{\footnotesize \textsuperscript {b}}')),
                                       bold(pl.NoEscape(r'invA{\footnotesize \textsuperscript {c}}')),
                                       bold(pl.NoEscape(r'stn{\footnotesize \textsuperscript {c}}')),)

            with doc.create(pl.Subsection('GeneSippr Analysis', numbering=False)) as genesippr_section:
                with doc.create(pl.Tabular('|c|c|c|c|c|')) as table:
                    # Header
                    table.add_hline()
                    table.add_row(genesippr_table_columns)

                    # Rows
                    for sample_id, df in metadata_reports.items():
                        table.add_hline()

                        # ID
                        lsts_id = df.loc[df['SeqID'] == sample_id]['SampleName'].values[0]

                        # Genus
                        # genus = df.loc[df['SeqID'] == sample_id]['Genus'].values[0]

                        # Serovar
                        serovar = df.loc[df['SeqID'] == sample_id]['SISTR_serovar'].values[0]

                        # Markers
                        marker_list = df.loc[df['SeqID'] == sample_id]['GeneSeekr_Profile'].values[0]
                        (inva, stn) = '-', '-'
                        if 'invA' in marker_list:
                            inva = '+'
                        if 'stn' in marker_list:
                            stn = '+'

                        table.add_row((lsts_id, serovar, inva, stn))
                    table.add_hline()

                create_caption(genesippr_section, 'a', 'Serovar determined with SISTR v1.x')
                create_caption(genesippr_section, 'b', '"+" indicates marker presence, "-" indicates marker absence')

        #########################
        #########################

        # SEQUENCE QUALITY METRICS
        sequence_quality_columns = (bold('LSTS ID'),
                                    bold(pl.NoEscape(r'Total Length{\footnotesize \textsuperscript {a}}')),
                                    bold(pl.NoEscape(r'Coverage{\footnotesize \textsuperscript {b}}')),
                                    bold(pl.NoEscape(r'rMLST{\footnotesize \textsuperscript {c}}')),
                                    bold(pl.NoEscape(r'MLST{\footnotesize \textsuperscript {c}}')),
                                    bold(pl.NoEscape(r'GDCS{\footnotesize \textsuperscript {d}}')),
                                    bold(pl.NoEscape(r'Pass/Fail{\footnotesize \textsuperscript {e}}')),
                                    )

        # Create the sequence table
        with doc.create(pl.Subsection('Sequence Quality Metrics', numbering=False)) as sequence_section:
            with doc.create(pl.Tabular('|c|c|c|c|c|c|c|')) as table:
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
                    mlst = df.loc[df['SeqID'] == sample_id]['MLST_Result'].values[0]
                    rmlst = df.loc[df['SeqID'] == sample_id]['rMLST_Result'].values[0]

                    # Fix coverage
                    average_coverage_depth = format(float(average_coverage_depth.replace('X','')), '.0f')
                    average_coverage_depth = str(average_coverage_depth) + 'X'

                    # Matches
                    matches = gdcs_dict[sample_id][0]

                    passfail = gdcs_dict[sample_id][1]
                    if passfail == '+':
                        passfail = 'Pass'
                    elif passfail == '-':
                        passfail = 'Fail'

                    # Add row
                    table.add_row((lsts_id, total_length, average_coverage_depth, mlst, rmlst, matches, passfail))
                table.add_hline()
        create_caption(sequence_section, 'a', 'Total length refers to the total number of nucleotides in '
                                                'the assembled sequence data.')
        create_caption(sequence_section, 'b', 'Coverage refers to sequencing redundancy. '
                                               'A minimum coverage of 20X indicates that, on average, '
                                               'each nucleotide in the genome has been covered by 20 sequence reads.')
        create_caption(sequence_section, 'c', 'Something about rMLST and MLST')
        create_caption(sequence_section, 'd', 'Sequence data is queried for Genomically Dispersed Conserved Sequences'
                                              ' (GDCS) which currently include 53 ribosomal proteins distributed '
                                              'throughout the genome and conserved in all bacterial species.')
        create_caption(sequence_section, 'e', 'Pass/Fail is determined by evaluating the number of GDCS matches.')



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

    # # REFERENCES
    # with doc.create(pl.Subsubsection('References', numbering=False)):
    #     with doc.create(pl.Enumerate()) as enum:
    #         enum.add_item(pl.FootnoteText("Hayashi T, Makino K, Ohnishi M, Kurokawa K, Ishii K, Yokoyama K, Han CG, Ohtsubo E, "
    #                       "Nakayama K, Murata T et al. 2001. Complete genome sequence of enterohemorrhagic Escherichia "
    #                       "coli O157:H7 and genomic comparison with a laboratory strain K-12. "
    #                       "DNA Res 2001, 8(1):11-22."))
    #         enum.add_item(pl.FootnoteText("Jaureguy F, Landraud L, Passet V, Diancourt L, Frapy E, Guigon G, et al. 2008. Phylogenetic "
    #                       "and "
    #                       "genomic diversity of human bacteremic Escherichia coli strains. BMC Genomics. 9:560."))
    #         enum.add_item(pl.FootnoteText("Jolley KA, Bliss CM, Bennett JS, Bratcher HB, et al. 2012. "
    #                                       "Ribosomal multilocus sequence typing: universal characterization of bacteria "
    #                                       "from domain to strain. Microbiology. 158:1005-15"))
    #         enum.add_item(pl.FootnoteText("Carrillo CD, Koziol AG, Mathews A, Goji N, Lambert D, "
    #                                       "Huszczynski G, Gauthier M, Amoako K K, Blais B. 2016. "
    #                                       "Comparative evaluation of genomic and laboratory approaches for "
    #                                       "determination of shiga toxin subtypes in Escherichia coli. "
    #                                       "Journal of Food Protection 79(12):2078-2085."))


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
            table.add_row(('', bold('Report generated via OLC AutoROGA v0.0.1'), ''))

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
    # section.append(bold(pl.NoEscape('{}. '.format(superscript)))
    # section.append(bold(pl.NoEscape(r'\textsuperscript{' + superscript + '}')))

    # Text
    section.append(italic(pl.NoEscape(r'{\footnotesize {' + text + '}}')))
    # section.append(italic('\t' + pl.NoEscape(r'\fontsize{10}{' + text + '}')))


def remove_bracketed_values(string):
    p = re.compile('\(.*?\)')  # Regex to remove bracketed terms
    new_string = re.sub(p, '', string).replace(' ','')  # Remove bracketed terms and spaces
    return new_string


def get_image():
    """
    :return: full path to image file
    """
    image_filename = os.path.join(os.path.dirname(__file__), 'CFIA_logo.png')
    return image_filename


if __name__ == '__main__':
    redmine_roga()
