import copy
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import random


def encode_df(df, data_types={}):
    """
    Encode columns so their values are usable in vector operations. Making a few 
    assumptions here, like that datetime should be an integer, and that it's 
    acceptable to fill NaNs with 0.
    """

    numbers = []
    categories = []
    datetimes = []
        
    for column, series in df.iteritems():
        if column in data_types:
            dtypes = data_types[column]
        else:
            dtypes = {}
        
        if 'datetime' in dtypes:
            index = pd.DatetimeIndex(pd.to_datetime(series.values))
            df[column] = index.astype(np.int64).astype(float)
            datetimes.append(column)
            
        elif any([dtype in dtypes for dtype in ['category', 'label']]):
            # If this can be treated as a category, encode it
            df = pd.get_dummies(df,columns=[column])
            categories.append(column)
                    
        elif 'numeric' in dtypes:
            df[column] = clean_numbers(df[column].values)
            df[column] = df[column].astype(float)
            numbers.append(column)
            
        else:
            df.drop(column,1,inplace=True)

    # Scale continuous columns
    scaler = MinMaxScaler()
    df[numbers + datetimes] = scaler.fit_transform(df[numbers + datetimes])
    
    return df, categories, numbers, datetimes


def ordinal_encoding(X_in, mapping=None, cols=None):
    """
    Ordinal encoding uses a single column of integers to represent the classes. An optional mapping dict can be passed
    in, in this case we use the knowledge that there is some true order to the classes themselves. Otherwise, the classes
    are assumed to have no true order and integers are selected at random.

    :param X:
    :return:
    """

    X = copy.deepcopy(X_in)

    if cols is None:
        cols = X.columns.values

    mapping_out = []
    if mapping is not None:
        for switch in mapping:
            for category in switch.get('mapping'):
                X.loc[X[switch.get('col')] == category[0], switch.get('col')] = str(category[1])
            X[switch.get('col')] = X[switch.get('col')].astype(int).reshape(-1, )
    else:
        for col in cols:
            categories = list(set(X[col].values))
            random.shuffle(categories)
            for idx, val in enumerate(categories):
                X.loc[X[col] == val, col] = str(idx)
            X[col] = X[col].astype(int).reshape(-1, )
            mapping_out.append({'col': col, 'mapping': [(x[1], x[0]) for x in list(enumerate(categories))]},)

    return X, mapping_out


class OrdinalEncoder(BaseEstimator, TransformerMixin):
    """
    Ordinal encoding uses a single column of integers to represent the classes. An optional mapping dict can be passed
    in, in this case we use the knowledge that there is some true order to the classes themselves. Otherwise, the classes
    are assumed to have no true order and integers are selected at random.
    """
    def __init__(self, verbose=0, mapping=None, cols=None):
        """

        :param verbose: foo
        :param mapping: bar
        :param cols: baz
        :return:
        """
        self.verbose = verbose
        self.cols = cols
        self.mapping = mapping

    def fit(self, X, y=None, **kwargs):
        """
        Fit doesn't actually do anything in this case.  So the same object is just returned as-is.

        :param X:
        :param y:
        :param kwargs:
        :return:
        """

        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        _, categories = ordinal_encoding(X, mapping=self.mapping, cols=self.cols)
        self.mapping = categories

        return self

    def transform(self, X):
        """
        Will use the mapping (if available) and the column list (if available, otherwise every column) to encode the
        data ordinally.

        :param X:
        :return:
        """

        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        X, _ = ordinal_encoding(X, mapping=self.mapping, cols=self.cols)
        return X

def binary(X_in, cols=None):
    """
    Binary encoding encodes the integers as binary code with one column per digit.

    :param X:
    :return:
    """

    X = copy.deepcopy(X_in)

    if cols is None:
        cols = X.columns.values

    bin_cols = []
    for col in cols:
        # figure out how many digits we need to represent the classes present
        if X[col].max() == 0:
            digits = 1
        else:
            digits = int(np.ceil(np.log2(X[col].max())))

        # map the ordinal column into a list of these digits, of length digits
        X[col] = X[col].map(lambda x: list("{0:b}".format(int(x)))) \
            .map(lambda x: x if len(x) == digits else [0 for _ in range(digits - len(x))] + x)

        for dig in range(digits):
            X[unicode(col) + u'_' + unicode(dig)] = X[col].map(lambda x: int(x[dig]))
            bin_cols.append(unicode(col) + u'_' + unicode(dig))

    X = X.reindex(columns=bin_cols)

    return X



class BinaryEncoder(BaseEstimator, TransformerMixin):
    """
    Binary encoding encodes the integers as binary code with one column per digit.

    """
    def __init__(self, verbose=0, cols=None):
        """

        :param verbose:
        :param cols:
        :return:
        """

        self.verbose = verbose
        self.cols = cols
        self.ordinal_encoder = OrdinalEncoder(verbose=verbose, cols=cols)

    def fit(self, X, y=None, **kwargs):
        """

        :param X:
        :param y:
        :param kwargs:
        :return:
        """

        self.ordinal_encoder = self.ordinal_encoder.fit(X)

        return self

    def transform(self, X):
        """

        :param X:
        :return:
        """

        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        X = self.ordinal_encoder.transform(X)

        return binary(X, cols=self.cols)
