# graph_node_classification v2: verifier.evaluate matches prediction and confidence keys as
# str(node id), rejects keys that collide after str(), and rejects missing or non-integer class
# predictions instead of dropping them and truncating the ground truth. Work image unchanged.
FROM --platform=linux/amd64 seededge/edgebench.judge.graph_node_classification@sha256:518c105ec283ea9231ecb87886e0937c14a7bd937d8e385afaa3369800c5c3bd
COPY files/home/workspace/045_graph_node_classification/verifier.py /home/workspace/045_graph_node_classification/verifier.py
