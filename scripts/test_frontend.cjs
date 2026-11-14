// Run with Node.js: node scripts/test_frontend.cjs
// DOM/camera doubles test lifecycle only, not a physical camera or rendering.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/vision/app.js'), 'utf8');
new vm.Script(source);
async function main() {
  const nodes = new Map(), timers = new Map();
  let timerId=0, stopped=0, resolveCamera, resolveFrame, frameSignal;
  const context2d = new Proxy({}, {get:()=>()=>{}});
  function element(id) {
    if (!nodes.has(id)) nodes.set(id, {
      hidden:true, disabled:false, style:{}, textContent:'', parentElement:{style:{}},
      videoWidth:640, videoHeight:480, play:async()=>{},
      getContext:()=>context2d, toBlob:fn=>fn({}),
      replaceChildren(){}, append(){}, addEventListener(){},
    });
    return nodes.get(id);
  }
  const track={stop(){stopped++;},addEventListener(){}};
  const stream={getTracks:()=>[track],getVideoTracks:()=>[track]};
  const sandbox={
    document:{getElementById:element,cookie:'csrftoken=test',addEventListener(){},createElement:()=>element(Symbol())},
    window:{addEventListener(){}},
    navigator:{mediaDevices:{getUserMedia:()=>new Promise(r=>{resolveCamera=r;})}},
    performance:{now:()=>100}, AbortController,
    setTimeout(fn){timers.set(++timerId,fn);return timerId;},clearTimeout(id){timers.delete(id);},
    fetch:async(url,options)=>{
      if(url==='/api/history/')return {ok:true,json:async()=>({count:0,events:[],top:[]})};
      frameSignal=options.signal;
      return new Promise(r=>{resolveFrame=r;});
    },
  };
  vm.createContext(sandbox);vm.runInContext(source,sandbox);
  let start=element('start').onclick();
  assert.equal(element('stop').disabled,false);
  element('stop').onclick();resolveCamera(stream);await start;
  assert.equal(stopped,1);assert.equal(element('video').hidden,true);
  assert.equal(element('start').disabled,false);
  start=element('start').onclick();resolveCamera(stream);await start;
  await Promise.resolve();await Promise.resolve();
  assert.equal(element('video').hidden,false);
  assert.equal(element('overlay').hidden,false);
  assert.ok(frameSignal);
  element('stop').onclick();
  assert.equal(frameSignal.aborted,true);
  resolveFrame({ok:true,status:200,json:async()=>({hands:[],total:9,saved:false})});
  await Promise.resolve();await Promise.resolve();await Promise.resolve();
  assert.equal(element('video').hidden,true);
  assert.equal(element('total').textContent,'0');
  assert.equal(timers.size,0);
  console.log('PASS: syntax; cancel camera acquisition; live preview; abort request; ignore stale response; clear timers.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
