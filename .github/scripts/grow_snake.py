"""Make the Platane/snk snake grow: one extra tail segment appears each time a square is eaten.

Usage: python grow_snake.py dist/github-snake.svg dist/github-snake-dark.svg   (edits the files in place)
snk draws a fixed 4-segment snake; segment k follows the head k steps later. Each new segment
copies the last segment's path one more step behind and stays hidden until its square is eaten.
Standard library only, so it runs on the GitHub Actions runner without installs.
"""
import re
import sys

KF = r"@keyframes {}\{{((?:[\d.,%]+\{{[^}}]*\}})*)\}}"


def keyframes(css, name):
    body = re.search(KF.format(re.escape(name)), css).group(1)
    pts = []
    for pcts, x, y in re.findall(r"([\d.,%]+)\{transform:translate\((-?[\d.]+)px,(-?[\d.]+)px\)\}", body):
        pts += [(float(p.rstrip("%")), x, y) for p in pcts.split(",")]
    return sorted(pts)


def grow(svg):
    if "class=\"s s4\"" in svg or "growsnake" in svg:
        return svg  # already grown
    css = svg[svg.index("<style>"):svg.index("</style>")]
    dur = re.search(r"\.s\{[^}]*?(\d+)ms", css).group(1)
    s0, s1, last = keyframes(css, "s0"), keyframes(css, "s1"), keyframes(css, "s3")
    step = next(p for p, x, y in s1 if (x, y) == ("0", "0")) - next(p for p, x, y in s0 if (x, y) == ("0", "0"))
    end = min(p for p, x, y in s0 if p > 50 and (x, y) == (s0[0][1], s0[0][2]))  # loop restart (e.g. 99.3%)
    eats = sorted(float(m) for m in re.findall(r"@keyframes c\w+\{([\d.]+)%", css))
    rules, rects = [], []
    for j, eat in enumerate(eats, 1):
        n = 3 + j
        pts = [(p + j * step, x, y) for p, x, y in last if p + j * step < end]
        frames = "".join(f"{p:.2f}%{{transform:translate({x}px,{y}px)}}" for p, x, y in pts)
        first = pts[0]
        rules.append(f"@keyframes s{n}{{0%{{transform:translate({first[1]}px,{first[2]}px)}}{frames}}}"
                     f".s.s{n}{{animation-name:s{n}}}"
                     f"@keyframes g{n}{{0%,{eat - 0.01:.2f}%{{opacity:0}}{eat:.2f}%,{end - 0.11:.2f}%{{opacity:1}}"
                     f"{end - 0.1:.2f}%,100%{{opacity:0}}}}"
                     f".g{n}{{opacity:0;animation:g{n} {dur}ms linear infinite}}")
        size = max(7.0, 9.9 - 0.15 * j)  # keep tapering gently after snk's own 4 segments
        off = (16 - size) / 2
        rects.append(f'<g class="g{n}"><rect class="s s{n}" x="{off:.1f}" y="{off:.1f}" width="{size:.1f}" '
                     f'height="{size:.1f}" rx="{size / 3:.1f}" ry="{size / 3:.1f}"/></g>')
    svg = svg.replace("</style>", "/* growsnake */" + "".join(rules) + "</style>", 1)
    head = svg.index('<rect class="s s0"')
    return svg[:head] + "".join(reversed(rects)) + svg[head:]  # tail drawn under the head


def demo():  # tiny self-check on a synthetic snk-like file
    svg = ('<svg><style>.s{animation:none linear 1000ms infinite}'
           '@keyframes c0{40.00%{fill:red}40.02%,100%{fill:none}}'
           '@keyframes s0{0%,99.3%{transform:translate(0px,-16px)}0.7%{transform:translate(0px,0px)}50%{transform:translate(160px,0px)}}'
           '@keyframes s1{0%,99.3%{transform:translate(16px,-16px)}0.7%{transform:translate(0px,-16px)}1.4%{transform:translate(0px,0px)}}'
           '@keyframes s3{0%,99.3%{transform:translate(48px,-16px)}2.8%{transform:translate(0px,0px)}52.1%{transform:translate(160px,0px)}}'
           '</style><rect class="s s0"/></svg>')
    out = grow(svg)
    assert "@keyframes s4{" in out and ".g4{" in out and out.index('class="g4"') < out.index('class="s s0"')
    assert "40.00%,99.19%{opacity:1}" in out, out
    assert grow(out) == out  # idempotent
    print("demo ok")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    for f in sys.argv[1:]:
        s = open(f, encoding="utf-8").read()
        open(f, "w", encoding="utf-8", newline="").write(grow(s))
        print("grown", f)
