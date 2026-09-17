"""
Приводит glTF-модель проводника к виду, который ждёт AR-модуль.

Соглашение модуля: ось Y вверх, ноги на y = 0, центр по X и Z в нуле,
лицом к +Z, рост ровно --height (по умолчанию 1.0). Тогда в коде рост
персонажа задаётся одним множителем в метрах, без угадывания габаритов.

Зачем скрипт, а не scaleToUnits в рантайме. Filament считает габариты модели
по исходной иерархии нод, без скиннинга. У моделей со скелетом (почти всё
с Sketchfab) это другая поза: у Шрека габариты без скиннинга 364×275×115
с центром на высоте 137, а нарисованный персонаж — 110×83×35 с ногами
на нуле. Масштабирование по неверной коробке и дало кривую модель в кадре.
Здесь поза считается честно, как её нарисует GPU: Σ вес · (кость · обратная
матрица привязки) · вершина.

Что делает:
  - считает реальные габариты со скиннингом;
  - добавляет корневую ноду с масштабом и сдвигом — геометрия и скелет
    не трогаются, анимации (если они есть) продолжают работать;
  - переводит материалы BLEND в OPAQUE (--keep-blend, чтобы не трогать):
    экспорт из Blender часто ставит BLEND телу целиком, и полупрозрачное
    двустороннее тело рисуется тёмной кашей;
  - выкидывает ноды по имени (--drop), например оторванный от скелета глаз.

Бинарная часть GLB не меняется — переписывается только JSON.

    python tools/normalize_companion.py raw/shrek.glb ar/src/main/assets/companion/shrek.glb --drop Object_4
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942

COMPONENT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NORMALIZE = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

Matrix = list[list[float]]
IDENTITY: Matrix = [[float(r == c) for c in range(4)] for r in range(4)]


def read_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    magic, version, _ = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC or version != 2:
        sys.exit(f"{path}: это не GLB 2.0")
    json_len, json_type = struct.unpack_from("<II", data, 12)
    if json_type != CHUNK_JSON:
        sys.exit(f"{path}: первым чанком должен идти JSON")
    gltf = json.loads(data[20 : 20 + json_len].decode("utf-8"))
    offset = 20 + json_len
    binary = b""
    if offset < len(data):
        bin_len, bin_type = struct.unpack_from("<II", data, offset)
        if bin_type == CHUNK_BIN:
            binary = data[offset + 8 : offset + 8 + bin_len]
    return gltf, binary


def write_glb(path: Path, gltf: dict, binary: bytes) -> None:
    payload = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    payload += b" " * (-len(payload) % 4)  # JSON-чанк добивается пробелами
    binary += b"\x00" * (-len(binary) % 4)  # бинарный — нулями
    total = 12 + 8 + len(payload) + (8 + len(binary) if binary else 0)
    out = bytearray(struct.pack("<III", GLB_MAGIC, 2, total))
    out += struct.pack("<II", len(payload), CHUNK_JSON) + payload
    if binary:
        out += struct.pack("<II", len(binary), CHUNK_BIN) + binary
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out)


def local_matrix(node: dict) -> Matrix:
    if "matrix" in node:
        m = node["matrix"]  # glTF хранит по столбцам
        return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    tx, ty, tz = node.get("translation", [0.0, 0.0, 0.0])
    x, y, z, w = node.get("rotation", [0.0, 0.0, 0.0, 1.0])
    sx, sy, sz = node.get("scale", [1.0, 1.0, 1.0])
    rot = [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]
    return [
        [rot[0][0] * sx, rot[0][1] * sy, rot[0][2] * sz, tx],
        [rot[1][0] * sx, rot[1][1] * sy, rot[1][2] * sz, ty],
        [rot[2][0] * sx, rot[2][1] * sy, rot[2][2] * sz, tz],
        [0.0, 0.0, 0.0, 1.0],
    ]


def multiply(a: Matrix, b: Matrix) -> Matrix:
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def transform_point(m: Matrix, v) -> tuple[float, float, float]:
    x, y, z = v[0], v[1], v[2]
    return (
        m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3],
        m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3],
        m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3],
    )


def read_accessor(gltf: dict, binary: bytes, index: int) -> list[tuple]:
    accessor = gltf["accessors"][index]
    if "sparse" in accessor or "bufferView" not in accessor:
        sys.exit(f"accessor {index}: sparse и пустые accessor не поддержаны")
    view = gltf["bufferViews"][accessor["bufferView"]]
    code, size = COMPONENT[accessor["componentType"]]
    width = WIDTH[accessor["type"]]
    stride = view.get("byteStride", size * width)
    base = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    fmt = "<" + code * width
    scale = NORMALIZE.get(accessor["componentType"]) if accessor.get("normalized") else None
    rows = []
    for i in range(accessor["count"]):
        row = struct.unpack_from(fmt, binary, base + i * stride)
        rows.append(tuple(v / scale for v in row) if scale else row)
    return rows


def world_matrices(gltf: dict, roots: list[int]) -> dict[int, Matrix]:
    nodes = gltf["nodes"]
    result: dict[int, Matrix] = {}

    def walk(index: int, parent: Matrix) -> None:
        result[index] = multiply(parent, local_matrix(nodes[index]))
        for child in nodes[index].get("children", []):
            walk(child, result[index])

    for root in roots:
        walk(root, IDENTITY)
    return result


def posed_bounds(gltf: dict, binary: bytes, roots: list[int]) -> tuple[list[float], list[float]]:
    """Габариты такими, какими их нарисует GPU, со скиннингом."""
    nodes = gltf["nodes"]
    world = world_matrices(gltf, roots)
    low, high = [float("inf")] * 3, [float("-inf")] * 3

    def extend(point) -> None:
        for axis in range(3):
            low[axis] = min(low[axis], point[axis])
            high[axis] = max(high[axis], point[axis])

    for index, matrix in world.items():
        node = nodes[index]
        if "mesh" not in node:
            continue
        skin_joints = None
        if "skin" in node:
            skin = gltf["skins"][node["skin"]]
            inverse = read_accessor(gltf, binary, skin["inverseBindMatrices"]) if "inverseBindMatrices" in skin else None
            skin_joints = []
            for slot, joint in enumerate(skin["joints"]):
                ibm = IDENTITY
                if inverse:
                    m = inverse[slot]
                    ibm = [[m[c * 4 + r] for c in range(4)] for r in range(4)]
                skin_joints.append(multiply(world[joint], ibm))

        for primitive in gltf["meshes"][node["mesh"]]["primitives"]:
            positions = read_accessor(gltf, binary, primitive["attributes"]["POSITION"])
            if skin_joints is None:
                for v in positions:
                    extend(transform_point(matrix, v))
                continue
            joints = read_accessor(gltf, binary, primitive["attributes"]["JOINTS_0"])
            weights = read_accessor(gltf, binary, primitive["attributes"]["WEIGHTS_0"])
            for v, js, ws in zip(positions, joints, weights):
                total = [0.0, 0.0, 0.0]
                for joint, weight in zip(js, ws):
                    if weight:
                        p = transform_point(skin_joints[joint], v)
                        for axis in range(3):
                            total[axis] += weight * p[axis]
                extend(total)

    if low[0] == float("inf"):
        sys.exit("в сцене не нашлось ни одной вершины")
    return low, high


def drop_nodes(gltf: dict, names: list[str]) -> list[str]:
    """Отвязывает ноды от родителей. Сама нода остаётся в массиве: индексы не сдвигаются."""
    nodes = gltf["nodes"]
    wanted = {i for i, n in enumerate(nodes) if n.get("name") in names}
    for node in nodes:
        if "children" in node:
            node["children"] = [c for c in node["children"] if c not in wanted]
    for scene in gltf.get("scenes", []):
        scene["nodes"] = [n for n in scene["nodes"] if n not in wanted]
    return sorted(nodes[i]["name"] for i in wanted)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--height", type=float, default=1.0, help="рост после нормализации, в единицах сцены")
    parser.add_argument("--drop", nargs="*", default=[], help="имена нод, которые убрать из сцены")
    parser.add_argument("--keep-blend", action="store_true", help="не переводить BLEND-материалы в OPAQUE")
    args = parser.parse_args()

    gltf, binary = read_glb(args.source)
    scene_index = gltf.get("scene", 0)
    scene = gltf["scenes"][scene_index]

    dropped = drop_nodes(gltf, args.drop)
    missing = set(args.drop) - set(dropped)
    if missing:
        sys.exit(f"ноды не найдены: {', '.join(sorted(missing))}")

    low, high = posed_bounds(gltf, binary, scene["nodes"])
    height = high[1] - low[1]
    if height <= 0:
        sys.exit("у модели нулевая высота")
    s = args.height / height
    cx, cz = (low[0] + high[0]) / 2, (low[2] + high[2]) / 2

    # Сначала масштаб, потом сдвиг: T · S, записанное по столбцам.
    root = {
        "name": "companion_root",
        "matrix": [s, 0, 0, 0, 0, s, 0, 0, 0, 0, s, 0, -cx * s, -low[1] * s, -cz * s, 1],
        "children": list(scene["nodes"]),
    }
    gltf["nodes"].append(root)
    scene["nodes"] = [len(gltf["nodes"]) - 1]

    opaque = []
    if not args.keep_blend:
        for material in gltf.get("materials", []):
            if material.get("alphaMode") == "BLEND":
                material.pop("alphaMode")
                material.pop("alphaCutoff", None)
                opaque.append(material.get("name", "?"))

    check_low, check_high = posed_bounds(gltf, binary, scene["nodes"])
    write_glb(args.target, gltf, binary)

    def fmt(values) -> str:
        return "[" + ", ".join(f"{v:.3f}" for v in values) + "]"

    print(f"исходные габариты со скиннингом: {fmt(low)} .. {fmt(high)}")
    print(f"множитель {s:.6f}, сдвиг центра по X/Z: {cx:.3f} / {cz:.3f}")
    print(f"после нормализации:              {fmt(check_low)} .. {fmt(check_high)}")
    print(f"убраны ноды: {', '.join(dropped) or 'нет'}")
    print(f"BLEND -> OPAQUE: {', '.join(opaque) or 'нет'}")
    print(f"записано: {args.target} ({args.target.stat().st_size / 1_048_576:.1f} МБ)")


if __name__ == "__main__":
    main()
