#!/bin/bash
# Run a named shipped test class with the evaluator's exact Maven flags.
cd /home/workspace/exchange-core
OPTS="--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/jdk.internal.ref=ALL-UNNAMED"
export MAVEN_OPTS="$(python3 -c 'import importlib.util as u;s=u.spec_from_file_location("e","/tmp/eval_exchange_core.py");m=u.module_from_spec(s);s.loader.exec_module(m);print(m.DELOMBOK_OPTS)')"
mvn -B test -Dtest="$1" -Dmaven.compiler.source=1.8 -Dmaven.compiler.target=1.8 -DfailIfNoTests=false "-Dsurefire.argLine=$OPTS" "-DargLine=$OPTS" > /out/mvn.log 2>&1
rc=$?
echo "MVN_RC $rc"
grep -E "Tests run:|FAIL|expected|BUILD" /out/mvn.log | head -40
