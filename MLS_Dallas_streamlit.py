import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
from PyPDF2 import PdfMerger
from urllib.parse import unquote
import time


# Function to download and merge PDFs
def download_and_merge_pdfs(parcel_numbers, save_path):
    for idx, txroll_cadaccountnumber in enumerate(parcel_numbers, start=1):
        url = f'{txroll_cadaccountnumber}'
        r = requests.get(url)
        try:
            page1 = requests.get(url)
            soup2 = BeautifulSoup(page1.content, 'html.parser')
            accno = soup2.find('span', id='lblTitle')
            if accno is not None:
                accno = accno.text.replace('Appraisal Record for Acct', '').strip()
                accno_path = os.path.join(save_path, accno)
                if not os.path.exists(accno_path):
                    os.mkdir(accno_path)
                st.write(f"Processing account: {accno}")
                all_urls = soup2.find_all('a')

                pdf_files = []
                for url in all_urls:
                    name = url.text
                    try:
                        if 'PDF' in url['href']:
                            pdf_url = ''
                            if 'https' not in url['href']:
                                pdf_url = 'https://www.dallascad.org/' + url['href']
                            else:
                                pdf_url = url['href']

                            pdf_response = requests.get(pdf_url)
                            filename = unquote(name).strip()
                            filepath = os.path.join(accno_path, f"{filename}.pdf")
                            with open(filepath, "wb") as outputStream:
                                outputStream.write(pdf_response.content)
                                pdf_files.append(filepath)
                    except Exception as e:
                        st.write(f"An error occurred while downloading PDF file for {name}: {e}")

                try:
                    merger = PdfMerger()
                    for pdf in pdf_files:
                        merger.append(pdf)
                    with open(os.path.join(accno_path, 'merged.pdf'), 'wb') as output_file:
                        merger.write(output_file)
                    st.write(f"Merged PDF created for account: {accno}")
                except Exception as e:
                    st.write(f"An error occurred while merging PDF files for {accno}: {e}")

        except requests.exceptions.RequestException as e:
            st.write(f"An error occurred while requesting {url}: {e}")

        time.sleep(3)


# Streamlit interface
st.title("PDF Downloader and Merger")

# File uploader for user input
uploaded_file = st.file_uploader("Upload an Excel file", type=["csv", "xlsx"])

# Directory input for saving files
save_path_input = st.text_input("Enter Directory Path to Save Files")

if st.button("Download and Merge PDFs"):
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            parcel_numbers = df['pin'].dropna().astype(str).tolist()

            save_path = save_path_input.strip()
            if parcel_numbers and save_path:
                if os.path.exists(save_path):
                    download_and_merge_pdfs(parcel_numbers, save_path)
                else:
                    st.write("The specified directory does not exist.")
            else:
                st.write("Please enter a valid directory path.")
        except Exception as e:
            st.write(f"An error occurred while reading the file: {e}")
    else:
        st.write("Please upload an Excel file containing the parcel numbers.")
