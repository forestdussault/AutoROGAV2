import glob
import pandas as pd


def create_report_dictionary(report_list, seq_list, id_column):
    """
    :param report_list: List of paths to report files
    :param seq_list: List of OLC Seq IDs
    :param id_column: Column used to specify primary key
    :return: Dictionary containing Seq IDs as keys and dataframes as values
    """
    # Create empty dict to store reports of interest
    report_dict = {}

    # Iterate over every metadata file
    for report in report_list:
        # Check if the sample we want is in file
        df = pd.read_csv(report)
        samples = df[id_column]
        # Check all of our sequences of interest to see if they are in the combinedMetadata file
        for seq in seq_list:
            if seq in samples.values:
                # Associate dataframe with sampleID
                report_dict[seq] = df
    return report_dict


 # TODO: Fix this for production to retrieve full list of combinedMetadata.csv reports
def get_combined_metadata(seq_list):
    """
    :param seq_list: List of OLC Seq IDs
    :return: Dictionary containing Seq IDs as keys and combinedMetadata dataframes as values
    """
    # Grab every single combinedMetadata file we have
    # all_reports = glob.glob('/mnt/nas/WGSspades/*/reports/combinedMetadata.csv')
    metadata_reports = glob.glob('/home/dussaultf/Documents/COWBAT_TEST_V2/reports/combinedMetadata.csv')
    metadata_report_dict = create_report_dictionary(report_list=metadata_reports, seq_list=seq_list, id_column='SeqID')
    return metadata_report_dict


# TODO: Fix this for production to retrieve full list of GDCS reports
def get_gdcs(seq_list):
    """
    :param seq_list: List of OLC Seq IDs
    :return: Dictionary containing Seq IDs as keys and GDCS dataframes as values
    """
    # Grab every single combinedMetadata file we have
    # all_reports = glob.glob('/mnt/nas/WGSspades/*/reports/combinedMetadata.csv')
    gdcs_reports = glob.glob('/home/dussaultf/Documents/COWBAT_TEST_V2/reports/GDCS.csv')
    gdcs_report_dict = create_report_dictionary(report_list=gdcs_reports, seq_list=seq_list, id_column='Strain')
    return gdcs_report_dict


def validate_genus(seq_list, genus):
    """
    Validates whether or not the expected genus matches the observed genus parsed from combinedMetadata.
    :param seq_list: List of OLC Seq IDs
    :param genus: String of expected genus (Salmonella, Listeria, Escherichia)
    :return: Dictionary containing Seq IDs as keys and a 'valid status' as the value
    """
    metadata_reports = get_combined_metadata(seq_list)

    valid_status = {}

    for seqid in seq_list:
        print('Checking {}'.format(seqid))
        df = metadata_reports[seqid]
        observed_genus = df.loc[df['SeqID'] == seqid]['Genus'].values[0]
        if observed_genus == genus:
            valid_status[seqid] = True  # Valid genus
        else:
            valid_status[seqid] = False  # Invalid genus

    return valid_status


def generate_validated_list(seq_list, genus):
    """
    :param seq_list: List of OLC Seq IDs
    :param genus: String of expected genus (Salmonella, Listeria, Escherichia)
    :return: List containing each valid Seq ID
    """
    # VALIDATION
    validated_list = []
    validated_dict = validate_genus(seq_list=seq_list, genus=genus)

    for seqid, valid_status in validated_dict.items():
        if validated_dict[seqid]:
            validated_list.append(seqid)
        else:
            print('WARNING: '
                  'Seq ID {} does not match the expected genus of {} and was ignored.'.format(seqid, genus.upper()))
    return validated_list


def parse_geneseekr_profile(value):
    """
    Takes in a value from the GeneSeekr_Profile of combinedMetadata.csv and parses it to determine which markers are
    present. i.e. if the cell contains "invA;stn", a list containing invA, stn will be returned
    :param value: String delimited by ';' character containing markers
    :return: List of markers parsed from value
    """
    detected_markers = []
    marker_list = ['invA', 'stn', 'IGS', 'hlyA', 'inlJ', 'VT1', 'VT2', 'VT2f', 'uidA', 'eae']
    markers = value.split(';')
    for marker in markers:
        if marker in marker_list:
            detected_markers.append(marker)
    return detected_markers


def generate_gdcs_dict(gdcs_reports):
    """
    :param gdcs_reports: Dictionary derived from get_gdcs() function
    :return: Dictionary containing parsed GDCS values
    """
    gdcs_dict = {}
    for sample_id, df in gdcs_reports.items():
        # Grab values
        matches = df.loc[df['Strain'] == sample_id]['Matches'].values[0]
        passfail = df.loc[df['Strain'] == sample_id]['Pass/Fail'].values[0]
        gdcs_dict[sample_id] = (matches, passfail)
    return gdcs_dict

