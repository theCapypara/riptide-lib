__version__ = '0.7.0'
from setuptools import setup, find_packages

# README read-in
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()
# END README read-in

setup(
    name='riptide-lib',
    version=__version__,
    packages=find_packages(),
    package_data={'riptide': ['assets/*']},
    description='Tool to manage development environments for web applications using containers - Library Package',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/Parakoopa/riptide-lib/',
    install_requires=[
        'configcrunch >= 1.0.0',
        'schema >= 0.7',
        'pyyaml >= 5.4',
        'appdirs >= 1.4',
        'janus >= 0.7',
        'psutil >= 5.8',
        'GitPython >= 3.1',
        'pywinpty >= 0.5.5; sys_platform == "win32"',
        'python-hosts >= 0.4',
        'python-dotenv >= 0.19.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
