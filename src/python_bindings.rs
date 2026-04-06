use pyo3::prelude::*;
use crate::Tree;  // imports Tree from the original lib.rs

/// TO DO:
///   1. new, add_node, add_child, add_child_to_root — gets you a working tree - DONE
///   2. len, is_empty, clear, remove_subtree — utility - DONE
///   3. get, children, parent_index_unchecked — lets you read it back - DONE
///   4. iter (as items()) — lets Python loop over the tree - DONE
///   5. traverse — most powerful, do last once you're comfortable

#[pyclass(unsendable)]  // Marking as unsendable for now, will throw error if used across threads
pub struct PyTree {
    inner: Tree<Py<PyAny>>,
}

#[pymethods]
impl PyTree {
    #[new]                          // tells PyO3 this is __init__ / __new__
    pub fn new() -> Self {          // no arguments, matches Tree::new()
        PyTree {
            inner: Tree::new(),     // just delegates to the original
        }
    }

    pub fn add_node(&mut self, data: Py<PyAny>) -> usize {
        self.inner.add_node(data)
    }

    pub fn add_child(&mut self, parent: usize, data: Py<PyAny>) -> usize {
        self.inner.add_child(parent, data)
    }

    pub fn add_child_to_root(&mut self, data: Py<PyAny>) -> usize {
        self.inner.add_child_to_root(data)
    }

    pub fn __len__(&self) -> usize {
        self.inner.len()
    }

    pub fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }

    pub fn clear(&mut self) {
        self.inner.clear();
    }

    pub fn remove_subtree(&mut self, index: usize) {
        self.inner.remove_subtree(index);
    }

    pub fn get(&self, py: Python<'_>, index: usize) -> Option<Py<PyAny>> {
        self.inner.get(index).map(|obj| obj.clone_ref(py))
    }

    pub fn set(&mut self, index: usize, data: Py<PyAny>) {
        if let Some(node) = self.inner.get_mut(index) {
            *node = data;
        }
    }

    pub fn children(&self, index: usize) -> Vec<usize> {
        self.inner.children(index).to_vec()
    }

    pub fn parent_index_unchecked(&self, index: usize) -> Option<usize> {
        self.inner.parent_index_unchecked(index)
    }

    pub fn parent(&self, py: Python<'_>, index: usize) -> Option<Py<PyAny>> {
        let parent_idx = self.inner.parent_index_unchecked(index)?;
        self.inner.get(parent_idx).map(|obj| obj.clone_ref(py))
    }

    pub fn items(&self, py: Python<'_>) -> Vec<(usize, Py<PyAny>)> {
        self.inner.iter().map(|(idx, obj)| (idx, obj.clone_ref(py))).collect()
    }

    /// Merges duplicate internal nodes (non-root, non-leaf) whose data compares equal with ==.
    /// The node with the smaller subtree is merged into the larger one:
    /// its children are moved (not copied) under the larger node, then it is removed.
    /// Repeats until no duplicates remain. Data must support Python == comparison.
    pub fn deduplicate(&mut self, py: Python<'_>) -> PyResult<()> {
        loop {
            // Collect indices of internal nodes: must have a parent AND have children
            let candidates: Vec<usize> = self.inner
                .iter()
                .filter_map(|(idx, _)| {
                    let has_parent = self.inner.parent_index_unchecked(idx).is_some();
                    let has_children = !self.inner.children(idx).is_empty();
                    if has_parent && has_children { Some(idx) } else { None }
                })
                .collect();

            // Find the first pair of nodes whose data compares equal with Python ==
            let mut merge_pair: Option<(usize, usize)> = None;
            'outer: for i in 0..candidates.len() {
                for j in (i + 1)..candidates.len() {
                    let a = candidates[i];
                    let b = candidates[j];
                    let data_a = self.inner.get(a).unwrap();
                    let data_b = self.inner.get(b).unwrap();
                    if data_a.bind(py).eq(data_b.bind(py))? {
                        let size_a = self.inner.subtree_size(a);
                        let size_b = self.inner.subtree_size(b);
                        // (smaller, larger)
                        merge_pair = if size_a >= size_b {
                            Some((b, a))
                        } else {
                            Some((a, b))
                        };
                        break 'outer;
                    }
                }
            }

            match merge_pair {
                None => break, // no duplicates found, done
                Some((smaller, larger)) => {
                    // move_children updates parent pointers in Rust, no Python overhead
                    self.inner.move_children(smaller, larger);
                    // smaller now has no children so remove_subtree only removes it
                    self.inner.remove_subtree(smaller);
                }
            }
        }

        Ok(())
    }

    pub fn traverse(
        &self,
        py: Python<'_>,
        before: Py<PyAny>,
        after: Py<PyAny>,
    ) -> PyResult<()> {
        let mut error: Option<PyErr> = None;

        self.inner.traverse(
            |idx, data, err| {
                if err.is_none() {
                    if let Err(e) = before.call1(py, (idx, data.clone_ref(py))) {
                        *err = Some(e);
                    }
                }
            },
            |idx, data, err| {
                if err.is_none() {
                    if let Err(e) = after.call1(py, (idx, data.clone_ref(py))) {
                        *err = Some(e);
                    }
                }
            },
            &mut error,
        );

        match error {
            Some(e) => Err(e),
            None => Ok(()),
        }
    }
}

#[pymodule]
pub fn easy_tree(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyTree>()?;
    Ok(())
}