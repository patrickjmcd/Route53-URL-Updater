from setuptools import setup

setup(
    name='Route53-URL-Updater',
    version='0.1',
    py_modules=['updateDeviceURLs'],
    install_requires=[
        'Click',
        "boto3"
    ],
    entry_points='''
        [console_scripts]
        route53_upd=updateDeviceURLs:cli
    ''',
)