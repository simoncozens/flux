"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['flux.py']
DATA_FILES = []
OPTIONS = {
'iconfile': 'flux.icns',
'packages': ['ometa', 'terml', 'fontFeatures'],
'excludes': ['PyQt5.QtDesigner', 'PyQt5.QtNetwork', 'PyQt5.QtOpenGL', 'PyQt5.QtScript', 'PyQt5.QtSql', 'PyQt5.QtTest', 'PyQt5.QtWebKit', 'PyQt5.QtXml', 'PyQt5.phonon', 'PyQt5.QtWebEngine'],
'plist': {
        'CFBundleIdentifier': 'uk.co.corvelsoftware.Flux',
        'UTExportedTypeDeclarations': [{
            'UTTypeIdentifier': 'uk.co.corvelsoftware.Flux',
            'UTTypeTagSpecification': {
                'public.filename-extension': [ 'fluxml' ],
            },
            'UTTypeDescription': 'Flux Project File',
            'UTTypeConformsTo': [ 'public.xml' ]
        }]
    }
}

setup(
    app=APP,
    name="Flux",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
