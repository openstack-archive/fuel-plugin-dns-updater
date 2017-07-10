import setuptools

# all other params will be taken from setup.cfg
setuptools.setup(packages=setuptools.find_packages(),
                 setup_requires=['pbr>=1.8'], pbr=True)
