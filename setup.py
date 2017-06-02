from setuptools import setup
import kamma

long_description = ('kamma is a very simplified task file queue that '
                    'persist jobs and its input data and it has a worker that '
                    'process all pending jobs. Not recommended for high performance applications.')

setup(name='kamma',
      version=kamma.__version__,
      description='kamma is a very simplified Task File Queue',
      keywords=['kamma', 'file queue', 'task', 'job', 'task queue'],
      long_description=open('README.rst').read(),
      author='Marcel Janer Font',
      author_email='marceljanerfont@gmail.com',
      maintainer='Marcel Janer Font',
      maintainer_email='marceljanerfont@gmail.com',
      url='https://github.com/marceljanerfont/kamma',
      packages=['kamma'],
      license='MIT',
      package_data={'': ['LICENSE', 'README.rst']},
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: Jython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Topic :: Communications',
          'Topic :: Internet',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Networking'],
      zip_safe=True)
