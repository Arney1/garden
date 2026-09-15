/* Deterministic build-time layout. No simulation is shipped to readers. */
const fs = require('node:fs');
const graph = JSON.parse(fs.readFileSync(0, 'utf8'));
const n = graph.nodes.length;
let seed = 17;
const random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
const positions = graph.nodes.map((_, i) => {
  const angle = i * 2.399963229728653;
  const r = 32 * Math.sqrt(i + 1);
  return {x: Math.cos(angle) * r, y: Math.sin(angle) * r, dx: 0, dy: 0};
});
const ideal = 50;
for (let step = 0; step < 220; step++) {
  const temperature = 18 * (1 - step / 220) + .2;
  for (const p of positions) { p.dx = -.045 * p.x; p.dy = -.045 * p.y; }
  for (let i = 0; i < n; i++) {
    const p = positions[i];
    for (let j = i + 1; j < n; j++) {
      const q = positions[j];
      const dx = p.x - q.x || (random() - .5) * .01;
      const dy = p.y - q.y || (random() - .5) * .01;
      const square = dx * dx + dy * dy + 1;
      const force = ideal * ideal / square;
      p.dx += dx * force; p.dy += dy * force;
      q.dx -= dx * force; q.dy -= dy * force;
    }
  }
  for (const [a, b] of graph.links) {
    const p = positions[a], q = positions[b];
    const dx = q.x - p.x, dy = q.y - p.y;
    const force = Math.sqrt(dx * dx + dy * dy) / ideal * .7;
    p.dx += dx * force; p.dy += dy * force;
    q.dx -= dx * force; q.dy -= dy * force;
  }
  for (const p of positions) {
    const size = Math.hypot(p.dx, p.dy) || 1;
    const speed = Math.min(size, temperature) / size;
    p.x += p.dx * speed; p.y += p.dy * speed;
  }
}
graph.nodes.forEach((node, i) => {
  node.x = Math.round(positions[i].x * 10) / 10;
  node.y = Math.round(positions[i].y * 10) / 10;
});
process.stdout.write(JSON.stringify(graph));
