# Flux: Font Layout UX

Flux *will be* a font layout editor. Currently this is in
a rapid prototyping ("spike") phase; there are many moving
parts and lots will change.

Flux relies heavily on my fontFeatures module for
representation of layout rules. Consequently, that module
is *also* rapidly changing to respond to the needs of this
project. All of the edges are bleeding.

Currently Flux only reads fonts in `.glyphs` format.

If you want to play:

```
pip3 install -r requirements.txt
python3 flux.py
```

## Building an app on OS X

* Ensure that fontFeatures is installed unpacked (i.e. not as an egg)
* Ensure that lxml.etree is built from source and installed
* Clone `py2app` and hack it as per https://github.com/ronaldoussoren/py2app/issues/271#issuecomment-609078700
* python3 setup.py py2app
* rm -rf dist/flux.app/Contents/Resources/lib/python3.8/PyQt5/Qt/lib/Qt{WebEngine,Designer,Quick}*
