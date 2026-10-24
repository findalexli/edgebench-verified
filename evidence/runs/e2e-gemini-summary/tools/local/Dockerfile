# Local stand-in for the E2B worker: its own dockerd (overlay2 store), python3, curl, patch.
FROM docker:29.1.3-dind
RUN apk add --no-cache bash python3 py3-pip curl patch git coreutils tar sed grep findutils procps gawk sudo iptables ip6tables flock
