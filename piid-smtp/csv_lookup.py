import dask.dataframe as dd
import ConfigParser
from pprint import pprint
import json


def create_dtype_dict(dict_string):
    """
    :param dict_string: dictionary string from config.ini
    :return: data type dictionary
    """
    basic_type_dict = {
        'str': str,
        'float': float,
        'int': int,
        'bool': bool,
        'complex': complex,
    }
    tmp_dict = json.loads(dict_string)
    result_dict = dict()
    for key, value in tmp_dict.iteritems():
        result_dict[key] = basic_type_dict[value]
    return result_dict


def pre_process_multispace(filepath, delimiter=" "):
    """
    Preprocess a csv file containing multiple spaces. Creates
    a new CSV file.

    :param filepath: filepath of the CSV file
    :param delimiter: delimiter for the output csv file
    """
    newpath = filepath+".rev.csv"
    with open(filepath, "r") as src_csv_file:
        with open(newpath, "w") as dst_csv_file:
            for src_line in src_csv_file:
                dst_csv_file.write(delimiter.join(src_line.split())+"\n")


class CSVLookupTable(object):
    def __init__(self, filepath, csv_dtypes, delimiter=' ', index_column=None):
        """
        :param filepath: path to csv file
        :param csv_dtypes: data types of csv headers
        :param delimiter: delimiter or separator to use, defaults to space
        :param index_column: column to index for lookup
        :return: dataframe for lookup
        """

        # Read CSV into Dask dataframe
        self.csv_df = dd.read_csv(filepath,
                                  sep=delimiter,
                                  dtype=create_dtype_dict(csv_dtypes), )

        # Index
        self.index_column= index_column
        if index_column is not None:
            self.csv_df.set_index(index_column)

        # Check dtypes
        pprint(self.csv_df.dtypes)

    def set_index(self, csv_index):
        """
        :param csv_index: index column for lookup
        :return: None
        """
        self.csv_df.set_index(csv_index)

    def lookup(self, csv_column, data_value):
        """
        :param csv_column: Name of CSV column header
        :param data_value: Value to look for
        :return: count of lookup results
        """
        return self.csv_df[self.csv_df[csv_column] == data_value].compute()



