from setuptools import setup, find_packages

setup(
    name="adk_project",
    version="0.1.0",
    packages=find_packages(),
    author="Factos Agents",
    description="An agent that fact-checks claims using a sequence of specialized agents.",
    install_requires=[
        # Dependencies are now managed in requirements.txt
        # to simplify deployment.
    ],
    entry_points={
        'console_scripts': [],
    },
) 