# subs/baseline: not published

`solution/solution.py` here was the shipped baseline, a verbatim copy of
`/home/workspace/045_graph_node_classification/solution/solution.py` from the pinned judge image
`seededge/edgebench.judge.graph_node_classification@sha256:518c105ec283ea9231ecb87886e0937c14a7bd937d8e385afaa3369800c5c3bd`
(sha256 `cde8fb22137c7661b0b9b2d29df8b18923e4a16cb96e1bf826379367a12f2b76`). Image files are not stored in Git. To rebuild it:

```bash
cid=$(docker create seededge/edgebench.judge.graph_node_classification@sha256:518c105ec283ea9231ecb87886e0937c14a7bd937d8e385afaa3369800c5c3bd true)
mkdir -p solution && docker cp $cid:/home/workspace/045_graph_node_classification/solution/solution.py solution/solution.py && docker rm $cid
sha256sum solution/solution.py   # expect cde8fb22137c7661b0b9b2d29df8b18923e4a16cb96e1bf826379367a12f2b76
```
