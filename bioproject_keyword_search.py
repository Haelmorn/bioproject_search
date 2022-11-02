import csv

import requests as requests
import tqdm as tqdm
from Bio import Entrez
import argparse

KEYWORDS = [
    "Faecal Microbiota Transplantation",
    "Fecal Microbiota Transplantation",
    "Fecal Microbiota Transplant",
    "Faecal Microbiota Transplant",
    "Fecal Microbiota",
    "Faecal Microbiota",
    "Fecal Microbiome",
    "Faecal Microbiome",
    "Faecal",
    "Fecal",
    "FMT",
]


def search_in_bioproject(keywords: list[str], from_date: str, to_date: str) -> list[str]:
    """
    Search in BioProject
    :param keywords: Keywords to search
    :param from_date: search from data
    :param to_date: search to date
    :return: list of BioProject IDs
    """
    results_list = []

    for keyword in keywords:
        keyword_phrase = "+".join(keyword.split(" "))
        url = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=BioProject&term=({keyword_phrase})"
                + f'+AND+("{from_date}"[Registration%20Date]%20:%20%22{to_date}%22[Registration%20Date])'
                + "&RetMax=999999&retmode=json"
        )

        response = requests.get(url)
        if response.status_code == 200:
            # decode the response contents
            response_json = response.json()
            # Get the list of ids from the response
            results_list.extend(response_json["esearchresult"]["idlist"])
            print(f"Found {len(response_json['esearchresult']['idlist'])} results for {keyword}")
        else:
            print(f"Error while fetching results: {response.status_code}")
            print("Exiting...")
            exit(1)

    # Remove duplicates
    results_list = list(set(results_list))
    print(f"Found {len(results_list)} unique BioProjects")

    return results_list


def check_proper_entrez_response(cleaned_result: list[str]) -> bool:
    """
    Check if an entrez result if properly formatted
    :param cleaned_result: a cleaned entrez response
    :return: Trueif properly formatted, False
    """
    # There must be an entry that starts with "1. " and an entry that starts with "BioProject Accession: "
    if not any([result.startswith("1. ") for result in cleaned_result]):
        return False
    if not any([result.startswith("BioProject Accession: ") for result in cleaned_result]):
        return False

    return True


def convert_ids_to_accessions(bioproject_ids: list[str], email: str) -> (dict[str, str], dict[str, str]):
    """
    Convert BioProject IDs to BioProject Accessions using Entrez
    :param bioproject_ids: list of BioProject IDs
    :return: list of BioProject Accessions, list of samples which failed conversion
    """
    Entrez.email = email

    bioproject_accessions = {}
    failed_bioprojects = {}

    for bioproject_id in tqdm.tqdm(bioproject_ids):
        # Convert ID to Accessions
        # Try 3 times, then list as failed
        for i in range(3):
            try:
                handle = Entrez.efetch(db="bioproject", id=bioproject_id, rettype="acc", retmode="text")
                entrez_result = handle.readlines()
                handle.close()
                break
            except Exception as e:
                tqdm.tqdm.write(f"Error while fetching {bioproject_id}: {e}")
                tqdm.tqdm.write("Retrying...")
                continue
        else:
            tqdm.tqdm.write(f"Failed to fetch {bioproject_id} after 3 tries")
            failed_bioprojects[bioproject_id] = "Failed to fetch"
            break

        # Parse and append the results
        cleaned_result = [result.strip() for result in entrez_result if result != "\n"]

        # Check if the cleaned result if properly formatted
        if check_proper_entrez_response(cleaned_result):
            # Response is valid, parse and save
            # Find abstract - entry that starts with "1. "
            abstract = [result for result in cleaned_result if result.startswith("1. ")][0]

            # Find bioproject accession - entry that starts with "BioProject Accession: "
            bioproject_accession = [result for result in cleaned_result if result.startswith("BioProject Accession: ")][0]
            bioproject_accession = bioproject_accession.split(": ")[1]
            bioproject_accessions[bioproject_accession] = abstract
        else:
            failed_bioprojects[bioproject_id] = str(cleaned_result)

    return bioproject_accessions, failed_bioprojects


def main():
    parser = argparse.ArgumentParser(description='Search in PubMed')
    parser.add_argument('-e', '--email', help='Email address', required=True)
    parser.add_argument('-k', '--keywords', help='Keywords to search', required=False, default=KEYWORDS)
    parser.add_argument('-m', '--max_results', help='Max results', required=False, default=10000000)
    parser.add_argument('-f', '--from_date', help='From date (YYYY/MM/DD)', required=True)
    parser.add_argument('-t', '--to_date', help='To date (YYYY/MM/DD)', required=True)
    parser.add_argument('-o', '--output', help="Path to output file", required=False,
                        default="output-from_date-to_date.csv")
    parser.add_argument('--failed', help="Path to file with failed IDs", required=False,
                        default="failed-from_date-to_date.csv")
    args = parser.parse_args()

    print("Searching in BioProject...")
    bioproject_ids = search_in_bioproject(args.keywords, args.from_date, args.to_date)

    # Convert BioProject IDs to BioProject Accessions
    print("Converting IDs to Accessions...")
    bioproject_accessions, failed_bioprojects = convert_ids_to_accessions(bioproject_ids, args.email)

    print(f"Successfully converted {len(bioproject_accessions)} studies")
    print(f"Failed to convert {len(failed_bioprojects)} IDs")

    print("Saving results...")

    output_file = args.output
    if output_file == "output-from_date-to_date.csv":
        output_file = f"output-{args.from_date.replace('/', '-')}-{args.to_date.replace('/', '-')}.csv"

    with open(output_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["study_id", "desc", "url"])
        for key, value in bioproject_accessions.items():
            url = f"https://www.ncbi.nlm.nih.gov/bioproject/{key}"
            writer.writerow([key, value, url])

    failed_file = args.failed
    if failed_file == "failed-from_date-to_date.csv":
        failed_file = f"failed-{args.from_date.replace('/', '-')}-{args.to_date.replace('/', '-')}.csv"

    if len(failed_bioprojects) > 0:
        with open(failed_file, 'w') as f:
            writer = csv.writer(f)
            for key, value in failed_bioprojects.items():
                writer.writerow([key, value])


if __name__ == '__main__':
    main()
