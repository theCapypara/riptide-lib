from setuptools import setup, find_packages

setup(
    name='riptide_lib',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    description='TODO',  # TODO
    long_description='TODO - Project will be available starting May/June',  # TODO
    install_requires=[
        'configcrunch >= 0.1',
        'schema >= 0.6',
        'pyyaml >= 5.1',
        'appdirs >= 1.4',
        'janus >= 0.4.0',
        'psutil >= 5.4',
        'GitPython >= 2.1',
        'pywinpty >= 0.5.5; sys_platform == "win32"',
        'python-hosts >= 0.4'
    ],
    # TODO
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
