
from setuptools import setup, find_packages

setup(
    name='SyncMaster',
    version='1.1.0',
    author='MasterCard007',
    author_email='',
    description='A Python-based file synchronization tool',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/MasterCard007/SyncMaster',
    packages=find_packages(),
    install_requires=[
        'humanize',
    ],
    entry_points={
        'console_scripts': [
            'syncmaster=SyncMaster_v9:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
