# AWS Route 53 URL Updater

## Requirements

*   Python 3
*   boto3 Python Package


## Usage

```Shell
python3 updateDeviceURLs.py --help
usage: updateDeviceURLs.py [-h] [-s] [-o OUTPUT_FILE] [-p] [-f]
                           configfile urlbase

positional arguments:
  configfile            The CSV file that holds the gateway configuration.
  urlbase               URL Base for gateways

optional arguments:
  -h, --help            show this help message and exit
  -s, --send            Send the configuration to AWS Route53
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Output the results to a JSON file.
  -p, --print-output    Print the output file to the console.
  -f, --skip-check      Skip checking for changes accepted
```

## Contributors

*   Patrick McDonagh @patrickjmcd - Owner
