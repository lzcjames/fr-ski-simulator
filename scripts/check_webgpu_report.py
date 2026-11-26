"""Never count WebGL2 fallback as a WebGPU test pass."""
import json
import sys
from pathlib import Path

def check(report):
    backend=report.get("game",{}).get("backend")
    probe=report.get("probe") or {}
    print(json.dumps({"actualBackend":backend,"probeBackend":probe.get("actualBackend"),"passed":report.get("passed"),"readyMs":report.get("readyMs"),"error":report.get("error"),"warnings":report.get("warnings"),"consoleErrors":report.get("consoleErrors"),"exceptions":report.get("exceptions")},ensure_ascii=False))
    if backend!="webgpu" or probe.get("actualBackend")!="webgpu" or report.get("passed") is not True or probe.get("passed") is not True:
        raise SystemExit("Strict WebGPU gate not passed (fallback, unsupported adapter or game failure).")

if __name__=="__main__":check(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
