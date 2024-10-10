# Libraries

## app
This script is the base for creating new CLI applications.

It exposes some nice features such as:
- Script banner (with application name, version, author and *quote*)
- Simple console logger
- User actions
- Properties usage (see [Properties](#properties))

### Usage
Simply extend the `App` class.

```python
import madhac.app as mapp

class TemplateApp(mapp.App):
    def main(self):
        self.logger.info('Hello world!')

if __name__ == "__main__":
    app = TemplateApp()
    app.start()
```

The most useful feature is the `UserAction` decorator.
This will allow you to define methods that can be called by the CLI directly.

For example:
```python
import madhac.app as mapp

class TemplateApp(mapp.App):
    @mapp.UserAction
    def test_me(self):
        self.logger.info('Yay!')

if __name__ == "__main__":
    app = TemplateApp()
    app.start()
```

And when you execute this script, you can use the method name to use it:
```bash
python script.py test_me
```

The App class also exposes the argparse parser to be used for adding options:
```python
import madhac.app as mapp

class TemplateApp(mapp.App):
    def main(self):
        self.logger.info('Hello world!')

if __name__ == "__main__":
    app = TemplateApp()
    parser = app.get_parser()
    parser.add_argument(
        'input',
        help='Input file',
    )
    app.start()
```

A global `properties` variable is also exposed by the madhac library:
```python
mapp.properties
```

The app class automatically injects an option `--prop` to control the properties.

Here is how to create and use properties:
```python
import madhac.app as mapp

class TemplateApp(mapp.App):
    def main(self):
        self.logger.info(mapp.properties.get('prop.test', 'DEFAULT'))

if __name__ == "__main__":
    app = TemplateApp()
    app.register_property('prop.test', 'Testing property')
    app.start()
```

The `register_property` method is used to display the help information to users.

## Properties
The properties are a nice way to have deployment specific variables injected into the script.

Using properties will generally be using two methods:
- `get(self, prop: str, default: typing.Any = None)`: To retrieve a property value and provide a default value if it is not set.
- `need(self, prop: str)`: To retrieve a property and raise an exception if not set.

## Logger
A console logging helping methods.
