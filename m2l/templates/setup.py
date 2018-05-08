from setuptools import find_packages, setup

import versioneer

setup(name='{{ pkg.pkgname }}',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='{{ pkg.description }}',
      packages=['{{ pkg.pkgimp }}'],
      {%- if pkg.requires %}
      install_requires={{ pkg.requires }},
      {%- endif %}
      tests_require='pytest',
      {%- if pkg.entrypoint %}
      entry_points={
        'console_scripts': [
            '{{pkg.pkgimp}} = {{pkg.pkgimp}}:{{pkg.entrypoint}}',
        ],
      },
      {%- endif %}
      zip_safe=False,
      include_package_data=True)
