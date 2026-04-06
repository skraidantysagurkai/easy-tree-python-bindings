# easy-tree — Python Bindings

[![Build and test](https://github.com/ezka/easy-tree-python-bindings/actions/workflows/test.yml/badge.svg)](https://github.com/ezka/easy-tree-python-bindings/actions)

Python bindings for [easy-tree](https://github.com/antouhou/easy-tree), a lightweight Rust library for managing and traversing hierarchical data structures. Built with [PyO3](https://pyo3.rs) and [Maturin](https://maturin.rs).

> **Original library**: https://github.com/antouhou/easy-tree — all core tree logic is unchanged. This repo adds a `python_bindings.rs` layer on top.

---

## What this repo does

The original `easy-tree` crate provides a fast, allocation-efficient tree structure in Rust. This fork exposes that functionality to Python by:

- Adding `src/python_bindings.rs` with PyO3 wrappers around the core `Tree<T>` type
- Adding `pyproject.toml` for Maturin to build a Python wheel
- Adding `subtree_size` and `move_children` to `src/lib.rs` to support deduplication
- Implementing `deduplicate` — merges duplicate internal nodes by moving children from the smaller subtree to the larger one, then removing the smaller node
- Implementing `remove_subtree` — removes a node and all its descendants, freeing their indices for reuse

---

## Installation

Requires Rust and [Maturin](https://maturin.rs):

```bash
pip install maturin
maturin build --release
pip install --find-links target/wheels easy_tree
```

---

## Python API

```python
from easy_tree import PyTree

tree = PyTree()

# Building the tree
root       = tree.add_node("root")
child1     = tree.add_child(root, "child1")
child2     = tree.add_child(root, "child2")
grandchild = tree.add_child(child1, "grandchild")

# Reading
tree.get(root)        # "root"
tree.children(root)   # [1, 2]
tree.parent(child1)   # "root"

# Utility
len(tree)             # 4
tree.is_empty()       # False

# Iteration — returns list of (index, data) tuples
for idx, data in tree.items():
    print(idx, data)

# Traversal — depth-first with before/after callbacks
tree.traverse(
    lambda idx, data: print(f"enter {idx}: {data}"),
    lambda idx, data: print(f"leave {idx}: {data}"),
)

# Mutation
tree.set(child1, "updated")

# Removal
tree.remove_subtree(child1)   # removes child1 and all its descendants
tree.clear()                  # removes everything

# Deduplication — merges duplicate internal nodes
# (non-root, non-leaf nodes with equal data are merged;
#  the smaller subtree's children move to the larger one)
tree.deduplicate()
```

---

## Traversal output example

```
enter 0: root
  enter 1: child1
    enter 3: grandchild
    leave 3: grandchild
  leave 1: child1
  enter 2: child2
  leave 2: child2
leave 0: root
```

---

## Development

```bash
# Build and install into current venv
maturin develop

# Run Rust tests
cargo test

# Run Python tests
pytest tests/ -v
```

---

## How it works

`Tree<T>` in Rust is generic — PyO3 classes cannot be generic, so `PyTree` wraps a concrete `Tree<Py<PyAny>>`, where `Py<PyAny>` is PyO3's owned handle to any Python object. Methods that return data use `clone_ref(py)` to increment the Python reference count rather than copying data.

The `deduplicate` method uses two helper methods added to `Tree` in `lib.rs` (`subtree_size` and `move_children`) for direct access to the private node fields, keeping the heavy work in Rust and only crossing the Python/Rust boundary for `==` comparisons.

---

## Original library

All credit for the core data structure goes to [@antouhou](https://github.com/antouhou).
- Original repo: https://github.com/antouhou/easy-tree
- Crates.io: https://crates.io/crates/easy-tree
- Docs: https://docs.rs/easy-tree
