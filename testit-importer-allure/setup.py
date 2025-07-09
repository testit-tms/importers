from setuptools import setup

VERSION = "1.12.5.post530"

setup(
    name='testit-importer-allure',
    version=VERSION,
    description='Allure report importer for Test IT',
    long_description=open('README.md', "r").read(),
    long_description_content_type="text/markdown",
    url='https://pypi.org/project/testit-importer-allure/',
    author='Integration team',
    author_email='integrations@testit.software',
    license='Apache-2.0',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    package_data={'testit_importer_allure': ['../connection_config.ini']},
    package_dir={'testit_importer_allure': 'src'},
    install_requires=[
        'testit-api-client==6.2.0',
        'xmltodict',
        'minio',
        'pika'
    ],
    entry_points={
        'console_scripts': [
            'testit = testit_importer_allure.__main__:console_main',
            'testit-consumer = testit_importer_allure.__main__:consumer_main'
        ]
    }
)
