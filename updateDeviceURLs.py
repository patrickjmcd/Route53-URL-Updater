#!/usr/bin/python

"""Generate record set for AWS Route53."""
import csv
import json
import boto3
import argparse
from time import sleep


def create_record_set(filename, url_base):
    """Create an AWS Route53 Record Set from a CSV File."""
    reader = csv.DictReader(open(filename, 'r'))

    all_changes = {
        "Changes": [],
        "Comment": "Upserting all device aliases"
    }
    for x in reader:
        if x['url'] and x['ipaddress']:
            change = {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "ResourceRecords": [
                        {
                            "Value": x['ipaddress']
                        },
                    ],
                    "Type": "A",
                    "Name": x['url'] + url_base,
                    "TTL": 300
                },
            }
            all_changes['Changes'].append(change)

    return all_changes


def find_hostedzoneid(urlbase):
    """Find the Hosted Zone ID for a given URL base."""
    if urlbase[0] == '.':
        urlbase = urlbase[1:]
    if urlbase[-1] != '.':
        urlbase = urlbase + '.'
    client = boto3.client('route53')
    get_result = client.list_hosted_zones()
    for z in get_result['HostedZones']:
        if z['Name'] == urlbase:
            return z['Id'].split('/')[2]  # Id is "/hostedzone/<Id>"
    raise KeyError("No Hosted Zone Found")

def send_recordset_to_aws(recordset, hostedzoneid):
    """Send the specified record set to AWS Route53."""
    client = boto3.client('route53')
    result = client.change_resource_record_sets(
        HostedZoneId=hostedzoneid,
        ChangeBatch=recordset)
    return result

def check_recordset_in_aws(changeid):
    """Checks the status of the record set in AWS Route53."""
    """Returns either PENDING or INSYNC"""
    client = boto3.client('route53')
    result = client.get_change(Id=changeid)
    return result['ChangeInfo']['Status']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('configfile', help="The CSV file that holds the gateway configuration.")
    parser.add_argument('urlbase', help="URL Base for gateways")
    parser.add_argument('-s', '--send', action='store_true', help="Send the configuration to AWS Route53")
    parser.add_argument('-o', '--output-file', default=None, help="Output the results to a JSON file.")
    parser.add_argument('-p', '--print-output', action='store_true', help="Print the output file to the console.")
    parser.add_argument('-f', '--skip-check', action='store_true', help="Skip checking for changes accepted")

    args = parser.parse_args()
    send_to_aws = args.send
    config_file = args.configfile
    output_file = args.output_file
    # hosted_zone_id = args.hosted_zone_id
    print_out = args.print_output
    url_base = args.urlbase

    if url_base[0] != ".":
        url_base = "." + url_base

    record_set = create_record_set(config_file, url_base)

    hosted_zone_id = find_hostedzoneid(url_base)

    if output_file:
        with open(output_file, 'wb') as jsonfile:
            json.dump(record_set, jsonfile, indent=4)

    if print_out:
        print(json.dumps(record_set, indent=4))

    if send_to_aws:
        send_result = send_recordset_to_aws(record_set, hosted_zone_id)
        change_id = send_result['ChangeInfo']['Id']
        print("Changes are currently {}".format(send_result['ChangeInfo']['Status']))
        seconds_to_wait_for_insync = 60
        seconds_waited = 0
        synced = False
        while seconds_waited < seconds_to_wait_for_insync:
            if check_recordset_in_aws(change_id) == 'INSYNC':
                synced = True
                print(" BOOM!\nChanges are INSYNC!!!")
                break
            else:
                print('.', end='', flush=True)
            seconds_waited += 1
            sleep(1)
        if not synced:
            print(" Yikes!\nCouldn't get INSYNC within {} seconds...".format(seconds_to_wait_for_insync))
        # print(json.dumps(send_result, indent=4, default=str))
