Prepy
========

Real life data is messy and uncooperative. This package is a handful of utilities for preparing, coercing, and outright forcing data to behave. 

### Setup

```bash
git clone https://github.com/popily/prepy
cd prepy
pip install -r requirements.txt
```

### Using prepy

We've broken data munging into three primary tasks. 

1. *Data acquisition* - pulling data into a [pandas](http://pandas.pydata.org/) `dataframe` from a tabular data source, such as a CSV file, Excel file, or SQL database.

2. *Type coercion* - ensuring a column of data will behave as you expect when performing calculations, particularly aggregations.

3. *Preparation for machine learning* - this includes type coercion, but also making sure categorical columns are represented in the way that's expected by most machine learning algorithms. 

#### Data acquisition

Prepy can retrieve data from CSV files, Excel files (including CSV and Excel files from a URL), a Python array of dictionaries, and SQL databases (at the moment Postgres and MySQL are supported). The excellent `pandas` library already makes this pretty easy, but we've added a handful of utilities for common issues that aren't addressed by the vanilla `read_csv` or `read_sql` methods.

Everything is packaged in a `get_df` method that handles: 
- delimiter type determination for csv files
- determining the appropriate character encoding (utf-8, ascii, etc)
- paginating through a dataset (using `last_retrieved_record` and `limit` keyword args)
- little nuisances like duplicated column names

That makes producing a dataframe as simple as:

```python
from prepy.dataframe import get_df

df = get_df(file_path='path/to/my/file.csv')
```

This method call is the same for any data source. The mechanism used for retrieving the data is inferred based on the keyword arguments passed to the `get_df` function. For example:

```python
# Postgres database
df, finished, last_retrieved_record = get_df(query='SELECT * from users',
            connection_string='postgresql://scott:tiger@localhost:5432/mydatabase')

# Excel file
df, finished, last_retrieved_record = get_df(file_path='path/to/my/file.xls')

# Excel file from URL
df, finished, last_retrieved_record = get_df(url='http://mywebsite.com/file.xls')

# Python array
df, finished, last_retrieved_record = get_df(rows=[{'a':1,'b':2},{'a':3,'b':4}])
```

Most of the time you can ignore the `finished` and `last_retrieved_record` 
variables. However for pagination:

```python
# Step 1, get first 100,000 records
df, finished, last_retrieved_record = get_df(file_path='path/to/big/csv.csv', 
                                                limit=100000)

# Step 2, get next 100,000 records
df2, finished, last_retrieved_record = get_df(file_path='path/to/big/csv.csv', 
                                                limit=100000, 
                                                last_retrieved_record=last_retrieved_record)

# Append df2 to df
df = df.append(df2)
```

This is particularly useful when querying a SQL database, or in situations where 
aggregations can be calculated by following the [split/apply/combine](https://www.jstatsoft.org/article/view/v040i01/v40i01.pdf) paradigm. 


#### Type coercion

In many datasets, columns that look like datetimes or continuous variables are actually strings. Before performing any calculations, even common aggregations, it's helpful to force a column to behave like the type you're expecting. Again, `pandas` has some utility features for accomplishing this, but they don't always work out of the box, which can be a challenge for programs that are inspecting datasets without humans being involved. With that in mind, we wrote some utility functions for just this purpose.

*Cleaning lists*

*Dates*
This function handles dates in any format that can be parsed by `dateutil.parser`, plus Unix/epoch timestamps, and four-digit years (like 2000, 2001, 2002). It'll also handle parsing errors and recognizing when timestamps contain a UTC offset. It returns a `pandas.Series`.

```python
from prepy.clean_list import clean_dates

my_dates = ['1/1/2000','1/2/2003','1/5/2003']

series = clean_dates(my_dates)
```

*Numbers*
This function makes sure that columns of values that look like numbers are typed as floats or `np.nan` values. It returns a `numpy.array`.

```python
from prepy.clean_list import clean_numbers

my_nums = [123, '5555', 'nan', 'None', 0, 100]

nums = clean_numbers(my_nums)
```

*Cleaning values*

You can also clean values one by one (or for an entire series using `pandas.Series.apply`). 

*Numbers*
The `clean_numbers` function above relies on a `number_cleaner` function which you can access directly and use on single values.

```python
from prepy.clean_value import number_cleaner

# will force to a float or np.nan
actually_a_number = number_cleaner(some_random_value)
```

*Strings*
Sometimes character encoding just gets in the way of what you're really trying to accomplish, especially when converting large amounts of text to word vectors, term frequencies, or some other representation that's useful for machine learning. Think of this as the "just work already!" string encoder.

```python
from prepy.clean_value import strip_non_ascii

safe_string = strip_non_ascii(some_gnarly_text)
```

Preferably you'd just encode all your strings as unicode. That too is not always as easy as it seems, so we made a convenience function that handles common problems. 

```python
from prepy.clean_value import string_cleaner

unicode_string = string_cleaner(some_gnarly_text)
```

#### Preparation for machine learning

Last but not least, we've included a utility function that not only ensures that column data is coerced to behave as expected, but also prepares all the columns in a dataframe in the way that's expected by most machine learning algorithms -- more or less a matrix of floats.

This handles things like:
- representing datetime objects as epoch timestamps (instead of datetimes or strings)
- representing ints and floats
- dummy coding categorical variables

The function accepts a `pandas.dataframe` and a dictionary mapping column names to semantic data types. It's assumed the semantic data types were generated by [identipyer](https://github.com/popily/identipyer), or conform to its naming conventions. 

Let's say you had a csv file, `my-dates.csv`, structured as follows:

| Some Number | A Date     | 
|-------------|------------| 
| 1           | 2016-01-01 | 
| 2           | 2016-01-02 | 
| 10          | 2016-01-03 | 
| 20          | 2016-01-04 | 
| 100         | 2016-01-05 | 


```python    
from peny.encoders import encode_df

data_types = {
    'Some Number': ['numeric'],
    'A Date': ['datetime']
}

df = pd.read_csv('my-dates.csv')
df_encoded = encode_df(df,data_types=data_types)
```
