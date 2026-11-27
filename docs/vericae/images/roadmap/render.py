"""Render the adjacent layers of roadmap.json with the Python standard library.

From any directory, run: python /path/to/roadmap/render.py
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import textwrap
import unicodedata
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
STAGES = ("available", "development", "planned")  # Lowest to highest uncertainty.
MARGIN, SIBLING_GAP, ROW_GAP = 24, 16, 46
NAME_SIZE, DETAIL_SIZE = 18, 15


def text_width(value, size):
    """Estimate proportional text width for layout without requiring installed fonts."""
    units = 0
    for char in value:
        if unicodedata.east_asian_width(char) in ("W", "F"):
            units += 1
        elif char in " .,:;!'|ijlIt":
            units += 0.36
        elif char in "MWmw@%":
            units += 0.95
        elif char.isupper():
            units += 0.73
        else:
            units += 0.61
    return units * size


def node_lines(node, statuses):
    lines = [(node["name"], NAME_SIZE, "name")]
    if node.get("detail"):
        lines.extend((line, DETAIL_SIZE, "detail") for line in textwrap.wrap(node["detail"], 38))
    stage = node["status"]
    label = node.get("statusLabels", {}).get(stage, statuses[stage]["label"])
    lines.append((label, DETAIL_SIZE, "status"))
    return lines


def column_centers(rows, edges, widths):
    """Lay out branches away from the narrowest layer, centering parents over children.

    A shared child reserves space in one branch. All declared edges are drawn later,
    including its additional parents. Nodes without a parent get their own column.
    """
    hub = min(range(len(rows)), key=lambda i: (len(rows[i]), abs(i - (len(rows) - 1) / 2)))
    parents, children = defaultdict(list), defaultdict(list)
    for edge in edges:
        parents[edge["to"]].append(edge["from"])
        children[edge["from"]].append(edge["to"])

    roots = list(rows[hub])
    branches = defaultdict(lambda: [[], []])
    for side, indices, towards_hub in (
        (0, range(hub - 1, -1, -1), children),
        (1, range(hub + 1, len(rows)), parents),
    ):
        for i in indices:
            for node in rows[i]:
                neighbors = towards_hub[node]
                if neighbors:
                    branches[neighbors[0]][side].append(node)
                else:
                    roots.append(node)

    spans = {}

    def group_width(group):
        return sum(spans[node] for node in group) + max(0, len(group) - 1) * SIBLING_GAP

    def measure(node):
        span = widths[node]
        for group in branches[node]:
            for child in group:
                measure(child)
            span = max(span, group_width(group))
        spans[node] = span

    centers = {}

    def place(group, left):
        for node in group:
            center = left + spans[node] / 2
            centers[node] = center
            for sub_group in branches[node]:
                place(sub_group, center - group_width(sub_group) / 2)
            left += spans[node] + SIBLING_GAP

    for root in roots:
        measure(root)
    place(roots, 0)
    return centers, group_width(roots)


def tag(parent, name, **attrs):
    return ET.SubElement(parent, name, {key.replace("_", "-"): str(value) for key, value in attrs.items()})


def label(parent, value, x, y, size, color, **attrs):
    tag(parent, "text", x=x, y=y, font_size=size, fill=color, **attrs).text = value


def stroke(status, theme_name):
    color = status["color"]
    if isinstance(color, dict):
        color = color[theme_name]
    attrs = {"stroke": color, "stroke_width": 1.8, "stroke_linecap": "round"}
    if status["dash"]:
        attrs["stroke_dasharray"] = status["dash"]
    return attrs


def ports(edges, centers, widths, end, opposite):
    """Spread adjacent connections across each card in the order of the other ends."""
    groups = defaultdict(list)
    for edge in edges:
        groups[edge[end]].append(edge[opposite])
    result = {}
    for node, neighbors in groups.items():
        ordered = sorted(neighbors, key=centers.get)
        spread = min(widths[node] * 0.66, (len(ordered) - 1) * 38)
        for i, neighbor in enumerate(ordered):
            offset = spread * (i / max(1, len(ordered) - 1) - 0.5)
            result[node, neighbor] = round(centers[node] + offset, 1)
    return result


def render(config, theme_name):
    theme, statuses = config["themes"][theme_name], config["statuses"]
    layers, edges = config["layers"], config["edges"]
    nodes = {node["id"]: node for node in config["nodes"]}
    indices = {layer["id"]: i for i, layer in enumerate(layers)}
    rows = [[] for _ in layers]
    if not layers or len(indices) != len(layers) or len(nodes) != len(config["nodes"]):
        raise ValueError("Supply a nonempty set of layers and unique layer and node IDs")
    for node in nodes.values():
        if node["status"] not in STAGES:
            raise ValueError(f"Unknown integration status: {node['status']}")
        rows[indices[node["layer"]]].append(node["id"])
    for edge in edges:
        start, end = nodes[edge["from"]], nodes[edge["to"]]
        if indices[end["layer"]] != indices[start["layer"]] + 1:
            raise ValueError(f"Edges must link consecutive layers from top to bottom: {edge}")

    lines = {key: node_lines(node, statuses) for key, node in nodes.items()}
    widths = {n: max(118, round(max(text_width(s, size) for s, size, _ in content)) + 28)
              for n, content in lines.items()}
    centers, branch_width = column_centers(rows, edges, widths)
    layer_labels = [textwrap.wrap(layer["label"], 16, break_long_words=False) for layer in layers]
    gutter = max((text_width(s, 15) for words in layer_labels for s in words), default=0) + 21

    legend_widths = [44 + text_width(statuses[key]["label"], DETAIL_SIZE) for key in STAGES]
    header_width = max(text_width(config["title"], 29), sum(legend_widths))
    width = round(max(gutter + branch_width, header_width) + 2 * MARGIN)
    offset = (width + gutter - branch_width) / 2
    centers = {n: round(x + offset, 1) for n, x in centers.items()}
    row_y, heights = [], []
    top = 119
    for row, words in zip(rows, layer_labels):
        tallest = max((len(lines[n]) for n in row), default=1)
        height = max(22 + 22 * tallest, 25 + 20 * len(words))
        row_y.append(top)
        heights.append(height)
        top += height + ROW_GAP
    height = top - ROW_GAP + MARGIN
    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg", "width": str(width), "height": str(height),
        "viewBox": f"0 0 {width} {height}", "role": "img", "aria-labelledby": "title desc",
        "font-family": "Arial, Helvetica, sans-serif",
    })
    tag(svg, "title", id="title").text = config["title"]
    tag(svg, "desc", id="desc").text = config["description"]
    tag(svg, "rect", x=1, y=1, width=width-2, height=height-2, rx=13,
        fill=theme["background"], stroke=theme["rule"])
    label(svg, config["title"], MARGIN, 47, 29, theme["ink"], font_weight=700)
    x = MARGIN
    for key, length in zip(STAGES, legend_widths):
        tag(svg, "path", d=f"M{x:g} 76h23", fill="none", **stroke(statuses[key], theme_name))
        label(svg, statuses[key]["label"], round(x + 31, 1), 81, DETAIL_SIZE, theme["muted"])
        x += length
    tag(svg, "path", d=f"M{MARGIN} 98H{width-MARGIN}", stroke=theme["rule"])

    outputs = ports(edges, centers, widths, "from", "to")
    inputs = ports(edges, centers, widths, "to", "from")
    for edge in edges:
        a, b = edge["from"], edge["to"]
        row = indices[nodes[a]["layer"]]
        x1, x2 = outputs[a, b], inputs[b, a]
        y1, y2 = row_y[row] + heights[row], row_y[row + 1]
        middle = (y1 + y2) / 2
        stage = max((nodes[a]["status"], nodes[b]["status"]), key=STAGES.index)
        tag(svg, "path", data_from=a, data_to=b, data_status=stage, fill="none",
            d=f"M{x1:g} {y1}C{x1:g} {middle:g} {x2:g} {middle:g} {x2:g} {y2}",
            **stroke(statuses[stage], theme_name))

    for i, row in enumerate(rows):
        top, h = row_y[i], heights[i]
        mid = top + h / 2
        words = layer_labels[i]
        number_y = mid - 10 * len(words) + 5
        label(svg, f"LAYER {i + 1:02d}", MARGIN, number_y, 11, theme["muted"],
              font_family="Consolas, monospace", font_weight=600, letter_spacing="1.1")
        for j, word in enumerate(words):
            baseline = number_y + 19 + j * 20
            label(svg, word, MARGIN, baseline, 15, theme["muted"], font_weight=600)
        for n in row:
            x, w = centers[n], widths[n]
            stage = nodes[n]["status"]
            group = tag(svg, "g", data_node=n, data_status=stage)
            tag(group, "rect", x=round(x - w / 2, 1), y=top, width=w, height=h, rx=8, fill=theme["panel"],
                **stroke(statuses[stage], theme_name))
            first = mid - (len(lines[n]) - 1) * 11 + 5
            for j, (value, size, kind) in enumerate(lines[n]):
                strong = kind == "name"
                label(group, value, x, first + 22*j, size, theme["ink" if strong else "muted"],
                      text_anchor="middle", font_weight=700 if strong else 400)

    ET.indent(svg, space="  ")
    return ET.tostring(svg, encoding="unicode") + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=HERE / "roadmap.json")
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    outputs = {theme: render(config, theme) for theme in ("light", "dark")}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for theme, svg in outputs.items():
        (args.output_dir / f"roadmap-{theme}.svg").write_text(svg, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
