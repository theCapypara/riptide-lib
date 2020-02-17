from setuptools import setup, find_packages

# README read-in
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()
# END README read-in

setup(
    name='riptide-lib',
    version='0.5.2',
    packages=find_packages(),
    package_data={'riptide': ['assets/*']},
    description='Tool to manage development environments for web applications using containers - Library Package',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/Parakoopa/riptide-lib/',
    install_requires=[
        # TEMPORARY, see #2:
        'idna <= 2.8',
        'configcrunch >= 0.3.3',
        'schema >= 0.6',
        'pyyaml >= 5.1',
        'appdirs >= 1.4',
        'janus >= 0.4.0',
        'psutil >= 5.6',
        'GitPython >= 3.0',
        'pywinpty >= 0.5.5; sys_platform == "win32"',
        'python-hosts >= 0.4'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
