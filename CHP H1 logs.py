# Databricks notebook source
# MAGIC %md
# MAGIC # Azure settings

# COMMAND ----------

spark.conf.set(
    "fs.azure.account.key.devatgdsgovst.dfs.core.usgovcloudapi.net",
    dbutils.secrets.get(scope="atg-ds-gov-databricks", key="atgdsgovst-key"))

# COMMAND ----------

# MAGIC %md
# MAGIC # Access data

# COMMAND ----------

import pandas as pd 
import re

# Set the display options to show all rows and columns
pd.set_option('display.max_rows', 20)
pd.set_option('display.max_columns', None)

# Set the figure size - handy for larger output
from matplotlib import pyplot as plt
plt.rcParams["figure.figsize"] = [10, 6]
# Set up with a higher resolution screen (useful on Mac)
%config InlineBackend.figure_format = 'retina'

# COMMAND ----------

df = spark.read.text("abfss://test@devatgdsgovst.dfs.core.usgovcloudapi.net/CHP_H1/UnitId_CobanH1_20210707 - Copy.log")
display(df)
df = df.toPandas()

# COMMAND ----------

df.count()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC Other data we have right now is of another form

# COMMAND ----------

test = spark.read.text("abfss://test@devatgdsgovst.dfs.core.usgovcloudapi.net/Logs/InCar/InCar/22321949/22321949_20230515173532.log")
display(test)


# COMMAND ----------

test = spark.read.text("abfss://test@devatgdsgovst.dfs.core.usgovcloudapi.net/Logs/InCar/InCar/22321949/22321949_20230523114302.log")
display(test)

# COMMAND ----------

test = spark.read.text("abfss://test@devatgdsgovst.dfs.core.usgovcloudapi.net/Logs/InCar/InCar/57004449/57004449_20210623095757.log")
display(test)

# COMMAND ----------

# MAGIC %md
# MAGIC This test dataframe has 4633 record entries in it, I am going to use this as a test to format the data and create a dashboard through the code.

# COMMAND ----------

test = spark.read.text("abfss://test@devatgdsgovst.dfs.core.usgovcloudapi.net/Logs/InCar/InCar/CARO/CARO_H1US_CobanH1_20221123_1669239216.log")
display(test)

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC # Data Formatting

# COMMAND ----------

test = test.toPandas()
test.head()

# COMMAND ----------

test['value'][10]

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC We are splitting the column into different types.

# COMMAND ----------

import re

# Define a regular expression pattern to match the most common log line format
pattern1 = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+-\d{2}:\d{2}) \S+ \S+ (\w+)\[\d+\]: (\S+)\s*: \S+ : (.*$)"

# Use str.extract() to split the 'message' column into new columns
test[['time', 'manager', 'log_type', 'log_message']] = test['value'].str.extract(pattern1)
test

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC In the three last rows, there are three different log types there, but with the same log message. Would this be a sign that they actually need to change the display settings?

# COMMAND ----------

selected_rows = test.iloc[4620:4633]
selected_rows

# COMMAND ----------

import pandas as pd

# Sample DataFrame
data = {'A': [1, 2, 3, 1, 4, 2, 5],
        'B': ['apple', 'orange', 'banana', 'apple', 'grape', 'kiwi', 'mango']}

df = pd.DataFrame(data)

# Identify rows where values in column A are duplicated
duplicated_rows = df[df.duplicated(subset=['A'], keep=False)]

# Display the result
print(duplicated_rows)


# COMMAND ----------

data

# COMMAND ----------

a = test[['log_type', 'log_message']]
b = a[a.duplicated(subset=['log_message'], keep=False)]
b.to_dict()

# COMMAND ----------

test.iloc[[1335, 1336, 1337,]]
test[test['log_message'] == "RUNNING State"]['log_type'].unique()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC This cell was used to further distinguish the rows which didn't get splitted in the first go. We need to create new regex patterns to adapt to the change in the log lines. But it's also a good sign that these lines are showing a different pattern with some alarming (recording) issues. 
# MAGIC
# MAGIC Given the number of the lines are not too many, it could be a good idea to just filter out all of them and carry out further inspections.

# COMMAND ----------

# further = test[test['time'].isna()]

# # Record the message for the rest log lines (there are only three groups filled now)
# pattern2 = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+-\d{2}:\d{2}) \S+ \S+ (\w+)\[\d+\]:(.*)"

# further[['time', 'manager', 'log_message']] = further['value'].str.extract(pattern2)

# COMMAND ----------

# Only 15 lines in a total 4633 rows
test['time'].isnull().sum()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC # Basic stats

# COMMAND ----------

test.head()

# COMMAND ----------

print(test['time'][0], test['time'].iloc[-1])

# COMMAND ----------

p1 = test["log_type"].value_counts(dropna=False)

# Calculate percentages
percentages = p1 / p1.sum() * 100

# Create bar chart
ax = percentages.plot(kind='bar', rot=45)

# Add percentage labels on top of each bar
for i, percentage in enumerate(percentages):
    ax.text(i, percentage + 1, f'{percentage:.1f}%', ha='center')

plt.xlabel("Log Type")
plt.ylabel("Percentage")
plt.title("Distribution of Log Types")
plt.show()

# COMMAND ----------

# this would return a series
result = test['manager'].value_counts(dropna=False)
result.plot(kind="bar")
plt.xticks(rotation=30, horizontalalignment="right")
plt.xlabel("Manager Type")
plt.ylabel("Count")

# Add values on top of the bars
for i, value in enumerate(result):
    plt.text(i, value + 0.1, str(value), ha='center', va='bottom')

plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC we want to have a plot of how many errors/info/warnings in each manager

# COMMAND ----------

# MAGIC %md
# MAGIC # Data Cleaning & Filtering

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC I have two options to filter the lines with "ERROR" and put them into a list, but the second way of iterating the rows seem faster than the first one

# COMMAND ----------

import re
# Regular expression pattern to match lines containing "ERROR"
error_pattern = re.compile(r".*ERROR.*", re.IGNORECASE)
# List to store lines containing errors from all files
error_lines = []

# Way 1: filter the dataframe with rows containing "error"
# Use str.contains() with regex to filter the DataFrame
error_df = df[df['value'].str.contains(error_pattern, regex=True)]

error_df
# # Convert the 'Column1' of the DataFrame to a list
# error_list = error_df['value'].tolist()


# COMMAND ----------

# MAGIC %md
# MAGIC Split the values in the error_df into different columns

# COMMAND ----------

# Split the 'Column1' into multiple columns based on spaces
split_columns = error_df['value'].str.split("ERROR", expand=True)

# Rename the new columns (optional)
split_columns.columns = ['Day', 'Message']

# Extract date and time as separate columns
split_columns['Date'] = split_columns['Day'].str[:10]
split_columns['Time'] = split_columns['Day'].str[11:23]

# Delete rows containing the keyword "main" as they contain useless info
split_columns = split_columns[~split_columns['Message'].str.contains('main', case=False)]

# Reset the index of the DataFrame
split_columns = split_columns.reset_index(drop=True)

# COMMAND ----------

split_columns

# COMMAND ----------

import re
# Regular expression pattern to match lines containing "ERROR"
error_pattern = re.compile(r".*ERROR.*", re.IGNORECASE)
# List to store lines containing errors from all files
error_lines = []

# Way 2 
# Iterate through the column values
for index, row in df.iterrows():
    value = row['value']
    if re.match(error_pattern, value): 
        error_lines.append(value)

# COMMAND ----------

error_lines

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC A way to sort out log messages based on key words:
# MAGIC
# MAGIC (Example of usage would be to filter out the error messages)

# COMMAND ----------

import re

def sort_by_keyword(df, keyword, into_list=False):
    """
    This function takes a dataframe and return the rows that contain certain keywords.
    
    Parameters:
    --------------------------------------
    df: the log data frame
    keyword: str, the word to search
    into_list: bol, True if you want the results to be dumped into a list

    Returns:
    --------------------------------------
    sorted_df: rows containing the search words
    sorted_list

    Example:
    --------------------------------------
    sort_by_keyword(df, "cfg")
    """
    # Regular expression pattern to match lines containing "ERROR"
    pattern = re.compile(".*" + keyword + ".*", re.IGNORECASE)

    # Use str.contains() with regex to filter the DataFrame
    sorted_df = df[df['value'].str.contains(pattern, regex=True)]

    if into_list == True:
        sorted_list = sorted_df['value'].tolist()
    else:
        sorted_list=[]

    return sorted_df, sorted_list

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC Notice this function can be further modified to fit the purpose of splitting the information into columns (including date, time, and messages)

# COMMAND ----------

a, b = sort_by_keyword(df, "error", into_list=True)

# COMMAND ----------

def sort_error(error_list):
    """   
    Given a list of error, put them into different brackets.
    "beginner_error",(errors showing in the beginning), 
    'camera', 'connection', 'download', 'USB' (needs attention for low USB storage),
    'ignore' (errors that's not giving much information).
    
    Parameters:
    -----------------------
    error_list: list
    
    Returns:
    -----------------------
    error_dict: dictionary of the errors sorted into 5 categories.
    
    """
    # interested = []
    # with open(file_name) as f:
    #     f = f.readlines()
    # for line in f:
    #     if 'Error' in line or 'error' in line or 'ERROR' in line:
    #         interested.append(line)
            
    error_dict = defaultdict(list)
    for error in interested:
        # get the main error message
        temp = "".join(error.split(":")[5:])
        
        # break erros into brackets:
        ## 1. errors that always appear in the beginning
        if 'main()' in temp or 'CFG ID' in temp:
            error_dict['beginner_error'].append(temp)
            continue
        ## 2. camera issues
        if any(re.findall(r'camera', temp, re.IGNORECASE)):
            error_dict['camera'].append(temp)
            continue
        ## 3. connection issues
        if any(re.findall(r'Curl|connection|HTTP|ntp|connect', temp, re.IGNORECASE)):
            error_dict['connection'].append(temp)
            continue
        ## 4. downloading issues
        if any(re.findall(r'download', temp, re.IGNORECASE)):
            error_dict['download'].append(temp)
            continue
        ## 5. USB issues (considered important)
        if any(re.findall(r'USB', temp, re.IGNORECASE)):
            error_dict['USB'].append(temp)
            continue
        ## 6. some errors that does not require attention (we will get more into this category)
        if any(re.findall(r'printlevel', temp, re.IGNORECASE)):
            error_dict['ignore'].append(temp)
            continue     
        ## 7. all ther miscellaneous issues (we are looking at them to sort them better)
        error_dict['else'].append(temp)

    return error_dict

file_name = 'C:/Users/Xinyi.Li/OneDrive - Safe Fleet/Desktop/Data_Science/CHP_log/sample_log/more_logs/3011536309_CobanH1_20230113_1673623658_capacity0.log'
sort_error(file_name)

# COMMAND ----------


