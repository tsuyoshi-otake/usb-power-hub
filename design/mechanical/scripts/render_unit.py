"""Realistic pictures of the assembled unit, for Blender 5.x (Cycles).

Run from the repository root, after make_enclosure.py and make_lid.py:

  "<Blender 5.2>/blender.exe" -b --python design/mechanical/scripts/render_unit.py -- \
      --kicad-cli "<KiCad 9.0>/bin/kicad-cli.exe" [--shots hero,low,back,top]
      [--res 1920x1080] [--samples 400] [--out DIR]

and writes design/mechanical/reports/UsbPowerHub_Enclosure_Rev0.5_Render<Shot>.jpg

It reads the enclosure's STL files and their placements from the manifest that
make_enclosure.py wrote, the lid's place from the lid interface, and the lid board itself as
a GLB file that kicad-cli exports from design/mechanical/lid/ into a temporary directory.

What the pictures are: the generated solids and the generated lid board, in the colour the
documents name (matte black: Enclosure E2, Lid K7), under studio lights.

What they are not: evidence. Nothing is printed. Drawn here, and not design data: the screws,
the receptacles, the two lit LED windows (D10 and D12, their positions typed in below), the
main board as a plain green slab, the layer lines, the floor and the lights. A picture is not
byte-reproducible (GPU path tracing with a denoiser), and no checker reads it:
check_enclosure.py's E16 covers render_enclosure.py's PNG files only.
"""
import argparse
import json
import math
import pathlib
import subprocess
import sys
import tempfile

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import enclosure_spec as spec  # noqa: E402  (pure Python; the revision's one home)

MM = 0.001
SHOTS = ("hero", "low", "back", "top")

# matte black, as the documents name it (Enclosure E2, Lid K7); the rest is the picture's own
CASE = (0.008, 0.008, 0.009)
MASK = (0.007, 0.007, 0.008)
MASK_ROUGH = 0.70
SCREW = ((0.030, 0.030, 0.032), 0.42)
FLOOR = (0.46, 0.46, 0.47)
WORLD = ((0.30, 0.31, 0.33), 0.45)
LIGHT = 0.85


def args_after_dashes():
    p = argparse.ArgumentParser()
    p.add_argument("--kicad-cli", required=True, help="KiCad 9.0's kicad-cli")
    p.add_argument("--out", type=pathlib.Path, default=spec.REPORTS)
    p.add_argument("--shots", default=",".join(SHOTS))
    p.add_argument("--res", default="1920x1080")
    p.add_argument("--samples", type=int, default=400)
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:])


def export_lid(kicad_cli, directory):
    """The lid board as KiCad draws it in 3D: mask, legend, pads and the bare windows."""
    glb = pathlib.Path(directory) / "lid.glb"
    board = spec.MECH / "lid" / "usb-power-hub-lid.kicad_pcb"
    subprocess.run([kicad_cli, "pcb", "export", "glb", "--force", "--include-silkscreen",
                    "--include-soldermask", "--include-zones", "--include-pads", "--include-tracks",
                    "-o", str(glb), str(board)], check=True, timeout=300)
    return glb


# ---------------------------------------------------------------- materials

def new_material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL" and n.type != "BSDF_PRINCIPLED":
            nt.nodes.remove(n)
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    return m, nt, bsdf


def set_in(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def simple(name, color, rough, metallic=0.0, coat=0.0, emission=None, strength=0.0):
    m, nt, bsdf = new_material(name)
    set_in(bsdf, "Base Color", (*color, 1.0))
    set_in(bsdf, "Roughness", rough)
    set_in(bsdf, "Metallic", metallic)
    set_in(bsdf, "Coat Weight", coat)
    if emission is not None:
        set_in(bsdf, "Emission Color", (*emission, 1.0))
        set_in(bsdf, "Emission Strength", strength)
    return m


def fdm_plastic(name, color, layer=0.2, line=0.45):
    """Matte printed plastic: layer lines on the walls, extrusion lines on flat faces."""
    m, nt, bsdf = new_material(name)
    N, L = nt.nodes, nt.links
    set_in(bsdf, "Base Color", (*color, 1.0))
    set_in(bsdf, "Roughness", 0.52)
    set_in(bsdf, "Sheen Weight", 0.05)

    coord = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(coord.outputs["Object"], sep.inputs[0])  # mm: the meshes are in mm, scaled by the object

    def wave(src, period):
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 2 * math.pi / period
        L.new(src, mul.inputs[0])
        sin = N.new("ShaderNodeMath"); sin.operation = "SINE"
        L.new(mul.outputs[0], sin.inputs[0])
        # round the wave towards a bead's profile: |sin| gives valleys between beads
        ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"
        L.new(sin.outputs[0], ab.inputs[0])
        return ab.outputs[0]

    walls = wave(sep.outputs["Z"], layer * 2)       # |sin| halves the period
    add = N.new("ShaderNodeMath"); add.operation = "ADD"
    L.new(sep.outputs["X"], add.inputs[0]); L.new(sep.outputs["Y"], add.inputs[1])
    flats = wave(add.outputs[0], line * 2 * math.sqrt(2))

    geo = N.new("ShaderNodeNewGeometry")
    nsep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["True Normal"], nsep.inputs[0])
    nz = N.new("ShaderNodeMath"); nz.operation = "ABSOLUTE"
    L.new(nsep.outputs["Z"], nz.inputs[0])
    flat = N.new("ShaderNodeMath"); flat.operation = "GREATER_THAN"
    flat.inputs[1].default_value = 0.9
    L.new(nz.outputs[0], flat.inputs[0])
    mix = N.new("ShaderNodeMix"); mix.data_type = "FLOAT"
    L.new(flat.outputs[0], mix.inputs["Factor"])
    L.new(walls, mix.inputs[2]); L.new(flats, mix.inputs[3])

    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.5
    noise.inputs["Detail"].default_value = 3.0
    L.new(coord.outputs["Object"], noise.inputs["Vector"])
    ramp = N.new("ShaderNodeMapRange")
    ramp.inputs["To Min"].default_value = 0.46
    ramp.inputs["To Max"].default_value = 0.60
    L.new(noise.outputs["Fac"], ramp.inputs["Value"])
    L.new(ramp.outputs["Result"], bsdf.inputs["Roughness"])

    bevel = N.new("ShaderNodeBevel")
    bevel.samples = 6
    bevel.inputs["Radius"].default_value = 0.25 * MM
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.035 * MM
    L.new(mix.outputs["Result"], bump.inputs["Height"])
    L.new(bevel.outputs["Normal"], bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def solder_mask(name, color, rough):
    m, nt, bsdf = new_material(name)
    N, L = nt.nodes, nt.links
    set_in(bsdf, "Base Color", (*color, 1.0))
    set_in(bsdf, "Roughness", rough)
    set_in(bsdf, "Coat Weight", 0.0)   # a matte mask has no gloss coat
    coord = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9000.0   # the GLB is in metres: about 0.1 mm grain
    noise.inputs["Detail"].default_value = 2.0
    L.new(coord.outputs["Object"], noise.inputs["Vector"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.01 * MM
    L.new(noise.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def lit_window(name, center_mm, color, strength):
    """Bare FR-4 over an LED: straw-coloured laminate with a soft glow round the LED."""
    m, nt, bsdf = new_material(name)
    N, L = nt.nodes, nt.links
    set_in(bsdf, "Base Color", (0.10, 0.13, 0.06, 1.0))
    set_in(bsdf, "Roughness", 0.45)
    coord = N.new("ShaderNodeTexCoord")
    sub = N.new("ShaderNodeVectorMath"); sub.operation = "DISTANCE"
    sub.inputs[1].default_value = (*center_mm, 0.0)
    L.new(coord.outputs["Object"], sub.inputs[0])
    fall = N.new("ShaderNodeMapRange")
    fall.interpolation_type = "SMOOTHSTEP"
    fall.inputs["From Min"].default_value = 0.2
    fall.inputs["From Max"].default_value = 2.6
    fall.inputs["To Min"].default_value = 1.0
    fall.inputs["To Max"].default_value = 0.03
    L.new(sub.outputs["Value"], fall.inputs["Value"])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    L.new(fall.outputs["Result"], mul.inputs[0])
    set_in(bsdf, "Emission Color", (*color, 1.0))
    L.new(mul.outputs[0], bsdf.inputs["Emission Strength"])
    return m


# ---------------------------------------------------------------- geometry

def link(ob, root):
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = root
    return ob


def mesh_object(name, verts, faces, root, material, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    return link(ob, root)


def box(name, x0, y0, z0, x1, y1, z1, root, material, bevel=0.0):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_object(name, v, f, root, material)
    if bevel > 0:
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    return ob


def stadium(w, h, n=24):
    """Outline of a rounded slot w x h (full-radius ends) in x-z, counter-clockwise."""
    r = h / 2
    pts = []
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        pts.append((w / 2 - r + r * math.cos(a), r * math.sin(a)))
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n
        pts.append((-(w / 2 - r) + r * math.cos(a), r * math.sin(a)))
    return pts


def receptacle(name, x, y_mouth, direction, root, mats):
    """A USB-C receptacle: steel shell 8.94 x 3.26 x 7.35 mm, tongue with contacts.

    direction is +1 when the body runs towards +y from the mouth (front edge), -1 at the back.
    """
    w, h, depth, wall = 8.94, 3.26, 7.35, 0.25
    zc = h / 2
    outer = stadium(w, h)
    inner = stadium(w - 2 * wall, h - 2 * wall)
    n = len(outer)
    ya, yb = y_mouth, y_mouth + direction * depth
    yi = y_mouth + direction * (depth - 0.6)
    verts, faces = [], []
    for ring, yy in ((outer, ya), (outer, yb), (inner, ya), (inner, yi)):
        verts += [(x + px, yy, zc + pz) for px, pz in ring]

    def quad(a, b, c, d):
        faces.append((a, b, c, d) if direction > 0 else (d, c, b, a))

    for i in range(n):
        j = (i + 1) % n
        quad(i, j, n + j, n + i)                       # outside
        quad(2 * n + j, 2 * n + i, 3 * n + i, 3 * n + j)  # inside
        quad(j, i, 2 * n + i, 2 * n + j)               # lip at the mouth
    faces.append(tuple(range(n, 2 * n)) if direction > 0 else tuple(reversed(range(n, 2 * n))))
    faces.append(tuple(reversed(range(3 * n, 4 * n))) if direction > 0 else tuple(range(3 * n, 4 * n)))
    shell = mesh_object(name + "_shell", verts, faces, root, mats["steel"], smooth=True)
    split = shell.modifiers.new("split", "EDGE_SPLIT")
    split.split_angle = math.radians(40)

    t0 = y_mouth + direction * 0.95
    t1 = y_mouth + direction * (depth - 0.6)
    box(name + "_tongue", x - 3.35, min(t0, t1), zc - 0.35, x + 3.35, max(t0, t1), zc + 0.35,
        root, mats["tongue"], bevel=0.12)
    c0 = y_mouth + direction * 1.35
    c1 = y_mouth + direction * 4.6
    for k in range(12):
        cx = x - 2.75 + 0.5 * k
        for zz in (zc + 0.35, zc - 0.37):
            box(f"{name}_pin{k}", cx - 0.13, min(c0, c1), zz, cx + 0.13, max(c0, c1), zz + 0.02,
                root, mats["gold"])


def pan_screw(name, x, y, z, root, material, turn=0.0):
    """An M2 pan head with a cross recess, standing on z."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=1.9, radius2=1.9, depth=1.3)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.65))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    link(ob, root)
    ob.location = (x, y, z)
    ob.rotation_euler = (0, 0, math.radians(turn))
    bev = ob.modifiers.new("bevel", "BEVEL")
    bev.width = 0.55
    bev.segments = 6
    bev.limit_method = "ANGLE"
    for k, ang in enumerate((0.0, math.pi / 2)):
        cb = bmesh.new()
        geom = bmesh.ops.create_cube(cb, size=1.0)
        vs = geom["verts"]
        bmesh.ops.scale(cb, verts=vs, vec=(2.3, 0.42, 1.2))
        bmesh.ops.rotate(cb, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(ang, 3, "Z"))
        bmesh.ops.translate(cb, verts=vs, vec=(0, 0, 1.3))
        cutter_me = bpy.data.meshes.new(f"{name}_cut{k}")
        cb.to_mesh(cutter_me)
        cb.free()
        cutter = bpy.data.objects.new(f"{name}_cut{k}", cutter_me)
        link(cutter, ob)
        cutter.hide_render = True
        cutter.hide_viewport = False
        cutter.display_type = "WIRE"
        boo = ob.modifiers.new(f"recess{k}", "BOOLEAN")
        boo.operation = "DIFFERENCE"
        boo.solver = "EXACT"
        boo.object = cutter
    split = ob.modifiers.new("split", "EDGE_SPLIT")
    split.split_angle = math.radians(35)
    return ob


def import_stl(path, name, m34, root, material):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=str(path))
    ob = (set(bpy.data.objects) - before).pop()
    ob.name = name
    m = Matrix((m34[0], m34[1], m34[2], (0, 0, 0, 1)))
    ob.parent = root
    ob.matrix_local = m
    ob.data.materials.clear()
    ob.data.materials.append(material)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    split = ob.modifiers.new("split", "EDGE_SPLIT")
    split.split_angle = math.radians(28)
    return ob


def import_lid(path, lid_z_mm, mats):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = set(bpy.data.objects) - before
    tops = [ob for ob in new if ob.parent is None]
    for ob in tops:
        # KiCad sheet (xk, yk) -> board frame (xk - 50, 122 - yk); the board's underside is z = 0
        ob.matrix_world = Matrix.Translation((-50 * MM, 122 * MM, lid_z_mm * MM)) @ ob.matrix_world
    for ob in new:
        if ob.type != "MESH":
            continue
        for slot in ob.material_slots:
            src = slot.material
            bsdf = src.node_tree.nodes.get("Principled BSDF") if src and src.node_tree else None
            col = tuple(bsdf.inputs["Base Color"].default_value)[:3] if bsdf else (0, 0, 0)
            if col[0] > 0.9 and col[1] > 0.9:
                slot.material = mats["silk"]
            elif col[1] > col[0] * 1.5 and col[1] > col[2]:
                slot.material = mats["mask"]
            elif col[2] < 0.05 and col[0] > 0.5:
                slot.material = mats["copper"]
            else:
                slot.material = mats["fr4"]
    return new


def cove(material):
    """A floor that curves up into a back wall, so that no horizon shows."""
    prof = [(-3.0, 0.0)]
    r = 0.7
    for i in range(25):
        a = -math.pi / 2 + (math.pi / 2) * i / 24
        prof.append((1.2 + r * math.cos(a), r + r * math.sin(a)))
    prof.append((1.2 + r, 3.0))
    verts, faces = [], []
    for xx in (-4.0, 4.0):
        verts += [(xx, py, pz) for py, pz in prof]
    n = len(prof)
    for i in range(n - 1):
        faces.append((i, n + i, n + i + 1, i + 1))
    me = bpy.data.meshes.new("cove")
    me.from_pydata(verts, [], faces)
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new("cove", me)
    ob.data.materials.append(material)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------- scene

def area_light(name, location, target, size, power, color=(1, 1, 1), size_y=None):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.color = color
    data.shape = "RECTANGLE" if size_y else "SQUARE"
    data.size = size
    if size_y:
        data.size_y = size_y
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    return ob


def camera(name, location, target, lens, fstop, focus=None):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36
    data.clip_start = 0.01
    data.clip_end = 20
    data.dof.use_dof = True
    data.dof.aperture_fstop = fstop
    data.dof.focus_distance = (Vector(focus or target) - Vector(location)).length
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    return ob


def setup_render(scene, res, samples):
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            used = [d for d in prefs.devices if d.type == kind]
            if used:
                for d in prefs.devices:
                    d.use = d.type == kind
                scene.cycles.device = "GPU"
                print("render device", kind, [d.name for d in used])
                break
        except TypeError:
            continue
    w, h = (int(v) for v in res.lower().split("x"))
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.quality = 92
    scene.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue
    scene.render.film_transparent = False


def main():
    a = args_after_dashes()
    shots = a.shots.split(",")
    unknown = [name for name in shots if name not in SHOTS]
    if unknown:
        sys.exit(f"unknown shot {unknown}: one of {SHOTS}")
    a.out.mkdir(parents=True, exist_ok=True)
    asm = spec.ASSEMBLY
    manifest = json.loads((asm / spec.MANIFEST).read_text("utf-8"))
    lidif = json.loads((asm / f"{spec.PREFIX}LidInterface.json").read_text("utf-8"))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    setup_render(scene, a.res, a.samples)

    mats = dict(
        case=fdm_plastic("case", CASE),
        steel=simple("steel", (0.62, 0.62, 0.63), 0.28, metallic=1.0),
        screw=simple("screw", SCREW[0], SCREW[1], metallic=1.0),
        tongue=simple("tongue", (0.012, 0.012, 0.013), 0.4),
        gold=simple("gold", (0.83, 0.62, 0.25), 0.3, metallic=1.0),
        silk=simple("silk", (0.86, 0.86, 0.84), 0.6),
        copper=simple("copper", (0.72, 0.42, 0.22), 0.35, metallic=1.0),
        fr4=simple("fr4", (0.13, 0.11, 0.05), 0.55),
        mask=solder_mask("mask", MASK, MASK_ROUGH),
        board=simple("board", (0.010, 0.085, 0.035), 0.3, coat=0.3),
        floor=simple("floor", FLOOR, 0.65),
    )

    root = bpy.data.objects.new("assembly_mm", None)
    scene.collection.objects.link(root)
    root.scale = (MM, MM, MM)

    for piece in manifest["pieces"]:
        for i, m34 in enumerate(piece["to_assembly"]):
            import_stl(asm / piece["file"], f"{piece['name']}{i}", m34, root, mats["case"])

    box("main_board", 0, 0, -1.6, 100, 72, 0, root, mats["board"])
    lid_z = lidif["underside_above_board"]
    lid_top = lid_z + lidif["thickness"]
    with tempfile.TemporaryDirectory() as tmp:
        import_lid(export_lid(a.kicad_cli, tmp), lid_z, mats)

    for hole in lidif["holes"]:
        if hole["kind"] == "screw":
            turn = {"H1": 23.0, "H2": 71.0, "H3": 118.0, "H4": 49.0}[hole["ref"]]
            pan_screw("screw_" + hole["ref"], hole["x"], hole["y"], lid_top, root, mats["screw"], turn)

    leds = {"D10": (29.75, 10.5), "D12": (70.25, 10.5)}  # the green LED of each port
    for win in lidif["windows"]:
        x0, y0, x1, y1 = win["rect"]
        ref = next(r for r in win["refs"] if r in leds)
        cx, cy = leds[ref]
        mat = lit_window("window_" + ref, (cx - x0, cy - y0), (0.02, 1.0, 0.08), 9.0)
        ob = mesh_object("window_" + ref, [(0, 0, 0), (x1 - x0, 0, 0), (x1 - x0, y1 - y0, 0), (0, y1 - y0, 0)],
                         [(0, 1, 2, 3)], root, mat)
        ob.location = (x0, y0, lid_top + 0.012)

    for port in lidif["ports"]:
        front = port["edge"] == "front"
        receptacle(port["ref"], port["x"], -1.06 if front else 73.06, 1 if front else -1, root, mats)

    floor_z = -7.1 * MM
    cv = cove(mats["floor"])
    cv.location = (0.05, 0.0, floor_z)

    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*WORLD[0], 1.0)
    bg.inputs["Strength"].default_value = WORLD[1]
    scene.world = world

    c = Vector((0.050, 0.036, 0.008))
    views = {
        "hero": dict(cam=(-0.105, -0.255, 0.185), target=(0.046, 0.026, 0.006), lens=72, fstop=13.0,
                     focus=(0.045, 0.012, 0.018)),
        "back": dict(cam=(0.215, 0.315, 0.150), target=(0.052, 0.042, 0.006), lens=72, fstop=13.0,
                     focus=(0.050, 0.062, 0.014)),
        "low": dict(cam=(-0.050, -0.185, 0.072), target=(0.034, 0.008, 0.009), lens=85, fstop=7.1,
                    focus=(0.0315, 0.002, 0.018)),
        "top": dict(cam=(0.050, -0.085, 0.420), target=(0.050, 0.033, 0.012), lens=85, fstop=11.0,
                    focus=(0.050, 0.030, 0.0206)),
    }
    for name in shots:
        shot = views[name]
        for ob in [o for o in scene.objects if o.type in ("LIGHT", "CAMERA")]:
            bpy.data.objects.remove(ob, do_unlink=True)
        cam = camera("cam_" + name, shot["cam"], shot["target"], shot["lens"], shot["fstop"], shot["focus"])
        scene.camera = cam
        view = (Vector(shot["cam"]) - c)
        side = Vector((-view.y, view.x, 0)).normalized()      # to the camera's left
        back = Vector((-view.x, -view.y, 0)).normalized()     # away from the camera
        up = Vector((0, 0, 1))
        dim = LIGHT
        area_light("key", c + side * 0.40 - back * 0.22 + up * 0.50, c, 0.50, 9.0 * dim, (1.0, 0.97, 0.93))
        area_light("top", c - back * 0.06 + up * 0.70, c, 0.70, 7.0 * dim, (0.95, 0.97, 1.0))
        area_light("strip", c - side * 0.10 + back * 0.62 + up * 0.36, c + back * 0.02, 0.60, 4.0 * dim,
                   (0.90, 0.95, 1.0), size_y=0.10)
        area_light("rim", c - side * 0.48 + back * 0.30 + up * 0.20, c, 0.25, 6.0 * dim, (0.85, 0.92, 1.0))
        area_light("fill", c - side * 0.35 - back * 0.45 + up * 0.12, c, 0.50, 1.2 * dim)
        scene.render.filepath = str(a.out / f"{spec.PREFIX}Render{name.capitalize()}.jpg")
        bpy.ops.render.render(write_still=True)
        print("wrote", scene.render.filepath)


main()
