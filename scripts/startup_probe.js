// Append to the verified upstream smoke probe before its return statement.
const boot = window.__frBoot;
if (!boot || !boot.completeMs || !boot.stages?.length) {
  result.passed=false;result.warnings.push('Startup profile missing');
} else {
  const byStage=[];
  for(let i=0;i<boot.stages.length;i++){
    const x=boot.stages[i],end=boot.stages[i+1]?.atMs??boot.completeMs;
    byStage.push({name:x.name,progress:x.progress,durationMs:end-x.atMs});
  }
  result.boot={...boot,byStage};
  const light = new URLSearchParams(location.search).get('frlight')==='1';
  if(boot.mode!==(light?'light':'original')){
    result.passed=false;result.warnings.push('Unexpected profiling mode');
  }
}
