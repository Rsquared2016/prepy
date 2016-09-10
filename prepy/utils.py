import md5
import urlparse
import urllib
import os
import time
import re

def is_four_digit_year(values):
    new_values = [v for v in values if v and str(v) != 'nan']
    if float(len(new_values))/len(values) > .5 and all([len(str(v)) is 4 and str(v)[0] in ['1','2'] for v in new_values]):
        return True

    return False


def get_limit_value(query):
    regex = re.compile(r" limit ", flags=re.I)
    pieces = regex.split(query)

    limit_value = None
    
    if len(pieces) > 1:
        if ',' in pieces[1]:
            offset_value,limit_value = [int(v.strip()) for v in pieces[1].split(',')]
        else:
            limit_value = int(pieces[1].strip())

    return limit_value


def prep_query(query, limit=1000, offset=0):
    query = query.replace(';','').replace('\n',' ').replace('\r', ' ')
    
    offset_keyword = ' offset '
    limit_keyword = ' limit '
    order_keyword = ' order by '
    
    limit_value = limit
    offset_value = offset
    order_by_clause = None
    
    base_query = query
    
    if offset_keyword in base_query.lower():
        regex = re.compile(r""+offset_keyword, flags=re.I)
        pieces = regex.split(base_query)
        base_query = pieces[0]
        
        if len(pieces) > 1:
            _offset_value = int(pieces[1].strip())
            if offset == 0:
                offset_value = _offset_value
    
    if limit_keyword in base_query.lower():
        regex = re.compile(r""+limit_keyword, flags=re.I)
        pieces = regex.split(base_query)
        base_query = pieces[0]
        
        if len(pieces) > 1:
            if ',' in pieces[1]:
                _offset_value,_limit_value = [int(v.strip()) for v in pieces[1].split(',')]
                if offset_value == 0:
                    offset_value = _offset_value
            else:
                _limit_value = int(pieces[1].strip())
            
            if _limit_value < limit_value:
                limit_value = _limit_value
    
    if order_keyword in base_query.lower():
        regex = re.compile(r""+order_keyword, flags=re.I)
        pieces = regex.split(base_query)
        base_query = pieces[0]
        
        if len(pieces) > 1:
            order_by_clause = pieces[1]
        else:
            order_by_clause = '1'
    else:
        order_by_clause = '1'
    
    new_query = base_query + order_keyword + order_by_clause + limit_keyword + str(limit_value) + offset_keyword + str(offset_value) + ';' 
    
    return new_query    


def get_sample_values(values, sample_size=100):
    if len(values) < sample_size:
        sample_size = len(values)

    short_list = list(np.random.choice(values,
                        size=sample_size,replace=False))
    without_nan = [x for x in short_list if unicode(x) != 'nan']

    return without_nan


def get_file(url, tmp_dir = ''):
    urlpath = urlparse.urlparse(url).path
    ext = os.path.splitext(urlpath)[1]

    m = md5.new()
    m.update(str(url))
    tmp_file = m.hexdigest() + ext
    path = tmp_dir + tmp_file
    
    try:
        last_update_ago = 0
        if os.path.isfile(path):
            last_update_ago = time.time() - os.path.getmtime(path)
        if last_update_ago == 0 or last_update_ago > 10:
            urllib.urlretrieve(url, path)
    except Exception, e:
        print e
        return None
        
    return path
