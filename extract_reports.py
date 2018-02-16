import glob
import pandas as pd


def create_report_dictionary(report_list, seq_list, id_column):
    """
    :param report_list:
    :param seq_list:
    :param id_column:
    :return:
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


def get_combined_metadata(seq_list):
    """

    :param seq_list:
    :return:
    """
    # Grab every single combinedMetadata file we have
    # all_reports = glob.glob('/mnt/nas/WGSspades/*/reports/combinedMetadata.csv')
    metadata_reports = glob.glob('/home/dussaultf/Documents/COWBAT_TEST/reports/combinedMetadata.csv')
    metadata_report_dict = create_report_dictionary(report_list=metadata_reports, seq_list=seq_list, id_column='SeqID')
    return metadata_report_dict


def get_gdcs(seq_list):
    """

    :param seq_list:
    :return:
    """
    # Grab every single combinedMetadata file we have
    # all_reports = glob.glob('/mnt/nas/WGSspades/*/reports/combinedMetadata.csv')
    gdcs_reports = glob.glob('/home/dussaultf/Documents/COWBAT_TEST/reports/GDCS.csv')
    gdcs_report_dict = create_report_dictionary(report_list=gdcs_reports, seq_list=seq_list, id_column='Strain')
    return gdcs_report_dict

