# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

LONGDOC = """
Auto selector for NVIDIA GPUs and CUDA

Support detection for tensorflow or torch
"""

setup(
    name='tsc-auto',
    version='0.6',
    description="tanshicheng's tools",
    long_description=LONGDOC,
    author='tanshicheng',
    license='GPLv3',
    url='https://github.com/aitsc',
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
        'console_scripts': ['ta=tsc_auto.auto:main'],  # 包不能有-
    },
    python_requires='>=3.6',
)
