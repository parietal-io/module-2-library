from setuptools import find_packages, setup

import versioneer

setup(name='module-2-package',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Create Python packages from single modules',
      packages=['m2l'],
      package_data={'m2l':['templates/*/*']},
      install_requires=['click', 'jinja2', 'versioneer'],
      tests_require='pytest',
      entry_points={
        'console_scripts': [
            'm2l = m2l:cli',
        ],
      },
      zip_safe=False,
      include_package_data=True)
