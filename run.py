import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import pytz

## Importing functions ---------------------------------------------------------------------##

from scrape_Gilman import *
from scrape_Elis import *
from scrape_Stork import *
from combine import *
from enrich import *
from cache import *
from run_Streamlit import run_Streamlit

CACHE_FILE = "cached_df.csv"
TIMESTAMP_FILE = "cached_df_timestamp.txt"
MAX_AGE_HOURS = 24


## Run Streamlit  ---------------------------------------------------------------------##
run_Streamlit()