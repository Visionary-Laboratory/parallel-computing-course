// Meaningful algorithm checks: examples, boundary cases, and permutation effects.
import assert from 'node:assert/strict';
import {GAUSSIANS,tilesFor,tilePipeline,exclusiveScan,composite,gaussian2D} from './model.mjs';
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-12,`${a} != ${b}`);
assert.deepEqual(GAUSSIANS.map(g=>tilesFor(g)),[[0,1,4,5],[1,5],[5,6,9,10],[15]]);
const p=tilePipeline();assert.deepEqual(p.counts,[4,2,4,1]);assert.deepEqual(p.offsets,[0,4,6,10]);assert.equal(p.total,11);
assert.deepEqual(p.sorted.slice(...p.ranges[5]).map(x=>x.id),[0,2,1]);assert.deepEqual(p.ranges[5],[4,7]);
assert.deepEqual(p.ranges[2],[0,0]);assert.deepEqual(p.ranges[15],[10,11]);
assert.deepEqual(exclusiveScan([2,0,3,1]),{offsets:[0,2,2,5],total:6});
assert.deepEqual(exclusiveScan([]),{offsets:[],total:0});
assert.deepEqual(tilesFor({x:-20,y:-20,radius:2}),[]);
assert.deepEqual(tilesFor({x:8,y:8,radius:8}),[0]); // half-open upper edge
const gs=[{alpha:.5,color:[1,0,0]},{alpha:.25,color:[0,1,0]},{alpha:.5,color:[0,0,1]}];
assert.deepEqual(composite(gs).C,[.5,.125,.1875]);near(composite(gs).T,.1875);
assert.notDeepEqual(composite([...gs].reverse()).C,composite(gs).C);near(composite([...gs].reverse()).T,.1875);
assert.deepEqual(composite([], [.2,.4,.6]).color,[.2,.4,.6]);
near(gaussian2D(0,0,30,10,.4,.8),.8);
near(gaussian2D(30,0,30,10),Math.exp(-.5));
near(gaussian2D(0,30,30,10,Math.PI/2),Math.exp(-.5));
console.log('PASS: tile coverage, scan, sorting/ranges, compositing, empty cases, boundaries, and Gaussian rotation.');
