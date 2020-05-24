from distutils.core import setup

setup(
    name='emma',
    version='0.3',
    packages=['emma',],
    license='MIT',
    long_description=open('README.md').read(),
    install_requires=['requests==2.22.0'], 
)