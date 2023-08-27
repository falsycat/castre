import bisect
import json
import os
import subprocess

def walk(args, walker, path_filter=None, fixer=None):
  proc = subprocess.run(["clang++", "-Xclang", "-ast-dump=json", "-c", *args], capture_output=True)
  if proc.returncode != 0:
    print(proc.stderr.decode("utf-8"))
    raise Exception("analysis failure")

  tree =  json.loads(proc.stdout)
  root = Item(tree)

  fixer = fixer if fixer is not None else Fixer()
  file  = None
  path  = None
  for item in tree["inner"]:
    if "file" in item["loc"]:
      path = os.path.abspath(item["loc"]["file"])
      file = None

    if path_filter is not None and not path_filter(path):
      continue

    if file is None:
      file = fixer.makeFile(path)

    walker(Item(item, parent=root, file=file))

  return fixer

class Item:
  def __init__(self, j, parent=None, file=None):
    self.parent = parent
    self.raw    = j
    self.file   = None

    if parent is not None:
      self.file = parent.file
    if file is not None:
      self.file = file

  def __iter__(self):
    return ItemItr(self)

  def refactorable(self):
    return self.file is not None and  "file" not in self.raw["range"]["end"]

  def range(self):
    if not self.refactorable():
      raise Exception("item is not refactorable")

    ra    = self.raw["range"]
    begin = ra["begin"]["offset"]
    end   = ra["end"]["offset"]
    return (begin, end)

  def pos(self):
    begin, end = self.range()
    return (begin, end-begin)

  def refactor(self, text):
    self.file.replace(*self.pos(), text)

  def insertBefore(self, text):
    self.file.replace(range()[0], 0, text)

  def insertAfter(self, text):
    self.file.replace(range()[1], 0, text)

class ItemItr:
  def __init__(self, item):
    self.index = 0
    self.item  = item
    self.inner = self.item.raw["inner"] if "inner" in self.item.raw else None

  def __next__(self):
    if self.inner == None or len(self.inner) <= self.index:
      raise StopIteration()
    ret = Item(self.inner[self.index], parent=self.item)
    self.index += 1
    return ret

class Fixer:
  def __init__(self):
    self.files = {}

  def makeFile(self, path):
    if path in self.files:
      return self.files[path]
    ret = File(path);
    self.files[path] = ret
    return ret

  def fix(self):
    for f in self.files.values():
      f.fix()

class File:
  def __init__(self, path):
    self.path  = path
    self.tasks = []

  def replace(self, offset, n, text):
    idx = bisect.bisect(self.tasks, x=offset, key=lambda x: x[0])

    if idx > 0:
      prev = self.tasks[idx-1]
      if prev[0]+prev[1] > offset:
        raise Exception("change conflict")

    if idx < len(self.tasks):
      next = self.tasks[idx]
      if next[0] < offset+n:
        raise Exception ("change conflict")

    self.tasks.insert(idx, (offset, n, text))

  def dryFix(self):
    with open(self.path, "r") as f:
      src = f.read()

    for task in reversed(self.tasks):
      begin = task[0]
      end   = begin + task[1]
      text  = task[2]
      if not isinstance(text, str):
        text = text(src[begin:end])
      src = src[0:begin] + text + src[end:]
    return src

  def fix(self):
    src = self.dryFix()
    with open(self.path, "w") as f:
      f.write(src)
