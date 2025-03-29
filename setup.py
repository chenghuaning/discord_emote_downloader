from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()
setup(
    name="discord_emote_downloader",
    version="1.0.0",
    author="chenghuaning",
    description="Download Discord emotes and stickers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chenghuaning/discord_emote_downloader",
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1',
        'click>=8.0.1',
        'tqdm>=4.60.0',
    ],
    python_requires=">=3.7",
    entry_points={
        'console_scripts': [
            'discord-emote-dl=discord_emote_downloader.main:main'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)