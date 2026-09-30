# Python DSA Codes

A practical collection of standalone Python scripts for learning **data structures**, **algorithms**, and **system-design-inspired patterns**.

Each script focuses on one concept and is designed to be run directly.

## Why this repository

- Beginner-friendly, readable implementations
- Broad topic coverage: fundamentals to advanced patterns
- Real-world style examples (caching, scheduling, routing, distributed concepts)
- Zero setup for most files (standard Python only)

## Repository structure

- All examples currently live in the repository root as individual `.py` files.
- Most files are self-contained and include demonstration logic.
- File names are descriptive and indicate the main concept implemented.

## Topic map (sample files)

### Fundamentals
- `LIFO_Stack_Wrapper.py`
- `Balanced_Brackets_Validator.py`
- `Fixed_Size_Ring_Buffer.py`
- `Node_Based_Pointer_Chain.py`
- `Binary_Search_Tree_Insertion.py`

### Search, sort, and optimization
- `Recursive_Divide_And_Conquer_Sort.py`
- `Three_Pointer_Pivot.py`
- `Memoized_Fibonacci_Sequence.py`
- `Space_Optimized_Matrix_Edit_Distance.py`

### Graphs and pathfinding
- `Simple_Social_Network_Graph.py`
- `Friends_of_Friends_Finder.py`
- `Grid_Based_A*_Pathfinding_Engine.py`
- `Kruskal_MST_Engine_With_Union_FInd.py`
- `Single_Pass_Bridge_Detector.py`

### Caching and probabilistic structures
- `Memory_Cache_From_Scratch.py`
- `Hash_Map_&_Doubly_Linked_List_Cache_Engine.py`
- `Production_Grade_LRU_K_Cache_Engine.py`
- `Production_Grade_Space_Efficient_Bloom_Filter.py`
- `Cuckoo_Filter_with_Fingerprint_Eviction_&_Deletions.py`

### Concurrency, reliability, and distributed patterns
- `Thread_Safe_Bounded_Queue_using_Condition_Variables.py`
- `Thread_Safe_Writer_Preference_Read_Write_Lock.py`
- `Crash_Resistant_Write_Ahead_Log_Engine.py`
- `Distributed_Raft_Leader_Election_State_Machine.py`
- `Production_Grade_Transactional_Outbox_&_Relay_Engine.py`

## Quick start

### Requirements

- Python 3.8+
- No external dependencies for most scripts

### Run examples

```bash
python Balanced_Brackets_Validator.py
python Grid_Based_A*_Pathfinding_Engine.py
python Production_Grade_LRU_K_Cache_Engine.py
```

## Suggested learning path

1. Start with stack, queue, hashmap, and linked structure examples.
2. Move to trees, heaps, recursion, and dynamic programming.
3. Continue with graph traversal and shortest-path problems.
4. Explore caching, probabilistic structures, and distributed patterns.

## How to contribute

Contributions are welcome.

- Keep scripts focused on one core concept.
- Use clear naming and readable logic.
- Prefer standalone examples that run without extra dependencies.

## Improvement roadmap

Potential future improvements for the repository:

- Group scripts into topic-based folders while preserving runnable examples.
- Add a small index table mapping concept → file.
- Add lightweight unit tests for selected canonical implementations.
- Add script headers with complexity notes (`Time`, `Space`, `Use case`).

## License

This repository is for learning and educational use.
