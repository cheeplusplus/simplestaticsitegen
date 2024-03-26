# Simple Static Site Generator

Takes an input directory with Markdown, plain HTML, or Jinja templates and turns them into a nice static HTML website.

Recommended Python 3.6 or later.


## Customization

### Templates
To replace the default templates, in your input directory, create `.templates/` and replace the files that exist in `sssg/default_templates` with your own.
Otherwise, use regular Jinja template extensions.

### Jinja filters
To add custom Jinja filters, create a file and pass the path to the `custom_filter_module_path=` parameter of `process_directory`, relative to the working directory (this can be the same file as the one for Markdown extensions). The file must contain a dictionary by the name of `SSSG_JINJA_FILTERS`, where the key is the filter name and the value is a method to transform the input.

Example:
```
def reversed_text(input: str) -> str:
  return input[::-1]


SSSG_JINJA_FILTERS = {"reverse": reversed_text}
```

and then in your Jinja files you can use the filter:
```
Normal text, {{ "reversed text" | reverse }}
```

### Markdown extensions
To add custom Markdown extensions, create a file and pass the path to the `custom_md_extension_module_path=` parameter of `process_directory`, relative to the working directory (this can be the same file as the one for Jinja filters). The file must contain a list by the name of `SSSG_MD_EXTENSIONS`, the items inheriting from `markdown.Extension`. For more info see the [python-markdown documentation](https://python-markdown.github.io/extensions/api/).

Example:
```
from markdown.extensions.tables import TableExtension

SSSG_MD_EXTENSIONS = [TableExtension()]
```

and then in your Markdown file you can use the extension:
```
First Header  | Second Header
------------- | -------------
Content Cell  | Content Cell
Content Cell  | Content Cell
```

## Running

CLI:

```
sssg [--delete] [--files-as-dirs] [--ignore *.ignore,paths/] source destination
```

Code example

```
import sssg

sssg.process_directory("input", "output")
```


## Examples

[Creator's blog site using SSSG](https://github.com/cheeplusplus/ncn-blog)
