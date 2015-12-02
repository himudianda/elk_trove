from setuptools import setup

setup(
    name='DBaaS',
    version='1.0',
    packages=['app'],
    include_package_data=True,
    install_requires=[
    ],
    entry_points='''
        [console_scripts]
        run=app:app
    ''',
)
