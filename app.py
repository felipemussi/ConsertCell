import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io

try:
    import plotly.express as px
except ImportError:
    st.error("Erro: A biblioteca 'plotly' não foi instalada. Verifique o seu requirements.txt.")

try:
    import xlsxwriter
except ImportError:
    st.error("Erro: A biblioteca 'xlsxwriter' não foi instalada.")