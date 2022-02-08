import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import csv
import time
from datetime import datetime

'''
This script makes API calls to the Proofpoint Isolation logging API and writes the output to CSV.
The page limit maximum is 10,000 records and the API only retrieves results for the last 30 days.
Reporting data is updated every 30 minutes.
'''


def sleep(secs):
    print(str(datetime.now()) + f" -- Waiting...Sleeping for {secs} seconds!")


def make_api_call(url, head):
    try:
        api_resp = requests.request("GET", url, headers=head, verify=False)
        api_resp_json = api_resp.json()
    except Exception as e:
        print("Error making API call! \n" + str(e))
        api_resp_json = {}
    return api_resp_json


def write_to_csv(logs, csv_writer):
    counter = 0
    for log in logs:
        csv_writer.writerow(log)
        counter = counter + 1
    print(str(counter) + " Logs written to CSV")


def main():

    #Disable Insecure Request Warning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    #Set Start Time for Export file name
    timestr = time.strftime("%Y%m%d-%H%M%S")
    print(timestr + " -- Starting Isolation API script now!")

    #Set base API URL
    log_api = "https://urlisolation.com/api/reporting/usage-data"

    #Define variables statically, comment out next 4 lines to be prompted for information.
    #api_key = ""
    #start_date = "2022-01-20"
    #end_date = "2022-02-07"
    page_size = "10000"

    #Define variables dynamically, comment out next 4 lines to define statically.
    api_key = input("Enter Isolation API Key: ")
    start_date = input("Enter Log Start Date (yyyy-mm-dd): ")
    end_date = input("Enter Log End Date (yyyy-mm-dd): ")
    #page_size = input("Enter page size: ")

    #Create base URL for requests
    base_url = log_api + "?key=" + api_key + "&pageSize=" + page_size + "&from=" + start_date + "&to=" + end_date
    print(base_url)

    #Set request header(s)
    headers = {'Accept': "*/*"}

    #Make initial API Request
    output = make_api_call(base_url, headers)
    status = output['status']
    job_id = output['jobId']
    api_call_url = base_url + "&jobId=" + job_id
    print(job_id)
    print(status)

    #Check if status is completed, if not sleep then check again.
    while not (status == "COMPLETED"):
        sleep(60)
        output = make_api_call(api_call_url, headers)
        status = output['status']
        print(output['jobId'])
        print(status)

    #Define variables
    if 'pageToken' in output:
        page_token = output['pageToken']
    else:
        page_token = ''
        print("No Page Token")
    if 'data' in output:
        log_data = output['data']
    else:
        log_data = ''
        print("No Data!")
    if 'total' in output:
        tot_logs = output['total']
        print(f"Total Records: {tot_logs}")
    else:
        print("Total not found!")

    #Create output file name string
    out_file = 'Isolation_Logs_' + timestr + ".csv"

    #Open CSV output file and write initial data
    with open(out_file, 'a', newline="") as csvfile:
        fieldnames = ["userId", "userName", "url", "date", "region", "zone",
                      "classification", "disposition", "categories"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        write_to_csv(log_data, writer)
        #sleep(10)

        #Loop over pages and write logs until pageToken isn't found
        while "pageToken" in output:
            print(f"PageToken: {page_token}")
            page_url = api_call_url + "&pageToken=" + page_token
            output = make_api_call(page_url, headers)
            write_to_csv(output['data'], writer)
            if "pageToken" in output:
                page_token = output['pageToken']
            else:
                print("Page Loop Complete")


if __name__ == '__main__':
    main()

