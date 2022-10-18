from setuptools import setup

setup(
    name='testit-importer-junit',
    version='1.0.1',
    description='Junit report importer for Test IT',
    long_description=open('README.md', "r").read(),
    long_description_content_type="text/markdown",
    url='https://pypi.org/project/testit-importer-junit/',
    author='Dmitry Gridnev',
    author_email='dmitry.gridnev@testit.software',
    license='Apache-2.0',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=['testit_importer_junit'],
    package_data={'testit_importer_junit': ['../connection_config.ini']},
    package_dir={'testit_importer_junit': 'src'},
    install_requires=['testit-api-client>=1.1,<2'],
    entry_points={
        'console_scripts': [
            'testit-junit = testit_importer_junit.__main__:console_main'
        ]
    }
)
