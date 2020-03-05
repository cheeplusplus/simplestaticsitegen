Simple Static Site Generator
===

Takes an input directory with Markdown, plain HTML, or Jinja templates and turns them into a nice static HTML website.

Recommended Python 3.6 or later.


Customization
---

In your input directory, create `.templates/



Running
---

CLI:

```
sssg [--delete] [--files-as-dirs] [--ignore *.ignore,paths/] source destination
```

Code example

```
import sssg

sssg.process_directory("input", "output")
```


Examples
---

[Creator's blog site using SSSG](https://github.com/cheeplusplus/ncn-blog)
