// USB Power-Control Hub — 60 x 24 mm, 6-layer PCB + 3D-printed two-part case.
// Built in millimetres inside a root group scaled to metres.

const stage = document.querySelector('three-d-stage');
const { THREE } = await stage.ready;

/* ---------------------------------------------------------------- materials */
const M = {
  mask:    new THREE.MeshStandardMaterial({ name: 'soldermask_matte_black', color: 0x15181b, roughness: 0.94, metalness: 0.02 }),
  fr4:     new THREE.MeshStandardMaterial({ name: 'fr4_dielectric',         color: 0x9c8f63, roughness: 0.85, metalness: 0.0  }),
  copper:  new THREE.MeshStandardMaterial({ name: 'copper_layer',           color: 0xb87145, roughness: 0.45, metalness: 0.35 }),
  gold:    new THREE.MeshStandardMaterial({ name: 'enig_gold',              color: 0xd9ae55, roughness: 0.30, metalness: 0.40 }),
  epoxy:   new THREE.MeshStandardMaterial({ name: 'ic_epoxy_black',         color: 0x25282c, roughness: 0.44, metalness: 0.05 }),
  ceramic: new THREE.MeshStandardMaterial({ name: 'mlcc_ceramic',           color: 0xb6a48b, roughness: 0.68, metalness: 0.0  }),
  steel:   new THREE.MeshStandardMaterial({ name: 'connector_shell_steel',  color: 0xc2c7cc, roughness: 0.26, metalness: 0.42 }),
  plastic: new THREE.MeshStandardMaterial({ name: 'connector_plastic',      color: 0xdedad2, roughness: 0.55, metalness: 0.0  }),
  ferrite: new THREE.MeshStandardMaterial({ name: 'ferrite_core',           color: 0x3b3d40, roughness: 0.72, metalness: 0.05 }),
  ledG:    new THREE.MeshStandardMaterial({ name: 'led_lens_green', color: 0x9be89b, emissive: 0x2fbf5a, emissiveIntensity: 0.9, roughness: 0.25 }),
  ledA:    new THREE.MeshStandardMaterial({ name: 'led_lens_amber', color: 0xf3c98a, emissive: 0xd98212, emissiveIntensity: 0.9, roughness: 0.25 }),
  ledB:    new THREE.MeshStandardMaterial({ name: 'led_lens_blue',  color: 0x9dc9f0, emissive: 0x2a72c9, emissiveIntensity: 0.9, roughness: 0.25 }),
  print:   new THREE.MeshStandardMaterial({ name: 'printed_case_pa12', color: 0x8e9298, roughness: 0.82, metalness: 0.04 }),
  printAcc:new THREE.MeshStandardMaterial({ name: 'printed_button_pa12', color: 0xd9a441, roughness: 0.7, metalness: 0.05 }),
  screw:   new THREE.MeshStandardMaterial({ name: 'm2_screw_steel', color: 0x5a6068, roughness: 0.34, metalness: 0.45 })
};

/* ------------------------------------------------------------------ helpers */
const L = 60, W = 24, T = 1.6, CR = 1.2;
const HOLES = [{ x: -26.5, z: 9.5 }, { x: -26.5, z: -9.5 }];
const TOP = 1.600;

const root = new THREE.Group(); root.name = 'usb_power_hub';
const board = new THREE.Group(); board.name = 'pcb_assembly';
const caseBase = new THREE.Group(); caseBase.name = 'case_base_printed';
const caseLid = new THREE.Group(); caseLid.name = 'case_lid_printed';
root.add(board, caseBase, caseLid); root.scale.setScalar(0.001);

let TARGET = board;
const add = (m, shadow = false) => { m.castShadow = shadow; m.receiveShadow = shadow; TARGET.add(m); return m; };
function box(name, mat, w, h, d, x, y, z, shadow = false, ry = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.name = name; m.position.set(x, y + h / 2, z); m.rotation.y = ry;
  return add(m, shadow);
}
function disc(name, mat, r, h, x, y, z, seg = 32) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), mat);
  m.name = name; m.position.set(x, y + h / 2, z);
  return add(m, false);
}
function roundedRect(w, h, r, PathClass = THREE.Shape, ox = 0, oy = 0) {
  const s = new PathClass(), x = -w / 2 + ox, y = -h / 2 + oy;
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y); s.absarc(x + w - r, y + r, r, -Math.PI / 2, 0, false);
  s.lineTo(x + w, y + h - r); s.absarc(x + w - r, y + h - r, r, 0, Math.PI / 2, false);
  s.lineTo(x + r, y + h); s.absarc(x + r, y + h - r, r, Math.PI / 2, Math.PI, false);
  s.lineTo(x, y + r); s.absarc(x + r, y + r, r, Math.PI, Math.PI * 1.5, false);
  return s;
}
function circlePath(cxp, cyp, r, PathClass = THREE.Shape, cw = false) {
  const p = new PathClass();
  p.moveTo(cxp + r, cyp);
  p.absarc(cxp, cyp, r, 0, Math.PI * 2, cw);
  return p;
}
// extrude a plan-view shape (shape-x -> world x, shape-y -> world -z) upward
function planExtrude(name, mat, shapes, y0, thick, mat2, shadow = true) {
  const g = new THREE.ExtrudeGeometry(shapes, { depth: thick, bevelEnabled: false, curveSegments: 24 });
  g.rotateX(-Math.PI / 2); g.translate(0, y0, 0);
  const m = new THREE.Mesh(g, mat2 || mat); m.name = name;
  return add(m, shadow);
}

function annulus(name, mat, rOut, rIn, x, y, z, thick = 0.025) {
  const s = circlePath(x, -z, rOut);
  s.holes.push(circlePath(x, -z, rIn, THREE.Path, true));
  return planExtrude(name, mat, s, y, thick, null, false);
}

/* -------------------------------------------------- 6-layer board stack-up  */
function slab(name, mat, y0, thick, shrink = 0) {
  const shape = roundedRect(L - shrink, W - shrink, Math.max(0.3, CR - shrink / 2));
  for (const h of HOLES) {
    const p = new THREE.Path();
    p.absarc(h.x, -h.z, 1.1, 0, Math.PI * 2, true);
    shape.holes.push(p);
  }
  return planExtrude(name, mat, shape, y0, thick);
}
[
  ['soldermask_bottom', M.mask,   0.000, 0.025, 0],
  ['copper_L6_gnd',     M.copper, 0.025, 0.035, 0.02],
  ['prepreg_5',         M.fr4,    0.060, 0.200, 0.02],
  ['copper_L5_power',   M.copper, 0.260, 0.018, 0.02],
  ['core_4',            M.fr4,    0.278, 0.400, 0.02],
  ['copper_L4_gnd',     M.copper, 0.678, 0.018, 0.02],
  ['prepreg_3',         M.fr4,    0.696, 0.208, 0.02],
  ['copper_L3_signal',  M.copper, 0.904, 0.018, 0.02],
  ['core_2',            M.fr4,    0.922, 0.400, 0.02],
  ['copper_L2_gnd',     M.copper, 1.322, 0.018, 0.02],
  ['prepreg_1',         M.fr4,    1.340, 0.200, 0.02],
  ['copper_L1_signal',  M.copper, 1.540, 0.035, 0.02],
  ['soldermask_top',    M.mask,   1.575, 0.025, 0]
].forEach(([n, m, y, t, s]) => slab(n, m, y, t, s));

HOLES.forEach((h, i) => {
  const g = new THREE.CylinderGeometry(1.12, 1.12, T, 32, 1, true);
  const m = new THREE.Mesh(g, M.gold); m.name = `mounting_hole_${i + 1}_plating`;
  m.position.set(h.x, T / 2, h.z); add(m);
  annulus(`mounting_hole_${i + 1}_ring`, M.gold, 1.75, 1.1, h.x, TOP - 0.005, h.z, 0.02);
});

/* ------------------------------------------------------------- part helpers */
const pad = (name, w, d, x, z) => box(name, M.gold, w, 0.025, d, x, TOP - 0.004, z);
const PASSIVE = { '0201': [0.60, 0.30, 0.26], '0402': [1.00, 0.50, 0.50], '0603': [1.60, 0.80, 0.80],
                  '0805': [2.00, 1.25, 1.05], '1206': [3.20, 1.60, 1.10], '2512': [6.30, 3.20, 0.60] };
function passive(ref, code, x, z, ry = 0, mat = M.ceramic) {
  const [l, w, h] = PASSIVE[code], cap = l * 0.22, c = Math.cos(ry), s = Math.sin(ry);
  box(`${ref}_body`, mat, l - cap * 2, h, w, x, TOP, z, h > 0.5, ry);
  [-1, 1].forEach((d, i) => {
    const o = d * (l / 2 - cap / 2);
    box(`${ref}_term_${i + 1}`, M.gold, cap, h * 0.98, w * 1.02, x + o * c, TOP, z - o * s, false, ry);
  });
}
function ledPart(ref, x, z, mat) {
  box(`${ref}_body`, M.plastic, 0.62, 0.42, 0.5, x, TOP, z);
  box(`${ref}_lens`, mat, 0.5, 0.30, 0.42, x, TOP + 0.14, z);
  [-1, 1].forEach(d => box(`${ref}_term_${d > 0 ? 2 : 1}`, M.gold, 0.2, 0.4, 0.52, x + d * 0.4, TOP, z));
}
function qfn(ref, x, z, size, pins, h = 0.85) {
  const per = pins / 4, pitch = (size - 0.9) / per, span = (per - 1) * pitch / 2;
  box(`${ref}_body`, M.epoxy, size, h, size, x, TOP + 0.03, z, true);
  box(`${ref}_thermal_pad`, M.gold, size * 0.55, 0.03, size * 0.55, x, TOP, z);
  for (let i = 0; i < per; i++) {
    const o = -span + i * pitch, e = size / 2 - 0.08;
    pad(`${ref}_pin_${i + 1}`, 0.24, 0.5, x - e, z + o);
    pad(`${ref}_pin_${per + i + 1}`, 0.5, 0.24, x + o, z + e);
    pad(`${ref}_pin_${per * 2 + i + 1}`, 0.24, 0.5, x + e, z - o);
    pad(`${ref}_pin_${per * 3 + i + 1}`, 0.5, 0.24, x - o, z - e);
  }
}
function uson(ref, x, z, w = 2.0, d = 3.0, per = 4) {
  box(`${ref}_body`, M.epoxy, w, 0.55, d, x, TOP + 0.02, z, true);
  const span = (per - 1) * 0.25;
  for (let i = 0; i < per; i++) {
    pad(`${ref}_pin_${i + 1}`, 0.4, 0.26, x - w / 2 + 0.1, z - span + i * 0.5);
    pad(`${ref}_pin_${per + i + 1}`, 0.4, 0.26, x + w / 2 - 0.1, z + span - i * 0.5);
  }
}
function sot(ref, x, z, l, w, h, nA, nB, pitch, ry = 0) {
  box(`${ref}_body`, M.epoxy, l, h, w, x, TOP + 0.05, z, true, ry);
  const c = Math.cos(ry), s = Math.sin(ry);
  const place = (dx, dz, n) => box(n, M.gold, 0.3, 0.12, 0.28, x + dx * c + dz * s, TOP, z - dx * s + dz * c, false, ry);
  const sa = (nA - 1) * pitch / 2, sb = (nB - 1) * pitch / 2;
  for (let i = 0; i < nA; i++) place(-sa + i * pitch, -(w / 2 + 0.18), `${ref}_pin_${i + 1}`);
  for (let i = 0; i < nB; i++) place(sb - i * pitch, (w / 2 + 0.18), `${ref}_pin_${nA + i + 1}`);
}
function tactile(ref, x, z) {
  box(`${ref}_base`, M.epoxy, 3.2, 0.75, 2.6, x, TOP, z, true);
  const dome = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 1.05, 0.35, 32), M.steel);
  dome.name = `${ref}_dome`; dome.position.set(x, TOP + 0.92, z); add(dome, true);
  [-1, 1].forEach(d => box(`${ref}_pad_${d > 0 ? 2 : 1}`, M.gold, 0.9, 0.06, 2.4, x + d * 1.85, TOP - 0.02, z));
}
function crystal(ref, x, z) {
  box(`${ref}_can`, M.steel, 3.2, 0.75, 2.5, x, TOP + 0.06, z, true);
  box(`${ref}_base`, M.ceramic, 3.24, 0.08, 2.54, x, TOP, z);
  [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(([a, b], i) =>
    box(`${ref}_pad_${i + 1}`, M.gold, 0.9, 0.06, 0.8, x + a * 1.1, TOP - 0.02, z + b * 0.82));
}
function inductor(ref, x, z) {
  box(`${ref}_core`, M.ferrite, 2.5, 1.1, 2.0, x, TOP, z, true);
  [-1, 1].forEach(d => box(`${ref}_term_${d > 0 ? 2 : 1}`, M.gold, 0.55, 1.0, 2.02, x + d * 1.05, TOP, z));
}
function usbc(ref, mouthX, z, dir) {
  const g = new THREE.Group(); g.name = ref;
  const CWD = 8.94, CHT = 3.26, DEPTH = 7.35;
  const outer = roundedRect(CWD, CHT, 1.62);
  outer.holes.push(roundedRect(CWD - 0.56, CHT - 0.56, 1.34, THREE.Path));
  const sg = new THREE.ExtrudeGeometry(outer, { depth: DEPTH, bevelEnabled: false, curveSegments: 20 });
  sg.rotateY(Math.PI / 2);
  const shell = new THREE.Mesh(sg, M.steel); shell.name = `${ref}_shell`;
  shell.position.set(mouthX, TOP + CHT / 2, z);
  shell.rotation.y = dir > 0 ? Math.PI : 0;
  shell.castShadow = shell.receiveShadow = true; g.add(shell);
  const at = d => mouthX - dir * d;
  const mk = (name, mat, w, h, dp, dist, dy) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(dp, h, w), mat);
    m.name = name; m.position.set(at(dist), TOP + dy, z); g.add(m); return m;
  };
  mk(`${ref}_back_plate`, M.steel, CWD - 0.6, CHT - 0.6, 0.5, DEPTH - 0.35, CHT / 2).castShadow = true;
  mk(`${ref}_tongue`, M.plastic, 6.8, 0.72, 5.1, 3.1, CHT / 2);
  for (let i = 0; i < 6; i++)
    mk(`${ref}_contact_${i + 1}`, M.gold, 0.5, 0.06, 4.2, 2.7, CHT / 2 + 0.38).position.z = z + (i - 2.5) * 1.05;
  [[-1, 0.9], [1, 0.9], [-1, DEPTH - 1.1], [1, DEPTH - 1.1]].forEach(([sgn, d], i) => {
    mk(`${ref}_leg_${i + 1}`, M.gold, 1.0, 0.35, 1.4, d, -0.02).position.z = z + sgn * (CWD / 2 - 0.2);
  });
  board.add(g);
}

/* -------------------------------------------------------------- placement   */
const PORT_Z = 5.4;
usbc('J1_usbc_host', -30.4, 0, -1);
usbc('J2_usbc_out_a', 30.4, PORT_Z, 1);
usbc('J3_usbc_out_b', 30.4, -PORT_Z, 1);

qfn('U1_rp2040', -4.0, -1.0, 7.0, 56, 0.9);
qfn('U2_usb_hub', -16.0, 0.0, 6.0, 36, 0.85);
qfn('U3_buck_regulator', -16.2, 8.8, 2.0, 8, 0.7);
sot('U4_ldo_3v3', -7.2, 9.0, 2.9, 1.3, 1.05, 3, 2, 0.95);
uson('U5_qspi_flash', -4.0, 4.4);
qfn('U6_adc_24bit', 3.5, 0.0, 4.0, 24, 0.8);
sot('U11_vref', 3.5, 4.8, 2.9, 1.3, 1.05, 3, 2, 0.95);
qfn('U7_range_amp_a', 10.0, 3.8, 3.0, 16, 0.8);
qfn('U8_range_amp_b', 10.0, -3.8, 3.0, 16, 0.8);
qfn('U9_load_switch_a', 21.5, 7.1, 2.0, 8, 0.7);
qfn('U10_load_switch_b', 21.5, -7.1, 2.0, 8, 0.7);
sot('D1_esd_host', -21.0, 0.0, 1.6, 1.2, 0.6, 3, 3, 0.5);
sot('D2_esd_out_a', 18.4, 2.7, 1.6, 1.2, 0.6, 3, 3, 0.5);
sot('D3_esd_out_b', 18.4, -2.7, 1.6, 1.2, 0.6, 3, 3, 0.5);
sot('Q1_range_fet_a', 13.6, 3.7, 1.6, 1.2, 0.6, 3, 3, 0.5);
sot('Q2_range_fet_b', 13.6, -3.7, 1.6, 1.2, 0.6, 3, 3, 0.5);

crystal('Y1_12mhz', -1.4, 8.6);
inductor('L1_buck', -12.6, 8.8);
passive('C1_bulk', '1206', -20.6, 8.2);
passive('FB1_cmc', '0805', -20.6, -6.6);
tactile('SW1_port_a', 7.0, 8.8);
tactile('SW2_port_b', 7.0, -8.8);

[[1, 'a'], [-1, 'b']].forEach(([s, ch]) => {
  passive(`RS1_shunt_10m_${ch}`, '2512', 16.4, s * 7.4, 0, M.plastic);
  passive(`RS2_shunt_1r_${ch}`, '0805', 12.4, s * 7.4, 0, M.plastic);
  passive(`RS3_shunt_100r_${ch}`, '0402', 9.6, s * 7.4, 0, M.plastic);
  passive(`RS4_shunt_1k_${ch}`, '0402', 8.4, s * 7.4, 0, M.plastic);
  passive(`C_flt1_${ch}`, '0201', 7.0, s * 6.6);
  passive(`C_flt2_${ch}`, '0201', 7.0, s * 5.7);
  for (let i = 0; i < 6; i++) passive(`C_amp${i + 1}_${ch}`, '0201', 8.6 + i * 0.9, s * 1.8);
  for (let i = 0; i < 5; i++) passive(`R_sw${i + 1}_${ch}`, '0201', 15.2 + i * 0.9, s * 4.3);
  passive(`C_out1_${ch}`, '0402', 19.6, s * 4.3, Math.PI / 2);
  passive(`C_out2_${ch}`, '0603', 23.6, s * 2.2, Math.PI / 2);
  passive(`C_out3_${ch}`, '0402', 21.9, s * 4.2);
});

const LED_MATS = [M.ledG, M.ledG, M.ledB, M.ledA, M.ledG, M.ledA, M.ledG, M.ledA];
LED_MATS.forEach((m, i) => ledPart(`D${10 + i}_status_${i + 1}`, -19 + i * 2.0, -10.0, m));

for (let i = 0; i < 13; i++) passive(`C_hub${i + 1}`, '0201', -20.0 + i * 0.92, 5.2);
for (let i = 0; i < 19; i++) passive(`C_mcu${i + 1}`, '0201', -20.0 + i * 0.95, -5.7);
for (let i = 0; i < 13; i++) passive(`R_io${i + 1}`, '0201', -19.0 + i * 1.0, -7.9);
for (let i = 0; i < 8; i++)  passive(`C_core${i + 1}`, '0201', -7.4 + i * 0.9, 2.0);
for (let i = 0; i < 6; i++)  passive(`C_pll${i + 1}`, '0201', -0.2, -4.6 + i * 0.9, Math.PI / 2);
for (let i = 0; i < 5; i++)  passive(`C_adc${i + 1}`, '0201', 1.4 + i * 0.9, -2.9);
// upstream UFP: Rd 5.1k on both CC pins + D+/D- series terminations
['R_cc1_rd_5k1', 'R_cc2_rd_5k1', 'R_dp_host', 'R_dm_host'].forEach((n, i) =>
  passive(n, '0201', -22.3, -2.0 + i * 0.9, Math.PI / 2));
// downstream DFP: Rp 56k on both CC pins of each port, gated with VBUS so the
// DUT detaches cleanly when its port is switched off
['R_cc1_rp_a', 'R_cc2_rp_a', 'R_cc1_rp_b', 'R_cc2_rp_b'].forEach((n, i) =>
  passive(n, '0201', 25.2 + i * 0.9, 0, Math.PI / 2));
sot('Q3_cc_gate_a', 20.8, 2.4, 1.6, 1.2, 0.6, 3, 3, 0.5);
sot('Q4_cc_gate_b', 20.8, -2.4, 1.6, 1.2, 0.6, 3, 3, 0.5);
for (let i = 0; i < 4; i++)  passive(`C_host${i + 1}`, '0201', -23.4, -2.0 + i * 0.9, Math.PI / 2);

[6.6, 8.4, 10.2, 12.0].forEach((x, i) => disc(`TP${i + 1}`, M.gold, 0.6, 0.03, x, TOP - 0.005, 0));
for (let i = 0; i < 6; i++) pad(`SWD_pad_${i + 1}`, 0.85, 1.5, 14.6 + i * 1.27, 0);
// BOOTSEL recovery: short these two pads (QSPI_SS / GND) while plugging in
pad('BOOT_pad_qspi_ss', 0.8, 1.2, -2.1, 4.4);
pad('BOOT_pad_gnd', 0.8, 1.2, -1.1, 4.4);

/* ------------------------------------------------------ silkscreen helper  */
const SILK_FONT = 'ui-monospace, Menlo, "Hiragino Kaku Gothic ProN", "Noto Sans JP", monospace';
function silkPlane(name, w, h, draw, PX = 40) {
  const cv = document.createElement('canvas');
  cv.width = w * PX; cv.height = h * PX;
  const ctx = cv.getContext('2d');
  ctx.strokeStyle = ctx.fillStyle = 'rgba(238,236,230,0.92)';
  ctx.lineWidth = 6;
  const a = {
    ctx,
    px: v => (v + w / 2) * PX,
    pz: v => (v + h / 2) * PX,
    rect: (x, z, rw, rh) => ctx.strokeRect(a.px(x - rw / 2), a.pz(z - rh / 2), rw * PX, rh * PX),
    circle: (x, z, r, fill) => { ctx.beginPath(); ctx.arc(a.px(x), a.pz(z), r * PX, 0, Math.PI * 2); fill ? ctx.fill() : ctx.stroke(); },
    line: (x1, z1, x2, z2) => { ctx.beginPath(); ctx.moveTo(a.px(x1), a.pz(z1)); ctx.lineTo(a.px(x2), a.pz(z2)); ctx.stroke(); },
    text: (t, x, z, size = 30, align = 'center') => {
      ctx.font = '700 ' + size + 'px ' + SILK_FONT;
      ctx.textAlign = align; ctx.textBaseline = 'middle';
      ctx.fillText(t, a.px(x), a.pz(z));
    }
  };
  draw(a);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({
    name, map: tex, transparent: true, roughness: 0.9, metalness: 0, depthWrite: false }));
  m.name = name; m.rotation.x = -Math.PI / 2;
  return m;
}

/* --------------------------------------------------------- board silkscreen */
const boardSilk = silkPlane('silkscreen_top', L, W, a => {
  a.rect(-26.8, 0, 7.6, 9.2); a.rect(26.8, PORT_Z, 7.6, 9.2); a.rect(26.8, -PORT_Z, 7.6, 9.2);
  a.ctx.setLineDash([14, 10]); a.ctx.lineWidth = 4;
  a.rect(15.0, 5.9, 17.0, 9.0); a.rect(15.0, -5.9, 17.0, 9.0);
  a.ctx.setLineDash([]); a.ctx.lineWidth = 6;
  a.text('HOST', -26.5, 5.9, 46); a.text('J1', -22.6, 2.6, 36, 'right');
  a.text('OUT A', 21.0, 10.7, 46); a.text('OUT B', 21.0, -10.7, 46);
  a.text('J2', 22.6, 1.5, 36, 'left'); a.text('J3', 22.6, -1.5, 36, 'left');
  a.text('U1', -8.0, -0.9, 40, 'right'); a.circle(-7.9, -4.7, 0.24, true);
  a.text('U2', -19.6, 0, 38, 'right'); a.circle(-19.4, -3.2, 0.22, true);
  a.text('U6', 1.0, 0, 36, 'right'); a.circle(1.2, -2.3, 0.2, true);
  a.text('U7', 8.1, 3.8, 34, 'right'); a.text('U8', 8.1, -3.8, 34, 'right');
  a.text('U9', 21.5, 5.4, 32); a.text('U10', 21.5, -5.4, 32);
  a.text('U5', -4.0, 6.3, 32); a.text('BOOT', -1.6, 6.1, 32); a.text('Y1', -1.4, 6.9, 32); a.text('L1', -12.6, 7.1, 32);
  a.text('U3', -16.2, 7.1, 32); a.text('U4', -7.2, 7.2, 32); a.text('D1', -21.0, 1.5, 32);
  a.text('SW1', 4.8, 8.8, 36, 'right'); a.text('SW2', 4.8, -8.8, 36, 'right');
  a.text('RS1', 16.4, 5.2, 32); a.text('RS1', 16.4, -5.2, 32);
  a.text('SWD', 17.2, 1.3, 32); a.text('TP · SDA SCL TX RX', 9.3, 1.2, 32);
  a.text('CC Rp', 15.8, 2.2, 32); a.text('CC Rd', -23.4, 1.6, 32);
  ['PWR', '3V3', 'LNK', 'ACT', 'AON', 'AOC', 'BON', 'BOC'].forEach((t, i) => a.text(t, -19 + i * 2.0, -8.9, 32));
  a.text('USB-PWR-HUB · 2CH · USB2.0 HS · 6L · REV A', -3.0, -11.1, 38, 'left');
  a.text('PPK2-COMPATIBLE  µA→A', -3.0, 11.1, 36, 'left');
});
boardSilk.position.y = TOP + 0.004; board.add(boardSilk);

/* =========================================================== enclosure =======
   Printed tub (1.8 mm walls, M2 bosses) + a 1.6 mm PCB top panel that drops
   into a rebate and doubles as the user-facing legend.                        */
const WALL = 1.8, CLR = 0.4;
const IX = L / 2 + CLR, IZ = W / 2 + CLR;
const OX = IX + WALL, OZ = IZ + WALL;
const FLOOR_T = 1.4, GAP = 1.6, FLOOR_Y = -(GAP + FLOOR_T);
const LEDGE = 5.05, RIM_T = 0.9, LID_T = 1.6, LID_TOP = LEDGE + LID_T;
const POST_R = 3.0, POST_RI = 1.2;
const PORT_W = 9.4, PORT_Y0 = 1.40, PORT_H = LEDGE - PORT_Y0;
const SLOT_X = OX - WALL / 2;
const LX = (OX - RIM_T - 0.15) * 2, LZ = (OZ - RIM_T - 0.15) * 2, LR = POST_R - RIM_T;
const BTN = [[7.0, 8.8, 'a'], [7.0, -8.8, 'b']];
const LED_X = i => -19 + i * 2.0, LED_Z = -10.0;

function cornerPost(sx, sz, y0, h, name, rOut = POST_R, rIn = POST_RI) {
  const cxp = (OX - POST_R) * sx, cyp = -(OZ - POST_R) * sz;
  const a0 = sx > 0 ? (sz > 0 ? -Math.PI / 2 : 0) : (sz > 0 ? Math.PI : Math.PI / 2);
  const a1 = a0 + Math.PI / 2, s = new THREE.Shape();
  s.moveTo(cxp + rIn * Math.cos(a0), cyp + rIn * Math.sin(a0));
  s.lineTo(cxp + rOut * Math.cos(a0), cyp + rOut * Math.sin(a0));
  s.absarc(cxp, cyp, rOut, a0, a1, false);
  s.lineTo(cxp + rIn * Math.cos(a1), cyp + rIn * Math.sin(a1));
  s.absarc(cxp, cyp, rIn, a1, a0, true);
  return planExtrude(name, M.print, s, y0, h);
}

TARGET = caseBase;
planExtrude('case_base_floor', M.print, roundedRect(OX * 2, OZ * 2, POST_R), FLOOR_Y, FLOOR_T);
const WALL_Y = FLOOR_Y + FLOOR_T, WALL_H = LEDGE - WALL_Y;
['left', 'right'].forEach((s, i) => {
  const sgn = i ? 1 : -1;
  box('case_base_side_wall_' + s, M.print, (OX - POST_R) * 2, WALL_H, WALL, 0, WALL_Y, sgn * (OZ - WALL / 2), true);
  box('case_base_pcb_rail_' + s, M.print, L - 2, GAP, 1.1, 0, WALL_Y, sgn * (IZ - 0.55), true);
  box('case_base_rim_side_' + s, M.print, (OX - POST_R) * 2, LID_T, RIM_T, 0, LEDGE, sgn * (OZ - RIM_T / 2), true);
});
[[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([a, b], i) => {
  cornerPost(a, b, WALL_Y, WALL_H, 'case_base_corner_post_' + (i + 1));
  cornerPost(a, b, LEDGE, LID_T, 'case_base_rim_corner_' + (i + 1), POST_R, POST_R - RIM_T);
});

function endWall(side, ports) {
  const x = SLOT_X * side, tag = side < 0 ? 'host' : 'out';
  const inner = (OZ - POST_R) * 2;
  box('case_base_end_wall_' + tag + '_lower', M.print, WALL, PORT_Y0 - WALL_Y, inner, x, WALL_Y, 0, true);
  box('case_base_rim_end_' + tag, M.print, RIM_T, LID_T, inner, (OX - RIM_T / 2) * side, LEDGE, 0, true);
  const edges = [-(OZ - POST_R)];
  ports.forEach(pz => edges.push(pz - PORT_W / 2, pz + PORT_W / 2));
  edges.push(OZ - POST_R);
  for (let i = 0; i < edges.length; i += 2) {
    const a = edges[i], b = edges[i + 1];
    if (b - a < 0.05) continue;
    box('case_base_end_wall_' + tag + '_pillar_' + (i / 2 + 1), M.print, WALL, PORT_H, b - a, x, PORT_Y0, (a + b) / 2, true);
  }
}
endWall(-1, [0]);
endWall(1, [-PORT_Z, PORT_Z]);

HOLES.forEach((h, i) => {
  const s = circlePath(h.x, -h.z, 2.3);
  s.holes.push(circlePath(h.x, -h.z, 0.85, THREE.Path, true));
  planExtrude('case_base_screw_boss_' + (i + 1), M.print, s, WALL_Y, GAP);
});
box('case_base_out_support_rib', M.print, 3.0, GAP, 16, 27.5, WALL_Y, 0, true);

/* -------------------------------------------- PCB top panel (2-layer, ENIG) */
TARGET = caseLid;
function lidSlab(name, mat, y0, thick, shrink = 0) {
  const s = roundedRect(LX - shrink, LZ - shrink, Math.max(0.3, LR - shrink / 2));
  const hole = (x, z, r) => { const p = new THREE.Path(); p.absarc(x, -z, r, 0, Math.PI * 2, true); s.holes.push(p); };
  BTN.forEach(([x, z]) => hole(x, z, 1.9));
  HOLES.forEach(h => hole(h.x, h.z, 1.15));
  for (let i = 0; i < 8; i++) hole(LED_X(i), LED_Z, 0.75);
  return planExtrude(name, mat, s, y0, thick);
}
[
  ['lid_soldermask_bottom', M.mask,   0.000, 0.025, 0],
  ['lid_copper_bottom',     M.copper, 0.025, 0.035, 0.02],
  ['lid_fr4_core',          M.fr4,    0.060, 1.480, 0.02],
  ['lid_copper_top',        M.copper, 1.540, 0.035, 0.02],
  ['lid_soldermask_top',    M.mask,   1.575, 0.025, 0]
].forEach(([n, m, y, t, s]) => lidSlab(n, m, LEDGE + y, t, s));

// ENIG annular rings around every opening — the holes stay open
BTN.forEach(([x, z, ch]) => annulus('lid_pad_ring_sw_' + ch, M.gold, 2.55, 1.9, x, LID_TOP - 0.006, z));
HOLES.forEach((h, i) => annulus('lid_pad_ring_screw_' + (i + 1), M.gold, 1.8, 1.15, h.x, LID_TOP - 0.006, h.z));
for (let i = 0; i < 8; i++) annulus('lid_pad_ring_led_' + (i + 1), M.gold, 1.05, 0.75, LED_X(i), LID_TOP - 0.006, LED_Z);

const lidSilk = silkPlane('silkscreen_lid_top', LX, LZ, a => {
  a.text('USB PWR HUB', -29.8, -4.4, 78, 'left');
  a.ctx.lineWidth = 5;
  a.line(-29.8, -2.9, -12.0, -2.9);
  a.ctx.lineWidth = 7;
  a.text('2CH SWITCHED USB-C 2.0 HS · PPK2 µA→A', -29.8, -1.6, 42, 'left');
  a.text('6 LAYER / 0201 / JLCPCB · REV A', -29.8, 0.1, 42, 'left');
  a.text('◀ HOST', -29.8, 2.9, 52, 'left');
  a.text('OUT A ▶', 29.9, 4.6, 52, 'right');
  a.text('OUT B ▶', 29.9, -4.6, 52, 'right');
  a.text('SW1 + SW2  3s → BOOTSEL / DFU', -0.6, 1.4, 42, 'left');

  BTN.forEach(([bx, bz]) => {
    const s = bz > 0 ? 1 : -1, n = bz > 0 ? 1 : 2, port = bz > 0 ? 'A' : 'B';
    a.circle(bx, bz, 2.95);
    a.text('SW' + n, bx - 3.9, bz, 52, 'right');
    a.text('PORT ' + port, bx + 4.2, bz - s * 2.9, 56, 'left');
    a.text('TAP · 電源 ON / OFF', bx + 4.2, bz - s * 1.0, 42, 'left');
    a.text('HOLD 2s · レンジ AUTO / 固定', bx + 4.2, bz + s * 0.7, 42, 'left');
    a.text('DOUBLE · ゼロ点校正', bx + 4.2, bz + s * 2.4, 42, 'left');
  });

  ['PWR', '3V3', 'LNK', 'ACT', 'A ON', 'A OC', 'B ON', 'B OC'].forEach((t, i) =>
    a.text(t, LED_X(i), LED_Z + (i % 2 ? 3.1 : 1.6), 42));
  a.text('STATUS', -20.6, LED_Z, 52, 'right');
  a.ctx.lineWidth = 5;
  a.line(-19.9, LED_Z + 0.9, -19.9, LED_Z - 0.9);
}, 52);
lidSilk.position.y = LID_TOP + 0.004; caseLid.add(lidSilk);

BTN.forEach(([bx, bz, ch]) => {
  disc('case_button_cap_' + ch, M.printAcc, 1.75, 1.4, bx, LID_TOP - 0.3, bz);
  disc('case_button_stem_' + ch, M.printAcc, 1.7, LID_TOP - 3.4, bx, 3.1, bz);
  disc('case_button_retainer_' + ch, M.printAcc, 2.6, 0.9, bx, 3.1, bz);
});

const fasteners = new THREE.Group(); fasteners.name = 'm2_screws';
root.add(fasteners);
HOLES.forEach((h, i) => {
  const head = new THREE.Mesh(new THREE.CylinderGeometry(1.9, 1.9, 1.25, 24), M.screw);
  head.name = 'm2_screw_' + (i + 1) + '_head';
  head.position.set(h.x, LID_TOP + 0.575, h.z); fasteners.add(head);
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 0.95, 8.0, 20), M.screw);
  shaft.name = 'm2_screw_' + (i + 1) + '_shaft';
  shaft.position.set(h.x, LID_TOP - 4.0, h.z); fasteners.add(shaft);
});

/* ------------------------------------------------------------------- views  */
TARGET = board;
stage.setObject(root);

const VIEWS = {
  board:     () => { caseBase.visible = caseLid.visible = fasteners.visible = false; },
  assembled: () => { caseBase.visible = caseLid.visible = fasteners.visible = true; caseLid.position.y = 0; caseBase.position.y = 0; },
  exploded:  () => { caseBase.visible = caseLid.visible = true; fasteners.visible = false; caseLid.position.y = 13; caseBase.position.y = -7; }
};
function setView(mode) {
  VIEWS[mode]();
  document.querySelectorAll('#views button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === mode)));
}
document.querySelectorAll('#views button').forEach(b => b.addEventListener('click', () => setView(b.dataset.view)));
setView('exploded');
