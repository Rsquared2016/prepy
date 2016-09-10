from .utils import prep_query, get_file
from .clean_value import header_cleaner
import sqlalchemy
import csv
import pandas as pd
import traceback

def determine_type(**kwargs):
    if 'connection_string' in kwargs and kwargs['connection_string']:
        return 'sql'

    elif 'file_path' in kwargs and kwargs['file_path']:
        ext = str(kwargs['file_path']).split('.')[-1]
        if ext in ['xls','xlsx']:
            return 'xls'
        elif ext == 'json':
            return 'json'
        else:
            return 'csv'

    elif 'url' in kwargs:
        ext = kwargs['url'].split('.')[-1]
        if ('sheetname' in kwargs and kwargs['sheetname']) or ext in ['xls','xlsx']:
            return 'e_xls'
        elif ext == 'json':
            return 'e_json'
        else:
            return 'e_csv'


def get_json_df(path, json_data=None, limit=None):
    if json_data is None:
        json_data = parse_json(path)
    
    if json_data is None:
        return None
    
    docs = find_docs(json_data)
    if docs is None:
        return None

    try:
        if limit:
            docs = docs[:limit]
        df = pd.DataFrame([flatten_dict(d) for d in docs])
        return df
    except:
        return None


def get_sql_df(query, connection_string, limit, offset):
    if offset is None:
        offset = 0

    finished = False

    query = prep_query(query, limit=limit, offset=offset)

    engine = sqlalchemy.create_engine(connection_string)
    df = pd.read_sql_query(sql=query, con=engine)

    if df is not None and len(df) < limit or len(df) == 0:
        finished = True

    last_retrieved_record = offset + len(df)

    return df,finished,last_retrieved_record


def get_csv_df(path,limit,offset):
    df = None
    finished = False
    last_retrieved_record = None

    if offset is None:
        offset = 0

    delimiter = ','
    
    try:
        with open(path) as f1:
            # (50 * 40 * 2 + 200) * 4 = 16800 * 10 lines
            dialect = csv.Sniffer().sniff(f1.read(168000))
            if dialect.delimiter and unicode(dialect.delimiter) != delimiter:
                delimiter = dialect.delimiter
    except Exception, e:
        pass

    if delimiter not in ['\t',';',',']:
        delimiter = ','

    for encoding in ['', 'ascii', 'utf-8', 'utf-16']:
        if df is not None:
            continue
    
        try:
            df_kwargs = { 
                'error_bad_lines': False,  
                'parse_dates': True,
                'index_col': False,
                'nrows': limit
            }

            if offset != 0:
                df_kwargs['skiprows'] = range(1,offset)

            if encoding:
                df_kwargs['encoding'] = encoding

            if delimiter != ',':
                df_kwargs['delimiter'] = delimiter

            df = pd.read_csv(path, **df_kwargs)

        except Exception, e:
            continue

    if df is not None:
        if len(df) < limit:
            finished = True

        last_retrieved_record = len(df) - 1 + offset

    return df,finished,last_retrieved_record


def get_df(**kwargs):
    df = None
    last_retrieved_record = None
    finished = False
    batch_size = 5000000

    if 'last_retrieved_record' in kwargs:
        last_retrieved_record = kwargs['last_retrieved_record']

    if 'limit' in kwargs and kwargs['limit'] < batch_size:
        batch_size = kwargs['limit']

    if 'rows' in kwargs:
        df = pd.DataFrame(kwargs['rows'])
        finished = True
    else:
        source_type = determine_type(**kwargs)

        if source_type == 'sql':
            df,finished,last_retrieved_record = get_sql_df(kwargs['query'],
                                        kwargs['connection_string'],
                                        batch_size, 
                                        last_retrieved_record)
        
        elif source_type in ['xls','e_xls']:
            if source_type == 'e_xls':
                path = get_file(kwargs['url'])
            else:
                path = kwargs['file_path']

            if 'sheetname' in kwargs:
                df = pd.read_excel(path, kwargs['sheetname'])
            else:
                df = pd.read_excel(path)
            finished = True
            last_retrieved_record = len(df) - 1        
        
        elif source_type in ['e_json', 'json']:
            if source.type == 'e_json':
                path = get_file(kwargs['url'])
            else:
                path = kwargs['file_path']
            df = get_json_df(path)
            finished = True
            last_retrieved_record = len(df) - 1
        
        elif source_type in ['e_csv', 'csv']:
            if source_type == 'e_csv':
                path = get_file(kwargs['url'])
            else:
                path = kwargs['file_path']

            df,finished,last_retrieved_record = get_csv_df(path,batch_size,
                                                        last_retrieved_record)


    if df is not None and len(df) > 0:
        columns = [header_cleaner(c) for c in df.columns]
        used = []
        for c in columns:
            if c in used:
                c = c + '_1'
            used.append(c)

        df.columns = used
    
    if df is not None and len(df) == 0:
        finished = True
    
    return df, finished, last_retrieved_record


def get_sample(df, ratio=.2, max_rows=200):
    sample_amount = int(len(df) * ratio)
    if max_rows > sample_amount:
        max_rows = sample_amount
    
    return df.sample(n=max_rows)
