castre
====

This is a python library for C++ AST-based REfactoring

- easy
- simple
- minimal
- changes only where to refactor

## How to Use

1. install this package
1. write a script to refactor like an example below
1. execute the script
1. execute your formatter
1. verify and approve the changes by `git add -p`
1. save the approved changes by `git commit -m ...`
1. discard the unapproved changes by `git restore .`

## Example

refactoring script:
```python
import castre
import re

def walker(item):
  # The actual AST json data is stored at `item.raw`
  # You can see it by `clang++ -Xclang -ast-dump=json -c [filename and options...]`
  # And you can also see an AST structure in human-readable form by -ast-dump option without any value
  # Please note that outputs of both commands are huge
  if item.raw["kind"] == "DeclStmt" and item.raw["inner"][0]["kind"] == "VarDecl":
    item.refactor(fix)
  else:
    for child in item:
      walker(child)

def fix(text):
  if text.startswith("auto"):
    text = "\n// meta comment to ignore violation in the next line\n" + text
  else:
    text = re.sub(r"^([^=]*)=(.*)$", r"\1{\2}", text, flags=re.S)
  return text

# parse cpp codes and queue refactoring tasks
fixer = castre.walk(
    ["a.cc", "-I.", "-std=c++20"],
    walker,
    path_filter=lambda x: x is not None and x.startswith("/Users/falsycat"))

# you can reuse the fixer
castre.walk(
    ["b.cc", "-I.", "-std=c++20"],
    walker,
    fixer=fixer,
    path_filter=lambda x: x is not None and x.startswith("/Users/falsycat"))

# execute the tasks and apply changes to the actual files
fixer.fix()
```

before:
```cpp
#include <iostream>

int main() {
  struct A { void f() { int a = 123; auto b = 1+2+3+4; } };
  int x = 123;
std::cout << "helloworld"
<< std::endl;
  auto y = 123;
    std::cout << "goodbye" << std::endl;
  int
  z
  =
  123;
}
```

after:
```cpp
#include <iostream>

int main() {
  struct A { void f() { int a { 123}; 
// meta comment to ignore violation in the next line
auto b = 1+2+3+4; } };
  int x { 123};
std::cout << "helloworld"
<< std::endl;
  
// meta comment to ignore violation in the next line
auto y = 123;
    std::cout << "goodbye" << std::endl;
  int
  z
  {
  123};
}
```

# License

WTFPL v2
