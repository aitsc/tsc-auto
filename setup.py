# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

if os.path.exists('readme.md'):
    long_description = open('readme.md', 'r', encoding='utf8').read()
else:
    long_description = '教程: https://github.com/aitsc/tsc-auto'

setup(
    name='tsc-auto',
    version='0.51',
    description="Auto selector for GPU and CUDA, support the detection of tensorflow or torch",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='tanshicheng',
    license='GPLv3',
    url='https://github.com/aitsc/tsc-auto',
    keywords='tools',
    packages=find_packages(),
    include_package_data=True,  # 包含 .sh 文件
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries',
    ],
    entry_points={  # 打包到bin
        'console_scripts': [
            'ta=tsc_auto.auto:main',  # 包不能有-符号
            'tkill=tsc_auto.kill:main',
            'ressh=tsc_auto.ressh:main',
            'tp=tsc_auto.proxy:main',
        ],
    },
    python_requires='>=3.6',
)
