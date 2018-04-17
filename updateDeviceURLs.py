#! /usr/bin/env python3

"""Generate record set for AWS Route53."""
import csv
import json
import boto3
from time import sleep
import click


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

@click.group()
def cli():
    pass


@click.command()
@click.argument("configfile", type=click.Path(exists=True))
@click.argument("urlbase")
@click.option("-s", "--send", is_flag=True, help="Send the configuration to AWS Route53")
@click.option('-o', '--output-file', default=None, help="Output the results to a JSON file.")
@click.option('-p', '--print-output', is_flag=True, help="Print the output file to the console.")
@click.option('-f', '--skip-check', is_flag=True, help="Skip checking for changes accepted")
def update_records(configfile, urlbase, send, output_file, print_output, skip_check):
    """Update the configuration in route 53."""
    if urlbase[0] != ".":
        urlbase = "." + urlbase

    record_set = create_record_set(configfile, urlbase)

    hosted_zone_id = find_hostedzoneid(urlbase)

    if output_file:
        with open(output_file, 'wb') as jsonfile:
            json.dump(record_set, jsonfile, indent=4)

    if print_output:
         click.echo(json.dumps(record_set, indent=4))

    if send:
        send_result = send_recordset_to_aws(record_set, hosted_zone_id)
        change_id = send_result['ChangeInfo']['Id']
        click.echo("Changes are currently {}".format(send_result['ChangeInfo']['Status']))
        seconds_to_wait_for_insync = 60
        seconds_waited = 0
        synced = False
        while seconds_waited < seconds_to_wait_for_insync:
            if check_recordset_in_aws(change_id) == 'INSYNC':
                synced = True
                click.echo(" BOOM!\nChanges are INSYNC!!!")
                break
            else:
                print('.', end='', flush=True)
            seconds_waited += 1
            sleep(1)
        if not synced:
            click.echo(" Yikes!\nCouldn't get INSYNC within {} seconds...".format(seconds_to_wait_for_insync))
        # print(json.dumps(send_result, indent=4, default=str))

@click.command()
@click.argument("configfile", type=click.Path(exists=True))
@click.argument("urlbase")
def show_config(configfile, urlbase):
    """Read the CSV configuration file and parse into an object."""
    if urlbase[0] != ".":
        urlbase = "." + urlbase

    with open(configfile, "r") as cfg:
        reader = csv.DictReader(cfg)
        companies = {}
        max_length = 0
        for c in reader:
            if not c["Company"] in companies.keys():
                companies[c["Company"]] = []
            companies[c["Company"]].append({"location": c["Gateway"], "URL": c["url"]})
            if len(c["Gateway"]) > max_length:
                max_length = len(c["Gateway"])
        for comp in companies.keys():
            click.echo("== {}".format(comp))
            for device in companies[comp]:
                spaces = " " * (max_length - len(device["location"]))
                click.echo("  \u21B3 {}{} \u21B9  {}{}".format(device["location"], spaces, device["URL"], urlbase))
            click.echo()

cli.add_command(update_records)
cli.add_command(show_config)

if __name__ == '__main__':
    cli()