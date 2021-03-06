from setuptools import setup, find_packages
import sys, os

from ckanext.hrifi import __version__

setup(name='ckanext-hrifi',
      version=__version__,
      description="CKAN Customizations for the Helsinki Region Infoshare",
      long_description="",
      classifiers=[], 
      keywords='ckan helsinki opendata region',
      author='Open Knowledge Foundation',
      author_email='info@okfn.org',
      url='http://www.okfn.org',
      license='GPL v3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      namespace_packages=['ckanext', 'ckanext.hrifi'],
      zip_safe=False,
      message_extractors = {
            'ckanext/hrifi': [
                ('**.py', 'python', None),
                ('templates/**.html', 'ckan', None),
                ('public/**', 'ignore', None)
                ],
            '../ckanext-multiedit/ckanext/multiedit': [
                ('templates/**.html', 'ckan', None),
                ('**.py', 'python', None),
                ('public/**', 'ignore', None)
                ],
            '../ckanext-comments/ckanext/comments': [
                ('templates/**.html', 'ckan', None),
                ('**.py', 'python', None),
                ('public/**', 'ignore', None)
                ],
            },
      install_requires=[
          # -*- Extra requirements: -*-
          'ckanclient>=0.9'
      ],
      entry_points="""
      # -*- Entry points: -*-           
      
      [ckan.plugins]
      hrifi=ckanext.hrifi.plugin:Hrifi
      hri_organization=ckanext.hrifi.hri_organization_form:HriOrganizationForm
      hri_wordpress_auth = ckanext.hrifi.plugin:WordPressAuthPlugin
      
      """
      )
