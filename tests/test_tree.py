from easy_tree import PyTree
import pytest


def test_new():
    tree = PyTree()
    assert tree.is_empty()
    assert len(tree) == 0


def test_add_node():
    tree = PyTree()
    root = tree.add_node("root")
    assert root == 0
    assert len(tree) == 1
    assert not tree.is_empty()


def test_add_child():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")
    grandchild = tree.add_child(child, "grandchild")

    assert len(tree) == 3
    assert tree.children(root) == [child]
    assert tree.children(child) == [grandchild]
    assert tree.children(grandchild) == []


def test_add_child_to_root():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child_to_root("child")

    assert tree.children(root) == [child]
    assert tree.parent(child) == "root"


def test_get():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")

    assert tree.get(root) == "root"
    assert tree.get(child) == "child"
    assert tree.get(999) is None


def test_parent():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")

    assert tree.parent(root) is None
    assert tree.parent(child) == "root"


def test_clear():
    tree = PyTree()
    tree.add_node("root")
    tree.clear()

    assert tree.is_empty()
    assert len(tree) == 0


def test_remove_subtree():
    tree = PyTree()
    root = tree.add_node("root")
    child1 = tree.add_child(root, "child1")
    child2 = tree.add_child(root, "child2")
    tree.add_child(child1, "grandchild")

    assert len(tree) == 4
    tree.remove_subtree(child1)

    assert len(tree) == 2
    assert tree.get(child1) is None
    assert tree.children(root) == [child2]


def test_items():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")

    items = dict(tree.items())
    assert items[root] == "root"
    assert items[child] == "child"


def test_set():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")

    # overwrite existing data
    tree.set(root, "new_root")
    assert tree.get(root) == "new_root"

    # set does not affect other nodes
    assert tree.get(child) == "child"

    # set works with any Python type, not just strings
    tree.set(child, 42)
    assert tree.get(child) == 42

    # tree structure is unchanged after set
    assert tree.children(root) == [child]
    assert tree.parent(child) == "new_root"


def test_traverse_order():
    tree = PyTree()
    root = tree.add_node("root")
    child1 = tree.add_child(root, "child1")
    tree.add_child(root, "child2")
    tree.add_child(child1, "grandchild")

    log = []
    tree.traverse(
        lambda idx, data: log.append(f"enter:{data}"),
        lambda idx, data: log.append(f"leave:{data}"),
    )

    # depth-first: enter root, enter child1, enter grandchild,
    # leave grandchild, leave child1, enter child2, leave child2, leave root
    assert log == [
        "enter:root",
        "enter:child1",
        "enter:grandchild",
        "leave:grandchild",
        "leave:child1",
        "enter:child2",
        "leave:child2",
        "leave:root",
    ]


def test_traverse_collect_indices():
    tree = PyTree()
    root = tree.add_node("a")
    child1 = tree.add_child(root, "b")
    tree.add_child(root, "c")
    tree.add_child(child1, "d")

    indices_seen = []
    tree.traverse(
        lambda idx, data: indices_seen.append(idx),
        lambda idx, data: None,
    )

    # every node index is visited exactly once in before callback
    assert len(indices_seen) == len(tree)
    assert set(indices_seen) == {root, child1, 2, 3}


def test_traverse_empty_tree():
    tree = PyTree()
    log = []
    # traverse on an empty tree should not call either callback
    tree.traverse(
        lambda idx, data: log.append("before"),
        lambda idx, data: log.append("after"),
    )
    assert log == []


def test_move_subtree():
    tree = PyTree()
    root = tree.add_node("root")
    child1 = tree.add_child(root, "child1")
    child2 = tree.add_child(root, "child2")
    grand = tree.add_child(child1, "grandchild")

    # move child1 (and its subtree) under child2
    tree.move_subtree(child1, child2)

    assert tree.children(root) == [child2]  # child1 detached from root
    assert tree.children(child2) == [child1]  # child1 now under child2
    assert tree.children(child1) == [grand]  # grandchild still under child1
    assert tree.parent(child1) == "child2"
    assert tree.parent(grand) == "child1"
    assert len(tree) == 4  # nothing added or removed


def test_move_subtree_self_referential_root_does_not_hang():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")
    grand = tree.add_child(child, "grandchild")

    # This must return quickly — previously hung forever due to root's
    # self-referential parent pointer causing is_descendant to loop infinitely
    with pytest.raises(ValueError):
        tree.move_subtree(child, grand)  # invalid: grand is inside child's subtree


def test_move_subtree_cycle_raises():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")
    grand = tree.add_child(child, "grand")

    import pytest

    with pytest.raises(ValueError):
        tree.move_subtree(child, grand)  # grand is inside child's subtree


def test_move_subtree_root_raises():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")

    import pytest

    with pytest.raises(ValueError):
        tree.move_subtree(root, child)  # cannot move root


def test_move_node():
    tree = PyTree()
    root = tree.add_node("root")
    child1 = tree.add_child(root, "child1")
    child2 = tree.add_child(root, "child2")
    grand = tree.add_child(child1, "grandchild")

    # move only child1 under child2 — grandchild stays under root
    tree.move_node(child1, child2)

    assert tree.children(root) == [child2, grand]  # grandchild re-parented to root
    assert tree.children(child2) == [child1]  # child1 now under child2
    assert tree.children(child1) == []  # child1 has no children
    assert tree.parent(child1) == "child2"
    assert tree.parent(grand) == "root"
    assert len(tree) == 4  # nothing added or removed


def test_move_node_cycle_raises():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")
    grand = tree.add_child(child, "grand")

    import pytest

    with pytest.raises(ValueError):
        tree.move_node(child, grand)


def test_deduplicate_merges_internal_nodes():
    tree = PyTree()
    root = tree.add_node("root")
    # Two internal "section" nodes with the same data
    a = tree.add_child(root, "section")
    b = tree.add_child(root, "section")
    # Each has children so they are internal nodes
    tree.add_child(a, "leaf_a1")
    tree.add_child(a, "leaf_a2")
    tree.add_child(b, "leaf_b1")

    # a has subtree size 3, b has subtree size 2 — b merges into a
    tree.deduplicate()

    assert len(tree) == 5  # root + one "section" + three leaves
    # Only one "section" node should remain
    section_nodes = [idx for idx, data in tree.items() if data == "section"]
    assert len(section_nodes) == 1
    # The surviving section has all three leaves
    assert len(tree.children(section_nodes[0])) == 3


def test_deduplicate_leaves_untouched():
    tree = PyTree()
    root = tree.add_node("root")
    # Duplicate leaves — should NOT be merged (leaves are excluded)
    tree.add_child(root, "leaf")
    tree.add_child(root, "leaf")

    tree.deduplicate()

    assert len(tree) == 3  # unchanged


def test_deduplicate_root_untouched():
    # A single-node tree — root is excluded, nothing to merge
    tree = PyTree()
    tree.add_node("root")
    tree.deduplicate()
    assert len(tree) == 1


def test_deduplicate_no_duplicates():
    tree = PyTree()
    root = tree.add_node("root")
    a = tree.add_child(root, "a")
    b = tree.add_child(root, "b")
    tree.add_child(a, "c")
    tree.add_child(b, "d")

    tree.deduplicate()

    assert len(tree) == 5  # unchanged


def test_set_then_traverse():
    tree = PyTree()
    root = tree.add_node("root")
    child = tree.add_child(root, "child")

    tree.set(child, "updated")

    seen = []
    tree.traverse(
        lambda idx, data: seen.append(data),
        lambda idx, data: None,
    )

    assert "updated" in seen
    assert "child" not in seen


if __name__ == "__main__":
    results = []
    tests = [
        test_new,
        test_add_node,
        test_add_child,
        test_add_child_to_root,
        test_get,
        test_parent,
        test_clear,
        test_remove_subtree,
        test_items,
        test_set,
        test_move_subtree,
        test_move_subtree_self_referential_root_does_not_hang,
        test_move_subtree_cycle_raises,
        test_move_subtree_root_raises,
        test_move_node,
        test_move_node_cycle_raises,
        test_deduplicate_merges_internal_nodes,
        test_deduplicate_leaves_untouched,
        test_deduplicate_root_untouched,
        test_deduplicate_no_duplicates,
        test_traverse_order,
        test_traverse_collect_indices,
        test_traverse_empty_tree,
        test_set_then_traverse,
    ]
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception as e:
            print(f"FAIL  {t.__name__}: {e}")
